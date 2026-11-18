import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from google import genai

logger = logging.getLogger(__name__)
load_dotenv()

# --- Configurazione Client ---
# FreeLLMAPI:
freellmapi_client = None
if os.getenv("FREELLMAPI_BASE_URL"):
    freellmapi_client = AsyncOpenAI(
        base_url=os.getenv("FREELLMAPI_BASE_URL"),
        api_key=os.getenv("FREELLMAPI_API_KEY", "dummy-key"),
        timeout=5.0,
        max_retries=0,  # Zero retry per non perdere ulteriore tempo
    )

# Gemini
gemini_client = None
if os.getenv("GEMINI_API_KEY"):
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
else:
    logger.warning("GEMINI_API_KEY non trovata")

MODELLO_FREELLMAPI = os.getenv("FREELLMAPI_MODEL", "auto:fastest")
MODELLO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
TIMEOUT_LLM = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
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
                timeout=TIMEOUT_LLM,
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


async def chiama_llm_json(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict:
    """Esegue il 1st try con FreeLLMAPI e il 2nd try con Gemini (gemini-3.5-flash-lite)."""
    sequenza = [_chiama_freellmapi, _chiama_gemini]

    ultimo_errore = None
    for provider in sequenza:
        try:
            logger.info("Tentativo con: %s", provider.__name__)
            return await provider(system_prompt, user_prompt, temperature)
        except LLMError as e:
            logger.warning("Fallback attivato: %s", e)
            ultimo_errore = e

    raise LLMError(f"Tutti i provider hanno fallito. Errore: {ultimo_errore}") from ultimo_errore
