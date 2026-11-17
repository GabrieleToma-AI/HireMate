import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError
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
        max_retries=0, # Zero retry per non perdere ulteriore tempo
    )

# Gemini
gemini_client = None
if os.getenv("GEMINI_API_KEY"):
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
else:
    logger.warning("GEMINI_API_KEY non trovata")

MODELLO_FREELLMAPI = os.getenv("FREELLMAPI_MODEL", "auto:fastest")
MODELLO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


class LLMError(Exception):
    """Errore nella chiamata all'LLM."""
    pass


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
        return json.loads(risposta.choices[0].message.content)
    except Exception as e:
        raise LLMError(f"FreeLLMAPI: {str(e)}")


async def _chiama_gemini(system_prompt: str, user_prompt: str, temperature: float) -> dict:
    if not gemini_client:
        raise LLMError("Gemini non configurato")
    try:
        risposta = await gemini_client.aio.models.generate_content(
            model=MODELLO_GEMINI,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=temperature
            )
        )
        return json.loads(risposta.text)
    except Exception as e:
        raise LLMError(f"Gemini: {str(e)}")


async def chiama_llm_json(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict:
    """Esegue il 1st try con FreeLLMAPI e il 2nd try con Gemini."""
    sequenza = [_chiama_freellmapi, _chiama_gemini]

    ultimo_errore = None
    for provider in sequenza:
        try:
            logger.info(f"Tentativo con: {provider.__name__}")
            return await provider(system_prompt, user_prompt, temperature)
        except LLMError as e:
            logger.warning(f"Fallback attivato: {e}")
            ultimo_errore = e

    raise LLMError(f"Tutti i provider hanno fallito. Errore: {ultimo_errore}")