"""Interfaccia del client DB (Collega 1, Stream 1).

Contiene gli utenti, le sessioni, i turni e la storia delle paure.
Implementazioni: `SupabaseClient` (database/supabase_client.py, reale)
e `FakeDbClient` (database/fake_client.py, per i test offline).
Per swappare un client nei test: la classe Fake è la stessa interfaccia
e accetta gli stessi parametri, quindi i router usano solo `DbClient`.
"""


class DbClient:
    """Astrazione del database sottostante: per ora Supabase, poi DB alternativi."""

    def find_user_by_nickname(self, nickname: str) -> dict | None:
        """Restituisce l'utente con quel nickname, oppure None se non c'è."""
        raise NotImplementedError

    def create_user(self, user: dict) -> dict:
        """Salva un utente nuovo (nickname univoco). Restituisce il record salvato."""
        raise NotImplementedError

    def save_user_cv(self, user_id: str, cv_json: dict | None) -> None:
        """Aggiorna users.cv_json (output di /api/cv/parse). Mai il PDF."""
        raise NotImplementedError

    def get_user_cv(self, user_id: str) -> dict | None:
        """Legge users.cv_json: None se mai salvato."""
        raise NotImplementedError

    def create_session(self, session: dict) -> dict:
        """Salva una nuova sessione (user_id, corso, ...). Restituisce il record."""
        raise NotImplementedError

    def save_turn(self, turno: dict) -> None:
        """Salva un turno della cronologia (domanda, trascrizione, voti)."""
        raise NotImplementedError

    def get_turns(self, session_id: str) -> list[dict]:
        """Legge i turni di una sessione, in ordine di creazione."""
        raise NotImplementedError

    def update_user_fear(self, user_id: str, nuova_paura: str, session_id: str | None = None) -> dict:
        """Aggiorna users.ansia_principale a `nuova_paura`. Restituisce l'utente."""
        raise NotImplementedError

    def save_fear_history(self, riga: dict) -> None:
        """Appende una riga a fears_history (vecchia_paura -> nuova_paura)."""
        raise NotImplementedError
