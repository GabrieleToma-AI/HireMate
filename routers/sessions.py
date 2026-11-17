from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agenti.interviewer import genera_domanda
from agenti.llm import LLMError

# Creiamo il router per le sessioni
router = APIRouter()

# Definiamo lo schema dei dati che ci manda il frontend (Pydantic) durante la registrazione
class SessionStartRequest(BaseModel):
    corso: str
    paura_colloquio: str
    reazione_problema: str
    paura_fallimento: str
    cv_json: dict | None = None

# Definiamo lo schema della risposta che diamo al frontend
class SessionStartResponse(BaseModel):
    turnId: str
    questionText: str
    audioUrl: str | None = None  # Per ora è None, poi ci metteremo Azure TTS
    visemes: list = []
    gesture: str = "explain"

@router.post("/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """
    Avvia una nuova sessione e genera la prima domanda.
    """
    try:
        # Chiamiamo il tuo Interviewer Agent!
        domanda = await genera_domanda(
            corso=request.corso,
            paura_colloquio=request.paura_colloquio,
            reazione_problema=request.reazione_problema,
            paura_fallimento=request.paura_fallimento,
            cv_json=request.cv_json
        )
        
        # Per ora restituiamo dati finti per audio e visemi (il tuo Collega 2 li implementerà)
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