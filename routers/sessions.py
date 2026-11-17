from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Importiamo gli agenti e le eccezioni
from agenti.interviewer import genera_domanda
from agenti.reporter import genera_report_finale
from agenti.llm import LLMError

# 1. INIZIALIZZAZIONE DEL ROUTER
# Questa riga DEVE stare prima di usare @router.post
router = APIRouter()

# ==========================================
# MODELLI PYDANTIC (I "Contratti" dei dati)
# ==========================================

class SessionStartRequest(BaseModel):
    corso: str
    profilo_soft_skill: dict
    cv_json: dict | None = None

class SessionStartResponse(BaseModel):
    turnId: str
    questionText: str
    audioUrl: str | None = None
    visemes: list = []
    gesture: str = "explain"

class EndSessionRequest(BaseModel):
    corso: str
    profilo_soft_skill: dict
    valutazioni: list[dict]
    report_precedente: dict | None = None

class EndSessionResponse(BaseModel):
    report: dict

# ==========================================
# ENDPOINT API
# ==========================================

@router.post("/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """
    Avvia una nuova sessione e genera la prima domanda.
    """
    try:
        domanda = await genera_domanda(
            corso=request.corso,
            profilo_soft_skill=request.profilo_soft_skill,
            cv_json=request.cv_json
        )
        
        return SessionStartResponse(
            turnId="mock-turn-001",
            questionText=domanda,
            audioUrl=None,
            visemes=[],
            gesture="explain"
        )
        
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.post("/end", response_model=EndSessionResponse)
async def end_session(request: EndSessionRequest):
    """
    Chiude la sessione e restituisce il report finale gamificato.
    """
    try:
        report = await genera_report_finale(
            corso=request.corso,
            profilo_soft_skill=request.profilo_soft_skill,
            valutazioni=request.valutazioni,
            report_precedente=request.report_precedente
        )
        return EndSessionResponse(report=report)
        
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")