"""Test offline del client DB (Collega 1, Stream 1): FakeDbClient in memoria.

Stile delle suite esistenti: `esegui`, output TOTALE/PASSATI/FALLITI, CASI_ATTESI.
Nessuna chiave, nessuna rete: FakeDbClient è l'appoggio di test.
"""

import sys

from database.fake_client import FakeDbClient

sys.stdout.reconfigure(encoding="utf-8")

CASI_ATTESI = 9

client = FakeDbClient()
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


def _utente_test() -> dict:
    return {
        "nickname": "stu_db",
        "pin_hash": "hash-finto",
        "corso": "Cyber Security Specialist",
        "ansia_principale": "Restare senza parole",
        "stile_gestione_problemi": "Mi blocco e mi faccio prendere dal panico",
        "timore_critico": "Non ho abbastanza esperienza tecnica per il ruolo",
        "cv_json": None,
    }


def test_find_vuoto():
    assert client.find_user_by_nickname("nessuno") is None


def test_create_e_find():
    utente = client.create_user(_utente_test())
    trovato = client.find_user_by_nickname("stu_db")
    assert trovato["nickname"] == "stu_db"
    assert trovato["id"] == utente["id"]


def test_due_utenti_distinti():
    altro = _utente_test()
    altro["nickname"] = "stu_db2"
    client.create_user(altro)
    assert client.find_user_by_nickname("stu_db")["id"] != client.find_user_by_nickname("stu_db2")["id"]


def test_cv_salvato_e_letto():
    cv = {"competenze": ["Python"], "progetti": ["Rete aziendale"]}
    user_id = client.find_user_by_nickname("stu_db")["id"]
    client.save_user_cv(user_id, cv)
    assert client.get_user_cv(user_id) == cv


def test_sessioni_e_turni():
    utente = client.find_user_by_nickname("stu_db")
    sessione = client.create_session({"user_id": utente["id"], "corso": CORSO_TEST})
    client.save_turn({"session_id": sessione["id"], "domanda": "D?", "trascrizione": "R1"})
    client.save_turn({"session_id": sessione["id"], "domanda": "D2?", "trascrizione": "R2"})
    turni = client.get_turns(sessione["id"])
    assert len(turni) == 2
    assert turni[0]["trascrizione"] == "R1"


CORSO_TEST = "Cyber Security Specialist"


def test_get_turni_vuoto():
    assert client.get_turns("id-non-esistente") == []


def test_turni_legati_alla_sessione():
    utente = client.find_user_by_nickname("stu_db")
    prima = client.create_session({"user_id": utente["id"], "corso": CORSO_TEST})
    client.save_turn({"session_id": prima["id"], "domanda": "D1", "trascrizione": "R1"})
    altra = client.create_session({"user_id": utente["id"], "corso": CORSO_TEST})
    assert all(t["session_id"] != altra["id"] for t in client.get_turns(altra["id"]))
    assert len(client.get_turns(prima["id"])) == 1


def test_update_user_fear():
    utente = client.find_user_by_nickname("stu_db")
    aggiornato = client.update_user_fear(utente["id"], "Fare una figuraccia con il recruiter")
    assert aggiornato["ansia_principale"] == "Fare una figuraccia con il recruiter"


def test_save_fear_history():
    utente = client.find_user_by_nickname("stu_db")
    prima = len(client._paure)
    client.save_fear_history({
        "user_id": utente["id"],
        "vecchia_paura": "A",
        "nuova_paura": "B",
    })
    assert len(client._paure) == prima + 1


def main() -> int:
    print("🧪 TEST DB (FakeDbClient in memoria) — offline, senza chiavi\n")
    print("=" * 60)

    esegui("find vuoto -> None", test_find_vuoto)
    esegui("create_user + find", test_create_e_find)
    esegui("due utenti distinti", test_due_utenti_distinti)
    esegui("cv_json salvato e letto", test_cv_salvato_e_letto)
    esegui("sessioni e turni (2 turni, ordine)", test_sessioni_e_turni)
    esegui("get_turns vuoto -> []", test_get_turni_vuoto)
    esegui("turni legati alla sessione", test_turni_legati_alla_sessione)
    esegui("update_user_fear", test_update_user_fear)
    esegui("save_fear_history appende", test_save_fear_history)

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
