import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

# Importiamo gli agenti e le eccezioni
from agenti.interviewer import genera_domanda
from agenti.reporter import genera_report_finale
from agenti.llm import LLMError
from corsi import CorsoNonValidoError, get_dettagli_corso
from profilo import PAURE_DISPONIBILI, STILI_GESTIONE_PROBLEMI, TIMORI_CRITICI

logger = logging.getLogger(__name__)

# 1. INIZIALIZZAZIONE DEL ROUTER
# Questa riga DEVE stare prima di usare @router.post
router = APIRouter()

# Numero indicativo di domande: il colloquio si chiude quando il Reporter
# ha abbastanza informazioni, non con un rifiuto brusco a tempo.
DOMANDE_PER_COLLOQUIO = 6

# ==========================================
# MODELLI PYDANTIC (I "Contratti" dei dati)
# ==========================================

class ProfiloSoftSkill(BaseModel):
    ansia_principale: str
    stile_gestione_problemi: str
    timore_critico: str

    @field_validator("ansia_principale")
    @classmethod
    def ansia_valida(cls, valore: str) -> str:
        if valore not in PAURE_DISPONIBILI:
            raise ValueError(f"Ansia non valida: '{valore}'")
        return valore

    @field_validator("stile_gestione_problemi")
    @classmethod
    def stile_valido(cls, valore: str) -> str:
        if valore not in STILI_GESTIONE_PROBLEMI:
            raise ValueError(f"Stile non valido: '{valore}'")
        return valore

    @field_validator("timore_critico")
    @classmethod
    def timore_valido(cls, valore: str) -> str:
        if valore not in TIMORI_CRITICI:
            raise ValueError(f"Timore non valido: '{valore}'")
        return valore

class Valutazione(BaseModel):
    chiarezza: float = Field(ge=0, le=10)
    struttura_star: float = Field(ge=0, le=10)
    esempi_concreti: float = Field(ge=0, le=10)

class ValutazioneCompleta(Valutazione):
    suggerimento: str = ""
    better_answer: str = ""

class SessionStartRequest(BaseModel):
    corso: str
    profilo_soft_skill: ProfiloSoftSkill
    cv_json: dict | None = None

    @field_validator("corso")
    @classmethod
    def corso_valido(cls, valore: str) -> str:
        # CorsoNonValidoError e' un ValueError: Pydantic risponde 422
        get_dettagli_corso(valore)
        return valore

class SessionStartResponse(BaseModel):
    turnId: str
    questionText: str
    audioUrl: str | None = None
    visemes: list = Field(default_factory=list)
    gesture: str = "explain"

class EndSessionRequest(BaseModel):
    corso: str
    profilo_soft_skill: ProfiloSoftSkill
    valutazioni: list[Valutazione] = Field(min_length=1)
    # Temporaneo: quando Supabase sara' pronto, il report precedente arrivera' dal DB.
    report_precedente: dict | None = None

    @field_validator("corso")
    @classmethod
    def corso_valido(cls, valore: str) -> str:
        get_dettagli_corso(valore)
        return valore

class EndSessionResponse(BaseModel):
    report: dict

# Contratto per Collega 2: l'endpoint POST /api/session/turn usera' questi modelli.
class Turno(BaseModel):
    domanda: str
    trascrizione: str

class TurnRequest(BaseModel):
    corso: str
    profilo_soft_skill: ProfiloSoftSkill
    cv_json: dict | None = None
    domanda: str
    trascrizione: str
    cronologia: list[Turno] = Field(default_factory=list)
    # Collega 2: passare [t.model_dump() for t in request.cronologia] a genera_domanda.

    @field_validator("corso")
    @classmethod
    def corso_valido(cls, valore: str) -> str:
        get_dettagli_corso(valore)
        return valore

class TurnResponse(BaseModel):
    turnId: str
    valutazione: ValutazioneCompleta
    prossimaDomanda: str | None = None
    colloquio_terminato: bool = False
    audioUrl: str | None = None
    visemes: list = Field(default_factory=list)
    gesture: str = "explain"

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
            profilo_soft_skill=request.profilo_soft_skill.model_dump(),
            cv_json=request.cv_json
        )

        return SessionStartResponse(
            turnId=f"turn-{uuid4().hex}",
            questionText=domanda,
            audioUrl=None,
            visemes=[],
            gesture="explain"
        )

    except CorsoNonValidoError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LLMError as e:
        logger.warning("LLM non disponibile su /start: %s", e)
        raise HTTPException(status_code=503, detail="Servizio LLM non disponibile, riprova.") from e
    except Exception as e:
        logger.exception("Errore interno su /start")
        raise HTTPException(status_code=500, detail="Errore interno del server.") from e


@router.post("/end", response_model=EndSessionResponse)
async def end_session(request: EndSessionRequest):
    """
    Chiude la sessione e restituisce il report finale gamificato.
    """
    try:
        report = await genera_report_finale(
            corso=request.corso,
            profilo_soft_skill=request.profilo_soft_skill.model_dump(),
            valutazioni=[v.model_dump() for v in request.valutazioni],
            report_precedente=request.report_precedente
        )
        return EndSessionResponse(report=report)

    except CorsoNonValidoError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LLMError as e:
        logger.warning("LLM non disponibile su /end: %s", e)
        raise HTTPException(status_code=503, detail="Servizio LLM non disponibile, riprova.") from e
    except Exception as e:
        logger.exception("Errore interno su /end")
        raise HTTPException(status_code=500, detail="Errore interno del server.") from e
