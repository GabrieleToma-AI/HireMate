"""Test offline dei limiti di input (hardening): nessuna chiamata LLM, nessuna quota.

Verifica che i modelli di routers/sessions.py rifiutino i payload abnormi con 422
e che i valori esattamente al limite passino ancora.
"""

import sys

from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app
from routers.sessions import (
    MAX_CV_JSON,
    MAX_DOMANDA,
    MAX_TRASCRIZIONE,
    SessionStartRequest,
    Turno,
    TurnRequest,
)

sys.stdout.reconfigure(encoding="utf-8")

CORSO = "Cyber Security Specialist"
PROFILO = {
    "ansia_principale": "Restare senza parole",
    "stile_gestione_problemi": "Mi blocco e mi faccio prendere dal panico",
    "timore_critico": "Non ho abbastanza esperienza tecnica per il ruolo",
}

CLIENT = TestClient(app)
esiti = {"passati": 0, "falliti": 0}


def esegui(nome: str, funzione) -> None:
    try:
        funzione()
    except Exception as errore:  # noqa: BLE001 - il test riporta qualsiasi guasto
        esiti["falliti"] += 1
        print(f"  ❌ {nome} -> {type(errore).__name__}: {errore}")
    else:
        esiti["passati"] += 1
        print(f"  ✅ {nome}")


def atteso_errore(funzione) -> None:
    """Il caso passa solo se Pydantic rifiuta l'input."""
    try:
        funzione()
    except ValidationError:
        return
    raise AssertionError("input accettato: il limite non sta funzionando")


def turn_request(**campi) -> TurnRequest:
    base = {
        "corso": CORSO,
        "profilo_soft_skill": PROFILO,
        "domanda": "Domanda valida?",
        "trascrizione": "Risposta valida.",
    }
    base.update(campi)
    return TurnRequest(**base)


def test_limiti_dichiarati():
    assert (MAX_TRASCRIZIONE, MAX_DOMANDA, MAX_CV_JSON) == (2000, 500, 4096)


def test_turn_request_al_limite():
    richiesta = turn_request(
        domanda="d" * MAX_DOMANDA,
        trascrizione="t" * MAX_TRASCRIZIONE,
    )
    assert len(richiesta.domanda) == MAX_DOMANDA
    assert len(richiesta.trascrizione) == MAX_TRASCRIZIONE


def test_domanda_troppo_lunga():
    atteso_errore(lambda: turn_request(domanda="d" * (MAX_DOMANDA + 1)))


def test_trascrizione_troppo_lunga():
    atteso_errore(lambda: turn_request(trascrizione="t" * (MAX_TRASCRIZIONE + 1)))


def test_cronologia_troppo_lunga():
    # La cronologia sarebbe un modo per aggirare il limite: vale anche qui.
    atteso_errore(
        lambda: turn_request(
            cronologia=[
                {"domanda": "Domanda?", "trascrizione": "t" * (MAX_TRASCRIZIONE + 1)}
            ]
        )
    )


def test_turno_valido():
    turno = Turno(domanda="Domanda?", trascrizione="Risposta.")
    assert turno.domanda == "Domanda?"


def test_cv_json_none():
    richiesta = SessionStartRequest(
        corso=CORSO, profilo_soft_skill=PROFILO, cv_json=None
    )
    assert richiesta.cv_json is None


def test_cv_json_piccolo():
    cv = {"competenze": ["Python"], "progetti": ["Rete aziendale"]}
    richiesta = SessionStartRequest(
        corso=CORSO, profilo_soft_skill=PROFILO, cv_json=cv
    )
    assert richiesta.cv_json == cv


def test_cv_json_troppo_grande():
    cv = {"competenze": ["x" * (MAX_CV_JSON + 100)]}
    atteso_errore(
        lambda: SessionStartRequest(
            corso=CORSO, profilo_soft_skill=PROFILO, cv_json=cv
        )
    )


def test_http_start_cv_enorme():
    # Il 422 lo produce Pydantic prima dell'endpoint: nessuna chiamata all'LLM.
    risposta = CLIENT.post(
        "/api/session/start",
        json={
            "corso": CORSO,
            "profilo_soft_skill": PROFILO,
            "cv_json": {"competenze": ["x" * (MAX_CV_JSON + 100)]},
        },
    )
    assert risposta.status_code == 422, risposta.status_code


def main() -> int:
    print("🛡️  HARDENING DEGLI INPUT — test offline (nessuna quota)\n")
    print("=" * 60)

    esegui("Limiti dichiarati: 2000 / 500 / 4096", test_limiti_dichiarati)
    esegui("TurnRequest accetta i valori al limite", test_turn_request_al_limite)
    esegui(f"Domanda di {MAX_DOMANDA + 1} caratteri -> 422", test_domanda_troppo_lunga)
    esegui(
        f"Trascrizione di {MAX_TRASCRIZIONE + 1} caratteri -> 422",
        test_trascrizione_troppo_lunga,
    )
    esegui("Cronologia con trascrizione lunga -> 422", test_cronologia_troppo_lunga)
    esegui("Turno valido", test_turno_valido)
    esegui("cv_json assente accettato", test_cv_json_none)
    esegui("cv_json piccolo accettato", test_cv_json_piccolo)
    esegui(f"cv_json oltre {MAX_CV_JSON} byte -> 422", test_cv_json_troppo_grande)
    esegui("POST /start con cv_json enorme -> 422", test_http_start_cv_enorme)

    totale = esiti["passati"] + esiti["falliti"]
    print("\n" + "=" * 60)
    print(
        f"TOTALE: {totale}   PASSATI: {esiti['passati']}   "
        f"FALLITI: {esiti['falliti']}"
    )
    print("=" * 60)
    if esiti["falliti"]:
        print("\n❌ ALCUNI TEST SONO FALLITI")
        return 1
    print("\n🎉 TUTTI I TEST SONO PASSATI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
