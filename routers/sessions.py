from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agenti.interviewer import genera_domanda
from agenti.llm import LLMError

router = APIRouter()

# 1. Il Modello Pydantic aggiornato
class SessionStartRequest(BaseModel):
    corso: str
    profilo_soft_skill: dict  # <-- Ora accetta il dizionario!
    cv_json: dict | None = None

class SessionStartResponse(BaseModel):
    turnId: str
    questionText: str
    audioUrl: str | None = None
    visemes: list = []
    gesture: str = "explain"

@router.post("/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    try:
        # 2. Passiamo il dizionario all'agente
        domanda = await genera_domanda(
            corso=request.corso,
            profilo_soft_skill=request.profilo_soft_skill, # <-- Passiamo il dict
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