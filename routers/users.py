"""Router auth e profilo — "sportello dell'utente" (Collega 1, Stream 1).

Endpoint:
- POST /api/users/register: nickname, PIN, profilo, corso -> {user_id, token}
- POST /api/users/login: nickname + PIN -> {user_id, token}
- PATCH /api/users/update-fear: Bearer + nuova_paura -> profilo aggiornato
- GET /api/users/me: utente attuale (dentro l'auth)
"""

import logging
import os
import time
from datetime import datetime, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from database.client import DbClient
from database.supabase_client import SupabaseClient
from profilo import PAURE_DISPONIBILI
from routers.sessions import ProfiloSoftSkill, get_dettagli_corso

logger = logging.getLogger(__name__)

router = APIRouter()

# PIN: 4 cifre, come da TODO/README.
PIN_LUNGHEZZA = 4

# Rate limit su login falliti: 3 errori → blocco esponenziale (60s, 120s, ...).
TENTATIVI_BLOCCO = 3
DURATA_BLOCCO_MAX = 3600.0  # Secondi; spesso inutile ma sicurezza per bug

# Stato rate limit in memoria: nickname -> (errori consecutivi, blocked_until).
_tentativi: dict[str, tuple[int, float]] = {}

# Segreto JWT: in produzione vale l'ambiente; il default è solo dev/localhost.
JWT_SECRET = os.getenv("JWT_SECRET", "hiremate-dev-segreto-non-in-codice")
JWT_ALGORITMO = "HS256"
JWT_TTL_SECONDI = int(os.getenv("JWT_TTL_SECONDI", "86400"))  # 24h, da TODO

_DB_CLIENT: DbClient | None = None


def get_db_client() -> DbClient:
    """Ritorna il client DB usato dai router; i test lo sostituiscono con FakeDbClient."""
    global _DB_CLIENT
    if _DB_CLIENT is None:
        _DB_CLIENT = SupabaseClient()
    return _DB_CLIENT


def _hash_pin(pin: str) -> str:
    """Hash del PIN (bcrypt): mai in chiaro, mai nei log."""
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verifica_pin(pin: str, pin_hash: str) -> bool:
    return bcrypt.checkpw(pin.encode("utf-8"), pin_hash.encode("utf-8"))


def _token(user_id: str, nickname: str) -> str:
    payload = {
        "sub": user_id,
        "nick": nickname,
        "exp": int(time.time()) + JWT_TTL_SECONDI,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITMO)


def _utente_da_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITMO])
    except jwt.InvalidTokenError:
        return None


def _utente_auth(authorization: str | None) -> dict:
    """Decodifica il Bearer; errore generico se assente o invalido."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Autenticazione richiesta.")
    payload = _utente_da_token(authorization[len("Bearer "):])
    if payload is None:
        raise HTTPException(status_code=401, detail="Autenticazione richiesta.")
    return payload


# --- Rate limit su login falliti (backoff esponenziale) ---

def _blocco_attivo(nickname: str) -> float:
    entry = _tentativi.get(nickname)
    if not entry:
        return 0.0
    _errori, blocked_until = entry
    return max(0.0, blocked_until - time.time())


def _registra_tentativo_fallito(nickname: str) -> float:
    errori, _blocked_until = _tentativi.get(nickname, (0, 0.0))
    errori += 1
    blocco = 0.0
    if errori >= TENTATIVI_BLOCCO:
        # Ogni tentativo oltre la soglia allunga il blocco: 60s, 120s, ...
        blocco = min(60.0 * (2 ** (errori - TENTATIVI_BLOCCO)), DURATA_BLOCCO_MAX)
    _tentativi[nickname] = (errori, time.time() + blocco)
    return blocco


# --- Modelli ---

class RegisterRequest(BaseModel):
    nickname: str = Field(min_length=3)
    pin: str = Field(min_length=PIN_LUNGHEZZA, max_length=PIN_LUNGHEZZA)
    corso: str
    profilo_soft_skill: ProfiloSoftSkill

    @field_validator("pin")
    @classmethod
    def pin_deve_essere_cifre(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Il PIN deve contenere solo cifre.")
        return v

    @field_validator("corso")
    @classmethod
    def corso_valido(cls, v: str) -> str:
        get_dettagli_corso(v)
        return v


class LoginRequest(BaseModel):
    nickname: str = Field(min_length=3)
    pin: str = Field(min_length=PIN_LUNGHEZZA, max_length=PIN_LUNGHEZZA)


class UpdateFearRequest(BaseModel):
    nuova_paura: str


# --- Endpoint ---

@router.post("/register")
async def register(req: RegisterRequest) -> dict:
    db = get_db_client()
    if db.find_user_by_nickname(req.nickname):
        # Opzione scelta in plan: 422 (come Nickname esistente, al Uniforme con altri 422).
        raise HTTPException(status_code=422, detail="Nickname già in uso: scegline un altro.")
    utente = db.create_user({
        "nickname": req.nickname,
        "pin_hash": _hash_pin(req.pin),
        "corso": req.corso,
        "ansia_principale": req.profilo_soft_skill.ansia_principale,
        "stile_gestione_problemi": req.profilo_soft_skill.stile_gestione_problemi,
        "timore_critico": req.profilo_soft_skill.timore_critico,
        "cv_json": None,
    })
    return {"user_id": utente["id"], "token": _token(utente["id"], utente["nickname"])}


@router.post("/login")
async def login(req: LoginRequest) -> dict:
    # Messaggio generico: non rivelare se il nickname esiste o se il PIN è sbagliato.
    if _blocco_attivo(req.nickname) > 0:
        raise HTTPException(status_code=401, detail="Credenziali non valide.")
    db = get_db_client()
    utente = db.find_user_by_nickname(req.nickname)
    if not utente or not _verifica_pin(req.pin, utente["pin_hash"]):
        _registra_tentativo_fallito(req.nickname)
        raise HTTPException(status_code=401, detail="Credenziali non valide.")
    _tentativi.pop(req.nickname, None)
    return {"user_id": utente["id"], "token": _token(utente["id"], utente["nickname"])}


@router.patch("/update-fear")
async def update_fear(
    request: UpdateFearRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    utente = _utente_auth(authorization)
    if request.nuova_paura not in PAURE_DISPONIBILI:
        raise HTTPException(status_code=422, detail="Paura non valida: non è nella lista ufficiale.")
    db = get_db_client()
    vecchia = (db.find_user_by_nickname(utente["nick"]) or {}).get("ansia_principale", "")
    aggiornato = db.update_user_fear(utente["sub"], request.nuova_paura)
    db.save_fear_history({
        "user_id": utente["sub"],
        "vecchia_paura": vecchia,
        "nuova_paura": request.nuova_paura,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"user_id": aggiornato["id"], "ansia_principale": aggiornato["ansia_principale"]}


@router.get("/me")
async def me(authorization: str | None = Header(default=None)) -> dict:
    utente = _utente_auth(authorization)
    db = get_db_client()
    record = db.find_user_by_nickname(utente["nick"])
    if record is None:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    return {
        "user_id": record["id"],
        "nickname": record["nickname"],
        "corso": record["corso"],
        "ansia_principale": record["ansia_principale"],
        "stile_gestione_problemi": record["stile_gestione_problemi"],
        "timore_critico": record["timore_critico"],
        "cv_json": db.get_user_cv(record["id"]),
    }
