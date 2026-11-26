"""Test offline di auth (Collega 1, Stream 1): register/login/update-fear.

TestClient su `app` con FakeDbClient (da router.users), senza chiavi e senza rete.
"""

import sys

from fastapi.testclient import TestClient

import routers.users as users_module
from database.fake_client import FakeDbClient
from main import app
from profilo import PAURE_DISPONIBILI

sys.stdout.reconfigure(encoding="utf-8")

CASI_ATTESI = 11

PROFILO = {
    "ansia_principale": "Restare senza parole",
    "stile_gestione_problemi": "Mi blocco e mi faccio prendere dal panico",
    "timore_critico": "Non ho abbastanza esperienza tecnica per il ruolo",
}
NICK = "stu_auth"
PIN = "1234"
CORSO = "Cyber Security Specialist"

users_module._DB_CLIENT = FakeDbClient()
CLIENT = TestClient(app)
esiti = {"passati": 0, "falliti": 0}


def esegui(nome: str, funzione) -> None:
    try:
        funzione()
    except Exception as errore:  # noqa: BLE001
        esiti["falliti"] += 1
        print(f"  ❌ {nome} -> {type(errore).__name__}: {errore}")
    else:
        esiti["passati"] += 1
        print(f"  ✅ {nome}")


def _payload_register() -> dict:
    return {"nickname": NICK, "pin": PIN, "corso": CORSO, "profilo_soft_skill": PROFILO}


def _payload_login() -> dict:
    return {"nickname": NICK, "pin": PIN}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_register_ok():
    r = CLIENT.post("/api/users/register", json=_payload_register())
    assert r.status_code == 200
    assert r.json()["user_id"]
    assert r.json()["token"]


def test_register_nickname_duplicato():
    CLIENT.post("/api/users/register", json=_payload_register())
    r = CLIENT.post("/api/users/register", json=_payload_register())
    assert r.status_code == 422


def test_register_pin_non_cifre():
    r = CLIENT.post("/api/users/register", json={**_payload_register(), "pin": "abcd"})
    assert r.status_code == 422


def test_login_ok():
    r = CLIENT.post("/api/users/login", json=_payload_login())
    assert r.status_code == 200
    assert r.json()["token"]


def test_login_sbagliato():
    r = CLIENT.post("/api/users/login", json={**_payload_login(), "pin": "0000"})
    assert r.status_code == 401


def test_login_blocco_backoff():
    users_module._tentativi.clear()
    for _ in range(3):
        r = CLIENT.post("/api/users/login", json={**_payload_login(), "pin": "0000"})
        assert r.status_code == 401
    assert users_module._blocco_attivo(NICK) > 0
    users_module._tentativi.clear()


def test_update_fear_senza_auth():
    r = CLIENT.patch("/api/users/update-fear", json={"nuova_paura": PAURE_DISPONIBILI[1]})
    assert r.status_code == 401


def test_update_fear_ok():
    token = CLIENT.post("/api/users/login", json=_payload_login()).json()["token"]
    r = CLIENT.patch(
        "/api/users/update-fear",
        json={"nuova_paura": PAURE_DISPONIBILI[1]},
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["ansia_principale"] == PAURE_DISPONIBILI[1]
    righe = users_module._DB_CLIENT._paure
    assert any(row["nuova_paura"] == PAURE_DISPONIBILI[1] for row in righe)


def test_update_fear_paura_invalida():
    token = CLIENT.post("/api/users/login", json=_payload_login()).json()["token"]
    r = CLIENT.patch(
        "/api/users/update-fear",
        json={"nuova_paura": "Paura inventata"},
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_me_con_token():
    token = CLIENT.post("/api/users/login", json=_payload_login()).json()["token"]
    r = CLIENT.get("/api/users/me", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["nickname"] == NICK


def test_token_falsificato():
    r = CLIENT.get("/api/users/me", headers=_auth("nome.finto.ndale"))
    assert r.status_code == 401


def main() -> int:
    print("🔐 TEST AUTH (FakeDbClient) — offline, senza chiavi\n")
    print("=" * 60)

    esegui("register ok (user_id + token)", test_register_ok)
    esegui("register nickname duplicato -> 422", test_register_nickname_duplicato)
    esegui("register PIN non cifre -> 422", test_register_pin_non_cifre)
    esegui("login ok", test_login_ok)
    esegui("login PIN sbagliato -> 401", test_login_sbagliato)
    esegui("login blocco backoff (3 tentativi)", test_login_blocco_backoff)
    esegui("update-fear senza auth -> 401", test_update_fear_senza_auth)
    esegui("update-fear ok (+ fears_history)", test_update_fear_ok)
    esegui("update-fear paura invalida -> 422", test_update_fear_paura_invalida)
    esegui("GET /me con token", test_me_con_token)
    esegui("token falso -> 401", test_token_falsificato)

    totale = esiti["passati"] + esiti["falliti"]
    print("\n" + "=" * 60)
    print(f"TOTALE: {totale}   PASSATI: {esiti['passati']}   FALLITI: {esiti['falliti']}")
    print("=" * 60)
    if totale != CASI_ATTESI:
        print(f"\n❌ Casi eseguiti: {totale}, attesi: {CASI_ATTESI}.")
        return 1
    if esiti["falliti"]:
        print("\n❌ ALCUNI TEST SONO FALLITI")
        return 1
    print("\n🎉 TUTTI I TEST SONO PASSATI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
