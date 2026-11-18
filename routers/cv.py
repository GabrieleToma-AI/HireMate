import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from agenti.cv_parser import estrai_cv_json
from agenti.llm import LLMError

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_BYTES = 5 * 1024 * 1024  # 5 MB
TIPI_ACCETTATI = {"application/pdf", "application/x-pdf", "application/octet-stream"}


@router.post("/parse")
async def parse_cv(file: UploadFile = File(...)):
    """Riceve un PDF e restituisce il CV in JSON (competenze + progetti)."""
    if file.content_type not in TIPI_ACCETTATI:
        raise HTTPException(status_code=415, detail="Carica un file PDF.")

    contenuto = await file.read()
    if not contenuto:
        raise HTTPException(status_code=400, detail="Il file è vuoto.")
    if len(contenuto) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="PDF troppo grande (max 5 MB).")

    try:
        cv_json = await estrai_cv_json(contenuto)
        return {"cv_json": cv_json}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LLMError as e:
        logger.warning("LLM non disponibile su /cv/parse: %s", e)
        raise HTTPException(status_code=503, detail="Servizio LLM non disponibile, riprova.") from e
    except Exception as e:
        logger.exception("Errore interno su /cv/parse")
        raise HTTPException(status_code=500, detail="Errore interno del server.") from e
