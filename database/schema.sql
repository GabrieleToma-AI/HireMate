-- database/schema.sql — HireMate (Collega 1, Stream 1)
--
-- Sistema verificabile: si applica in Supabase (SQL Editor) o su PostgreSQL
-- (>= 13, `gen_random_uuid()` integrato) con: psql -f database/schema.sql
--
-- Colonne di users sono il mirror del TODO §3.1, non da inventare.

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nickname TEXT NOT NULL UNIQUE,
    pin_hash TEXT NOT NULL,                          -- solo hash bcrypt, mai in chiaro
    corso TEXT NOT NULL,
    ansia_principale TEXT NOT NULL,
    stile_gestione_problemi TEXT NOT NULL,
    timore_critico TEXT NOT NULL,
    cv_json JSONB,                                   -- outpu di /api/cv/parse, mai il PDF
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_nickname ON users(nickname);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    corso TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    report JSONB
);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

CREATE TABLE turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    numero INTEGER,                                  -- lo riempie il futuro /turn (Collega 2)
    domanda TEXT,
    trascrizione TEXT,
    chiarezza INTEGER DEFAULT 0,
    struttura_star INTEGER DEFAULT 0,
    esempi_concreti INTEGER DEFAULT 0,
    suggerimento TEXT,
    better_answer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_turns_session_id ON turns(session_id);

CREATE TABLE fears_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID,
    vecchia_paura TEXT NOT NULL,
    nuova_paura TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
