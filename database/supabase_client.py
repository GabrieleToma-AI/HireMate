"""Client DB reale su Supabase (Collega 1, Stream 1).

Implementa DbClient (database/client.py) con PostgREST:
`supabase.table("users").insert(...)`, `.select("*").eq("nickname", ...).limit(1)`,
`.update({...}).eq("id", ...)`.
Usa solo variabili d'ambiente SUPABASE_URL / SUPABASE_KEY (chiave a servizio, lato server).
"""

import os

from supabase import create_client

from database.client import DbClient


class SupabaseClient(DbClient):
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL e SUPABASE_KEY devono essere impostati in .env (solo lato server)."
            )
        self._client = create_client(url, key)

    @staticmethod
    def _prima(risultato) -> dict | None:
        return dict(risultato.data[0]) if risultato.data else None

    def find_user_by_nickname(self, nickname: str) -> dict | None:
        risultato = self._client.table("users").select("*").eq("nickname", nickname).limit(1).execute()
        return self._prima(risultato)

    def create_user(self, user: dict) -> dict:
        return self._prima(self._client.table("users").insert(user).execute())

    def save_user_cv(self, user_id: str, cv_json: dict | None) -> None:
        self._client.table("users").update({"cv_json": cv_json}).eq("id", user_id).execute()

    def get_user_cv(self, user_id: str) -> dict | None:
        risultato = self._client.table("users").select("cv_json").eq("id", user_id).limit(1).execute()
        riga = self._prima(risultato)
        return riga.get("cv_json") if riga else None

    def create_session(self, session: dict) -> dict:
        return self._prima(self._client.table("sessions").insert(session).execute())

    def save_turn(self, turno: dict) -> None:
        self._client.table("turns").insert(turno).execute()

    def get_turns(self, session_id: str) -> list[dict]:
        risultato = self._client.table("turns").select("*").eq("session_id", session_id).execute()
        return [dict(t) for t in risultato.data]

    def update_user_fear(self, user_id: str, nuova_paura: str, session_id: str | None = None) -> dict:
        risultato = self._client.table("users").update(
            {"ansia_principale": nuova_paura}
        ).eq("id", user_id).execute()
        return self._prima(risultato)

    def save_fear_history(self, riga: dict) -> None:
        self._client.table("fears_history").insert(riga).execute()
