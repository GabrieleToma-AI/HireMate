"""Finto client DB in memoria: FakeDbClient (database/fake_client.py).

Per i test offline (test_db.py, test_auth.py): ha gli stessi metodi di
DbClient, quindi i router e i test accettano lo fake al posto del client reale.
Appoggio di test: nessuna chiave, nessuna rete, dati volatile per l'esecuzione.
"""

from database.client import DbClient


class FakeDbClient(DbClient):
    def __init__(self):
        self._utenti: dict[str, dict] = {}
        self._utenti_da_nick: dict[str, str] = {}
        self._sessioni: dict[str, dict] = {}
        self._turni: list[dict] = []
        self._paure: list[dict] = []

    def find_user_by_nickname(self, nickname: str) -> dict | None:
        id_utente = self._utenti_da_nick.get(nickname)
        return dict(self._utenti[id_utente]) if id_utente else None

    def create_user(self, user: dict) -> dict:
        record = dict(user)
        if "id" not in record:
            import uuid
            record["id"] = uuid.uuid4().hex
        self._utenti[record["id"]] = record
        self._utenti_da_nick[record["nickname"]] = record["id"]
        return dict(record)

    def save_user_cv(self, user_id: str, cv_json: dict | None) -> None:
        self._utenti[user_id]["cv_json"] = cv_json

    def get_user_cv(self, user_id: str) -> dict | None:
        return self._utenti[user_id].get("cv_json")

    def create_session(self, session: dict) -> dict:
        import uuid
        record = dict(session)
        record.setdefault("id", uuid.uuid4().hex)
        self._sessioni[record["id"]] = record
        return dict(record)

    def save_turn(self, turno: dict) -> None:
        self._turni.append(dict(turno))

    def get_turns(self, session_id: str) -> list[dict]:
        return [dict(t) for t in self._turni if t.get("session_id") == session_id]

    def update_user_fear(self, user_id: str, nuova_paura: str, session_id: str | None = None) -> dict:
        utente = self._utenti[user_id]
        utente["ansia_principale"] = nuova_paura
        return dict(utente)

    def save_fear_history(self, riga: dict) -> None:
        self._paure.append(dict(riga))
