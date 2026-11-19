import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from google import genai

logger = logging.getLogger(__name__)
load_dotenv()

# --- Configurazione timeout ---
# I primi due provider devono rispondere in fretta: l'utente è in attesa.
# DeepSeek è a pagamento e fa da ultima risorsa, quindi può prendersi più tempo.
TIMEOUT_FREELLMAPI = float(os.getenv("FREELLMAPI_TIMEOUT_SECONDS", "3"))
TIMEOUT_GEMINI = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "6"))
TIMEOUT_DEEPSEEK = float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "30"))

# --- Configurazione Client ---
# FreeLLMAPI:
freellmapi_client = None
if os.getenv("FREELLMAPI_BASE_URL"):
    freellmapi_client = AsyncOpenAI(
        base_url=os.getenv("FREELLMAPI_BASE_URL"),
        api_key=os.getenv("FREELLMAPI_API_KEY", "dummy-key"),
        timeout=TIMEOUT_FREELLMAPI,
        max_retries=0,  # Zero retry per non perdere ulteriore tempo
    )

# Gemini
gemini_client = None
if os.getenv("GEMINI_API_KEY"):
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
else:
    logger.warning("GEMINI_API_KEY non trovata")

# DeepSeek (API compatibile OpenAI): ultima risorsa, servizio a pagamento.
deepseek_client = None
if os.getenv("DEEPSEEK_API_KEY"):
    deepseek_client = AsyncOpenAI(
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        timeout=TIMEOUT_DEEPSEEK,
        max_retries=0,  # se anche DeepSeek fallisce, l'errore arriva all'utente
    )
else:
    logger.warning("DEEPSEEK_API_KEY non trovata")

MODELLO_FREELLMAPI = os.getenv("FREELLMAPI_MODEL", "auto:fastest")
MODELLO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
MODELLO_DEEPSEEK = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
TENTATIVI_GEMINI = 3  # 1 tentativo + 2 retry
ATTESA_RETRY = float(os.getenv("LLM_RETRY_DELAY_SECONDS", "1.5"))


class LLMError(Exception):
    """Errore nella chiamata all'LLM."""
    pass


def _estrai_json(testo: str | None) -> dict:
    """Converte la risposta dell'LLM in dict, tollerando i code fence markdown."""
    testo = (testo or "").strip()

    # Rimuove eventuali ```json ... ```
    if testo.startswith("```"):
        testo = testo.strip("`")
        if testo.lower().startswith("json"):
            testo = testo[4:]
        testo = testo.strip()

    # Se il modello aggiunge testo prima/dopo il JSON, prende solo l'oggetto
    inizio = testo.find("{")
    fine = testo.rfind("}")
    if inizio != -1 and fine != -1:
        testo = testo[inizio:fine + 1]

    return json.loads(testo)


def _errore_temporaneo(errore: Exception) -> bool:
    """True per 503/429/quota/timeout: vale la pena riprovare."""
    if isinstance(errore, asyncio.TimeoutError):
        return True
    testo = str(errore).upper()
    return any(
        codice in testo
        for codice in (
            "503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
            "RATE LIMIT", "TIMEOUT", "TIMED OUT",
        )
    )


async def _chiama_freellmapi(system_prompt: str, user_prompt: str, temperature: float) -> dict:
    if not freellmapi_client:
        raise LLMError("FreeLLMAPI non configurato nel .env")
    try:
        risposta = await freellmapi_client.chat.completions.create(
            model=MODELLO_FREELLMAPI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return _estrai_json(risposta.choices[0].message.content)
    except Exception as e:
        raise LLMError(f"FreeLLMAPI: {str(e)}") from e


async def _chiama_gemini(system_prompt: str, user_prompt: str, temperature: float) -> dict:
    if not gemini_client:
        raise LLMError("Gemini non configurato")

    for tentativo in range(TENTATIVI_GEMINI):
        try:
            risposta = await asyncio.wait_for(
                gemini_client.aio.models.generate_content(
                    model=MODELLO_GEMINI,
                    contents=user_prompt,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=temperature
                    )
                ),
                timeout=TIMEOUT_GEMINI,
            )
            return _estrai_json(risposta.text)
        except Exception as e:
            if tentativo == TENTATIVI_GEMINI - 1 or not _errore_temporaneo(e):
                raise LLMError(f"Gemini: {str(e)}") from e
            logger.warning(
                "Gemini ha risposto con un errore temporaneo (%s); retry %d/%d tra %.1fs",
                e, tentativo + 1, TENTATIVI_GEMINI - 1, ATTESA_RETRY,
            )
            await asyncio.sleep(ATTESA_RETRY)

    raise LLMError("Gemini: nessun tentativo eseguito")


async def _chiama_deepseek(system_prompt: str, user_prompt: str, temperature: float) -> dict:
    """Ultima risorsa: servizio a pagamento, quindi senza retry (l'errore deve arrivare in fretta)."""
    if not deepseek_client:
        raise LLMError("DeepSeek non configurato nel .env")
    try:
        risposta = await deepseek_client.chat.completions.create(
            model=MODELLO_DEEPSEEK,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return _estrai_json(risposta.choices[0].message.content)
    except Exception as e:
        raise LLMError(f"DeepSeek: {str(e)}") from e


async def chiama_llm_json(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict:
    """Prova nell'ordine: FreeLLMAPI, Gemini Lite, DeepSeek.

    I primi due hanno timeout corti per non far attendere l'utente;
    DeepSeek, essendo a pagamento, è l'ultima risorsa ed è quella più affidabile.
    """
    sequenza = [_chiama_freellmapi, _chiama_gemini, _chiama_deepseek]

    errori: list[str] = []
    ultimo_errore: Exception | None = None
    for provider in sequenza:
        try:
            logger.info("Tentativo con: %s", provider.__name__)
            return await provider(system_prompt, user_prompt, temperature)
        except LLMError as e:
            logger.warning("Fallback attivato: %s", e)
            errori.append(str(e))
            ultimo_errore = e

    # Si riportano tutti gli errori, non solo l'ultimo: altrimenti un guasto
    # del primo provider resta invisibile nel messaggio finale.
    dettaglio = " | ".join(errori)
    raise LLMError(f"Tutti i provider hanno fallito. Errori: {dettaglio}") from ultimo_errore
