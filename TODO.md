# ✅ TODO — cosa manca (aggiornato 20/11/2026)

Questo è **l'unico documento dei task** di HireMate: sostituisce `split_lavoro.md`, `handoff.md` e i TO DO sparsi nei vecchi recap.

- **Stato di partenza:** `main` è allineata a `origin/main`; i documenti sono consolidati nei 5 file attuali e il contratto `sessionId` è mergiato.
- **Regola:** si spunta una casella solo quando il criterio di accettazione è soddisfatto e i test sono verdi.
- **Legenda proprietari:** `[C1]` Collega 1 (Stream 1), `[C2]` Collega 2 (Stream 2), `[S3]` Stream 3 (GenAI core), `[AR/VR]` team frontend.

---

## 0. Stato di partenza

### Già fatto e testato (non serve rifarlo)

- Backend GenAI core: `/start`, `/end`, Interviewer, Evaluator, Reporter, wrapper LLM.
- Profilo ufficiale in `profilo.py` con validazione stretta.
- Paura superata sulla **metrica specifica** (≥ 7.5), sticky, `metrica_paura`, `prossime_paure`.
- Interviewer con `cronologia`, nessuna ripetizione, temperatura 0.8.
- Evaluator severo (risposte povere → 1-3), voti sempre 1-10.
- LLM con catena `FreeLLMAPI` → `gemini-3.5-flash-lite` → `deepseek-flash`, timeout per provider e 2 retry su Gemini.
- CV: `POST /api/cv/parse` (PDF max 5 MB → `cv_json`) con `pypdf` + LLM.
- API: validazione Pydantic, `turnId` univoco, CORS, errori 400/422/503/500.
- `TurnRequest` / `TurnResponse` / `Turno` pronti (manca solo l'endpoint `/turn`).
- Test: `test_enorme.py` 88/88 offline; 91/91 con `--live`. Gli altri test sono verdi.
- Documenti: i 5 file attuali (`AGENTS.md`, `README.md`, `FUNZIONAMENTO.md`, `RECAP.md`, `TODO.md`).

### Non fatto (oggetto di questo TODO)

- Supabase (tabelle, client, persistenza).
- Auth nickname + PIN (hash bcrypt) e `PATCH /api/users/update-fear`.
- Endpoint `POST /api/session/turn`.
- TTS Azure + visemi, anche per la prima domanda.
- `sessionId` propagato a `/turn` e `/end` quando esisterà il DB (oggi `/start` lo genera, gli altri lo accettano opzionale).
- `/end` che legge valutazioni e report dal DB (oggi si fida del client).
- Frontend (team AR/VR).
- Review delle PR nuove e merge su `main`.
- CI su GitHub Actions e protezione di `main` (oggi nulla impedisce un merge rosso).
- Hardening degli input (`max_length` su trascrizione, domanda, `cv_json`).
- Igiene del repository (`.gitattributes`, `.editorconfig`).
- Test senza assert (`test_int_eval.py`) e `test_api_full.py` che esce 0 con server spento.

---

## 1. TO DO generale

Vista d'insieme, in ordine di milestone. Il dettaglio per persona è nelle sezioni 3-5.

### Blocco 0 — Contratto condiviso `[S3]`

- [x] Aggiungere `sessionId` (uuid4) alla risposta di `/start`.
- [x] Aggiornare `TurnRequest` e `EndSessionRequest` con `sessionId`, mantenendo i campi legacy per la transizione.
- [x] Congelare le forme JSON finali (sezione 2) e aggiornare `README.md` / `FUNZIONAMENTO.md`.
- [ ] Comunicare a Collega 1 e Collega 2 di branchare da `main` e di usare i modelli senza duplicarli.
- [x] Aprire la PR del contratto.

### Blocco 0.5 — Guardrail (prima di integrare) `[S3]`

Sono le cose che rendono sicuri tutti gli altri blocchi: prima la CI, poi la protezione del branch.

- [ ] **CI su GitHub Actions**: `.github/workflows/test.yml` su push e PR; Python 3.14 con fallback 3.13; `pip install -r requirements.txt`; `python test_enorme.py`. Verde su una PR di prova, rosso se si rompe un test di proposito.
- [ ] **Protezione di `main`**: check della CI obbligatorio, merge solo via PR. Oggi `main` non è protetta.
- [ ] **Hardening degli input**: `max_length` su `trascrizione`, `domanda` e `cv_json` nei modelli di `routers/sessions.py` (es. 2000 caratteri) → `422`, con test dedicati.
- [ ] **Igiene del repository**: `.gitattributes` (`* text=auto`) e `.editorconfig` (UTF-8), per chiudere i due incidenti già visti: freeze UTF-16 e fine riga incoerenti.
- [ ] **Qualità dei test**: `test_int_eval.py` senza assert (o lo si rende un test vero, o diventa `demo_int_eval.py`) e `test_api_full.py` che oggi esce 0 anche quando il server non è attivo.
- [ ] **Baseline di demo**: server avviato, `test_api_full.py`, `/docs`, CORS e codici 422/415/503 con output attesi salvati come riferimento.

### Blocco 1 — Fondamenta (in parallelo) `[C1]` `[C2]` `[S3]`

- [ ] `[C1]` Progetto Supabase + variabili d'ambiente (`SUPABASE_URL`, `SUPABASE_KEY`, `JWT_SECRET`).
- [ ] `[C1]` Tabelle `users`, `sessions`, `turns`, `fears_history` + indici.
- [ ] `[C1]` `database/supabase_client.py` con le funzioni CRUD.
- [ ] `[C1]` `routers/users.py`: register/login con PIN hash bcrypt, JWT, rate limit.
- [ ] `[C1]` `PATCH /api/users/update-fear`.
- [ ] `[C2]` Spike TTS Azure: `genera_audio(testo) -> (audioUrl, visemes)`.
- [ ] `[C2]` `routers/turn.py` con `/turn` e LLM mockato.
- [ ] `[C2]` `static/audio/` + snippet `StaticFiles` da passare a Stream 3.
- [ ] `[S3]` Modelli aggiornati a `sessionId` + test estesi (mock).

### Blocco 2 — Integrazione `[C1]` `[C2]` `[S3]`

- [ ] `[C1]` CV salvato come `cv_json` nel DB (schema `CvJson`), mai il PDF.
- [ ] `[C1]` `/end` può leggere il report precedente di un utente/sessione.
- [ ] `[C2]` `/turn` reale: valutazione server-side, salvataggio turno, prossima domanda.
- [ ] `[C2]` Audio anche su `/start` con lo stesso helper.
- [ ] `[C2]` `/end` server-side: valutazioni dal DB, non dal client.
- [ ] `[S3]` `/start` e `/end` collegati al DB, con fallback legacy.
- [ ] `[S3]` Test integrati + test "utente scarso".

### Blocco 3 — Chiusura `[S3]` `[C2]` `[C1]` `[AR/VR]`

- [ ] Colloquio completo di 6 turni con DB, auth e audio (o fallback).
- [ ] Frontend AR/VR sul contratto finale (`sessionId`, `audioUrl`, `visemes`, `metrica_paura`, `prossime_paure`).
- [ ] Review delle PR, merge su `main` solo a test verdi.
- [ ] Demo, documenti aggiornati, push finale.

### Milestone

| Milestone | Cosa deve funzionare |
|---|---|
| **M0** | Contratto congelato, branch creati da `main`, PR aperta |
| **M1** | Auth + DB CRUD; `/turn` con mock; TTS smoke test |
| **M2** | 6 turni reali con DB; `/end` dal DB; audio o fallback |
| **M3** | Demo completa, test verdi, documenti, merge |

---

## 2. Contratto condiviso (blocco 0)

Da chiudere **prima** di implementare DB, `/turn` e TTS.

### 2.1 `sessionId`

`/start` restituisce `sessionId` (uuid4) accanto a `turnId`; `TurnRequest` ed `EndSessionRequest` lo accettano come campo **opzionale** durante la transizione (senza DB la cronologia viaggia ancora nel payload).

- [x] `/start` genera `sessionId` e lo restituisce;
- [ ] `/turn` riceve `sessionId` e salva il turno (Collega 2);
- [ ] `/end` riceve `sessionId` e legge tutto dal DB (Collega 1);
- [ ] il DB collega `users` → `sessions` → `turns`.

**Proprietario:** Stream 3 modifica `routers/sessions.py`. Collega 1 e 2 lo usano, non lo modificano.

### 2.2 Forme JSON

**`POST /api/session/start`** — richiesta invariata:

```json
{
  "corso": "Cyber Security Specialist",
  "profilo_soft_skill": {
    "ansia_principale": "Restare senza parole",
    "stile_gestione_problemi": "Mi blocco e mi faccio prendere dal panico",
    "timore_critico": "Non ho abbastanza esperienza tecnica per il ruolo"
  },
  "cv_json": {"competenze": ["Python"], "progetti": ["Rete aziendale"]}
}
```

Risposta (nuova):

```json
{
  "sessionId": "uuid",
  "turnId": "turn-uuid",
  "questionText": "Testo della domanda",
  "audioUrl": "/static/audio/sessionId/turnId.mp3",
  "visemes": [{"time": 0, "visemeId": 1}],
  "gesture": "explain"
}
```

**`POST /api/session/turn`** (nuovo, Collega 2):

```json
{
  "sessionId": "uuid",
  "domanda": "Domanda appena fatta",
  "trascrizione": "Risposta dello studente"
}
```

In transizione (DB non pronto) si può aggiungere `cronologia` come fallback; dopo il DB la legge il server.

Risposta:

```json
{
  "turnId": "turn-uuid",
  "valutazione": {
    "chiarezza": 8,
    "struttura_star": 7,
    "esempi_concreti": 9,
    "suggerimento": "…",
    "better_answer": "…"
  },
  "prossimaDomanda": "… oppure null",
  "colloquio_terminato": false,
  "audioUrl": "/static/audio/…mp3",
  "visemes": [{"time": 0, "visemeId": 1}],
  "gesture": "explain"
}
```

`colloquio_terminato` diventa `true` dopo `DOMANDE_PER_COLLOQUIO = 6` (o quando il Reporter ha abbastanza informazioni).

**`POST /api/session/end`** — oggi:

```json
{
  "corso": "…",
  "profilo_soft_skill": {},
  "valutazioni": [],
  "report_precedente": null
}
```

Obiettivo finale:

```json
{"sessionId": "uuid"}
```

Il server legge dal DB valutazioni, profilo e report precedente. In transizione si accettano ancora `valutazioni` e `report_precedente`, ma sono **deprecati**.

### 2.3 Auth (Collega 1)

- `POST /api/users/register`: nickname, PIN 4 cifre, profilo, `cv_json` opzionale → `{user_id, token}`.
- `POST /api/users/login`: nickname, PIN → `{user_id, token}`; PIN errato → `401` con messaggio generico.
- `PATCH /api/users/update-fear`: `Authorization: Bearer <token>`, body `{nuova_paura}`; deve essere in `PAURE_DISPONIBILI` e diversa da quella attuale.
- PIN **solo hash bcrypt**, mai in chiaro, mai nei log.
- Rate limit sul login (es. 5 tentativi, poi attesa) perché un PIN di 4 cifre ha solo 10.000 combinazioni.

### 2.4 Proprietà dei modelli

- `ProfiloSoftSkill`, `Valutazione`, `ValutazioneCompleta`, `Turno`, `TurnRequest`, `TurnResponse`, `SessionStart*`, `EndSession*` → **Stream 3** in `routers/sessions.py`.
- Collega 2 **importa** i modelli in `routers/turn.py`; non li duplica.
- Collega 1 usa `ProfiloSoftSkill` e `PAURE_DISPONIBILI` per registrazione e `update-fear`.

---

## 3. TO DO — Collega 1 (Stream 1: Data, Auth e CV)

**Obiettivo:** rendere il progetto persistente e autenticato; il CV diventa un dato salvato, non solo restituito.

### P0 — Da fare subito

1. **Supabase**
   - Creare progetto e variabili: `SUPABASE_URL`, `SUPABASE_KEY` (service role, solo backend), `JWT_SECRET`.
   - Tabelle:
     - `users`: `id`, `nickname` unique, `pin_hash`, `corso`, `ansia_principale`, `stile_gestione_problemi`, `timore_critico`, `cv_json` jsonb, `created_at`, `updated_at`.
     - `sessions`: `id`, `user_id`, `corso`, `started_at`, `ended_at`, `report` jsonb.
     - `turns`: `id`, `session_id`, `numero`, `domanda`, `trascrizione`, `chiarezza`, `struttura_star`, `esempi_concreti`, `suggerimento`, `better_answer`, `created_at`.
     - `fears_history`: `id`, `user_id`, `session_id`, `vecchia_paura`, `nuova_paura`, `created_at`.
   - Indici su `nickname`, `sessions.user_id`, `turns.session_id`.
2. **`database/supabase_client.py`**
   - `create_user`, `get_user_by_nickname`, `create_session`, `save_turn`, `get_turns`, `get_last_report`, `update_user_fear`, `save_fear_history`.
3. **Auth**
   - `routers/users.py`: register/login con PIN hash bcrypt.
   - Token JWT breve (`PyJWT`), `sub=user_id`, scadenza 24h.
   - Rate limit login; messaggi generici per non rivelare se il nickname esiste.
4. **`PATCH /api/users/update-fear`**
   - Autenticato; valida `nuova_paura` contro `PAURE_DISPONIBILI`; aggiorna `users` e scrive `fears_history`.
5. **CV**
   - `routers/cv.py` e `agenti/cv_parser.py` passano a te: aggiungi lo schema Pydantic `CvJson` (`competenze: list[str]`, `progetti: list[str]`), salva `cv_json` in `users.cv_json`, documenta che i PDF scansionati (solo immagini) non sono supportati.
   - Non salvare il PDF: solo il JSON. Privacy: non loggare contenuti del CV.

### P1 — Subito dopo

- [ ] RLS/policy Supabase e uso della service key solo lato server.
- [ ] Test `test_db.py` / `test_auth.py` con mock del client Supabase (niente chiavi reali in CI).
- [ ] Documentazione schema + setup.
- [ ] Aggiungere a `requirements.txt`: `supabase`, `bcrypt`, `PyJWT`; a `.env.example`: chiavi Supabase/JWT (le righe le inserisce Stream 3 nel merge).

### Dipendenze

- `sessionId` da Stream 3.
- `paura_attuale`, `metrica_paura`, `prossime_paure` da `agenti/reporter.py` (già pronti).
- `PAURE_DISPONIBILI` da `profilo.py`.

### Criteri di accettazione

- [ ] Registrazione e login funzionano; PIN errato → 401; nel DB c'è solo `pin_hash`.
- [ ] Le 4 tabelle esistono e il client salva/legge.
- [ ] `update-fear` aggiorna il profilo e scrive la storia.
- [ ] `/end` può leggere il report precedente di un utente/sessione.
- [ ] Il CV viene salvato come JSON, non come PDF.
- [ ] Test verdi e nessuna chiave nei file tracciati.

---

## 4. TO DO — Collega 2 (Stream 2: Turn API e Audio)

**Obiettivo:** il colloquio diventa multi-turno con valutazione server-side e voce dell'avatar.

### P0 — Da fare subito

1. **`routers/turn.py` — `POST /api/session/turn`**
   - Importa `TurnRequest`/`TurnResponse` da `routers/sessions.py`.
   - Riceve `sessionId`, `domanda`, `trascrizione`.
   - Recupera profilo, CV e cronologia dal DB (o dal payload in transizione).
   - Chiama `valuta_risposta(...)`.
   - Salva il turno (Collega 1: `save_turn`).
   - Aggiorna la cronologia e chiama `genera_domanda(..., cronologia=...)`.
   - Dopo 6 domande: `colloquio_terminato: true`, `prossimaDomanda: null`.
2. **TTS Azure — `agenti/tts.py`**
   - `genera_audio(testo) -> (audioUrl, visemes)`.
   - Variabili: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `AZURE_VOICE`.
   - Salva mp3 in `static/audio/{sessionId}/{turnId}.mp3`; Stream 3 monta `StaticFiles` in `main.py`.
   - Visemi: lista `[{"time": ms, "visemeId": int}]`; conferma il formato con il team AR/VR.
   - Se Azure non è configurato o fallisce: `audioUrl=None`, `visemes=[]`, il turno continua.
3. **Audio anche su `/start`**
   - Oggi `/start` restituisce `audioUrl=None`, `visemes=[]`: aggiungi la TTS della prima domanda, con lo stesso helper.
4. **`/end` con valutazioni server-side**
   - Collega 1 fornisce le valutazioni salvate; `end_session` non deve più fidarsi del client.
   - In transizione accetta ancora `valutazioni`, poi le ignora quando il DB è pronto.

### P1 — Subito dopo

- [ ] Cache audio per testi ripetuti (facoltativa).
- [ ] Test `test_turn.py` / `test_tts.py` con mock; smoke test TTS reale solo se le chiavi Azure sono presenti.
- [ ] Documentazione `/turn`, `audioUrl`, `visemes`, variabili Azure.
- [ ] Aggiungere `azure-cognitiveservices-speech` a `requirements.txt`; chiavi in `.env.example` (righe fornite a Stream 3).

### Dipendenze

- `sessionId` e modelli da Stream 3.
- Funzioni DB da Collega 1.
- Formato visemi dal team AR/VR.
- `main.py` e `requirements.txt` li modifica Stream 3 su richiesta.

### Criteri di accettazione

- [ ] Un colloquio di 6 turni funziona via API: ogni turno restituisce valutazione, prossima domanda e audio (o fallback).
- [ ] `colloquio_terminato=true` al sesto turno.
- [ ] I turni sono salvati nel DB; `/end` usa le valutazioni server-side.
- [ ] Se Azure manca, il colloquio funziona comunque senza audio.
- [ ] Test verdi, nessuna chiave nei file tracciati.

---

## 5. TO DO — Stream 3 (tu: GenAI core, integrazione e qualità)

**Obiettivo:** tenere insieme i pezzi, congelare il contratto, aggiornare i test e portare il progetto alla demo.

### P0 — Da fare subito

1. **Allineamento e PR**
   - `main` è allineata a `origin/main`; contratto `sessionId`, documenti e `AGENTS.md` sono mergiati.
   - Comunicazione a Collega 1 e 2: partono da `main` e importano i modelli da `routers/sessions.py`.
2. **`sessionId` e contratto**
   - `sessionId` è in `/start`; `TurnRequest`/`EndSessionRequest` lo accettano come opzionale; i campi legacy restano per la transizione.
   - Definisci le forme JSON finali (sezione 2) e aggiorna `README.md`/`FUNZIONAMENTO.md`.
3. **`main.py`**
   - Includi `routers/turn.py` e monta `static/`.
   - Sei l'unico proprietario di `main.py`: Collega 2 ti passa lo snippet, tu lo applichi.
4. **Reporter + DB**
   - Quando Collega 1 è pronto, `/end` legge il report precedente dal DB e non da `report_precedente`.
   - Mantieni il fallback client solo per la transizione.

### P1 — Integrazione e qualità

- [ ] **Test reali utente scarso**: una risposta vuota/povera deve dare metriche basse; con `/turn` la valutazione è server-side, non più fidata dal client.
- [ ] **Prompt** (diagnosi in [RECAP §6.9](RECAP.md#69-diagnosi-dei-prompt-rimandata)): rubrica esplicita per l'Evaluator, numero di domanda e copertura dei temi per l'Interviewer, limiti di lunghezza per il Reporter. Rimandato: non è bloccante.
- [ ] **Test**: estendi `test_enorme.py` con `sessionId`, `/turn` (mock), DB/auth (mock), TTS (mock); mantieni 88/88 offline; live quando la modifica tocca l'LLM.
- [ ] **Sicurezza**: niente chiavi, CORS, limiti di input, PIN hash, rate limit, errori generici.
- [ ] **Contratto frontend**: conferma con AR/VR `sessionId`, `audioUrl`, `visemes`, `metrica_paura`, `prossime_paure`.
- [ ] **Documenti**: aggiorna i 5 file a ogni cambio di contratto.

### P2 — Chiusura

- [ ] Review delle PR di Collega 1 e 2.
- [ ] Merge su `main` solo a test verdi, con review.
- [ ] Demo finale: registrazione, CV, 6 turni, risposta scarsa, report, promozione paura, cambio paura.

### Criteri di accettazione

- [ ] `/start`, `/turn`, `/end` usano `sessionId`.
- [ ] Un colloquio completo di 6 turni funziona con DB, auth e audio (o fallback).
- [ ] `/end` non si fida più delle valutazioni del client.
- [ ] Test offline/live verdi; documenti aggiornati; nessuna chiave committata.
- [ ] Branch pushato e PR mergiata su `main`.

---

## 6. TO DO — team AR/VR & game (fuori perimetro backend)

Serve al backend sapere **cosa** il frontend si aspetta; questi punti vanno concordati, non implementati dagli AI engineer.

- [ ] Card delle 4 paure identiche a `PAURE_DISPONIBILI` (altrimenti mostra paure sconosciute).
- [ ] Modale "Promozione Paura" che si apre con `paura_superata: true` e mostra le 3 `prossime_paure`.
- [ ] Report animato con `stats_previous` → `stats_current` e `overall_previous` → `overall_current`.
- [ ] Avatar 3D sincronizzato con `audioUrl` + `visemes` (`time` in ms, `visemeId` intero).
- [ ] Onboarding in stile Typeform/Tinder + push-to-talk (Web Speech API).
- [ ] Conferma il formato visemi a Collega 2 prima del merge di `/turn`.

---

## 7. Matrice file → proprietario

| File / area | Proprietario | Note |
|---|---|---|
| `main.py` | Stream 3 | Solo tu: include router e static; gli altri ti passano gli snippet |
| `routers/sessions.py` | Stream 3 | Modelli e `/start`/`/end`; Collega 2 importa i modelli, non li modifica |
| `agenti/interviewer.py`, `evaluator.py`, `reporter.py`, `llm.py` | Stream 3 | Core GenAI |
| `profilo.py`, `corsi.py` | Stream 3 | Dati e regole |
| `test_enorme.py`, `test_reporter.py`, `test_sistema.py`, `test_interviewer.py`, `test_int_eval.py` | Stream 3 | Test e qualità |
| `README.md`, `FUNZIONAMENTO.md`, `RECAP.md`, `TODO.md` | Stream 3 | Documenti e contratto |
| `requirements.txt`, `.env.example` | Stream 3 (merge) | Collega 1/2 forniscono le righe, tu fai il merge finale |
| `database/`, `routers/users.py` | Collega 1 | Supabase, auth |
| `routers/cv.py`, `agenti/cv_parser.py` | Collega 1 | CV end-to-end; Stream 3 rivede il prompt |
| `test_db.py`, `test_auth.py` | Collega 1 | Nuovi test |
| `routers/turn.py` | Collega 2 | Nuovo endpoint `/turn` |
| `agenti/tts.py`, `static/audio/` | Collega 2 | Azure TTS e visemi |
| `test_turn.py`, `test_tts.py` | Collega 2 | Nuovi test |

---

## 8. Regole di lavoro e Definition of Done

### Regole di lavoro

1. **Base di partenza**: `main` è allineata a `origin/main`. Ogni stream crea il proprio branch **da `main`**.
2. **Un branch per stream**: `feature/db-auth`, `feature/turn-audio`, `feature/contratto-sessionid` (o nome equivalente).
3. **Niente commit su `main`**; PR verso `main` con review.
4. **Niente `.env` o chiavi** nei commit, nei log o nelle chat. La chiave Gemini free è autorizzata **solo per i test**; se un giorno la cartella viene condivisa o sincronizzata fuori dal PC, le chiavi vanno ruotate.
5. **Un solo proprietario per file** (matrice in sezione 7). Se serve modificare un file di un altro, si chiede al proprietario.
6. **Test prima della PR**: `python test_enorme.py`; per le parti nuove, test dedicati.
7. **Contratto API congelato** prima di scrivere codice (sezione 2).
8. **Lingua e registro**: italiano semplice e didattico; ogni concetto tecnico spiegato con *cos'è, perché serve, cosa succede senza*. Il progetto è scolastico: deve restare corto, completo e spiegabile al professore.
9. **Documenti**: in root ci sono esattamente **5 `.md`** (`AGENTS.md` + i 4 di progetto). Il test della sezione 9 confronta la lista esatta: un sesto `.md` lo fa fallire.

### Workflow quando viene chiesta una modifica

1. Leggere i file coinvolti e il contratto API.
2. Applicare la modifica **minima e spiegabile**.
3. Eseguire test offline e, solo se serve, test end-to-end.
4. Consegnare il riepilogo nell'ordine: *cosa ho cambiato → perché → come verificarlo → come spiegarlo al prof → impatto sui colleghi*.

### Definition of Done (per ogni stream)

- [ ] Codice con test (unit/integration) verdi.
- [ ] `python test_enorme.py` verde; live test se la modifica tocca l'LLM.
- [ ] Documentazione aggiornata (`README.md` o gli altri 3 file).
- [ ] Nessuna chiave, `.env`, `venv` o file temporaneo committato.
- [ ] PR con review di almeno un altro AI engineer.
- [ ] Nessun commit diretto su `main`.

---

## 9. Ordine e tempi

| Blocco | Contenuto | Chi | Tempo indicativo |
|---|---|---|---|
| **Blocco 0 — Sbloccare** | Allineamento, contratto `sessionId`, PR | Stream 3 | 2-3 ore |
| **Blocco 0.5 — Guardrail** | CI, protezione `main`, hardening, igiene, qualità test, baseline | Stream 3 | ~3 ore |
| **Blocco 1 — Fondamenta** | Schema Supabase + client + auth; spike TTS + `/turn` mock; test estesi | C1, C2, S3 (parallelo) | 2-3 giorni |
| **Blocco 2 — Integrazione** | CV salvato, `/end` dal DB; `/turn` reale, audio su `/start` | C1, C2, S3 | 3-4 giorni |
| **Blocco 3 — Chiusura** | End-to-end 6 turni, frontend, demo, documenti, merge | Tutti | 1-2 giorni |

**Ordine consigliato:** contratto → DB/auth → `/turn` con mock → TTS → integrazione → demo.

---

## 10. Rischi e decisioni aperte

- **Base allineata:** `main` è allineata a `origin/main`; ogni stream brancha da lì per non divergere.
- **Nessun guardrail automatico:** senza CI un test rosso può essere mergiato, e `main` non è protetta. Sono i primi due task del Blocco 0.5.
- **OneDrive:** `git fetch --prune` può fermarsi su `Deletion of directory ... failed` (directory-reparse). Risposta `n`, poi `git update-ref -d <ref>`; non è corruzione del repo.
- **DeepSeek:** è a pagamento e resta l'ultima risorsa; monitorare chiave e costi, non usarlo nei test di massa.
- **Contratto `sessionId`:** va congelato prima di DB e `/turn`, altrimenti si sovrascrivono.
- **Auth:** PIN a 4 cifre → bcrypt + rate limit obbligatori; token JWT breve.
- **Supabase:** service key solo backend; RLS da configurare; niente chiavi nel frontend.
- **Azure:** chiavi e latenza; il turno deve funzionare anche senza audio.
- **Audio:** decidere se salvare su disco (`static/`) o su storage; per il SAL va bene `static/`.
- **Visemi:** formato da concordare con AR/VR (`time` in ms, `visemeId`).
- **`/end`:** cambio di contratto; mantenere i campi legacy per una transizione.
- **File condivisi:** `main.py`, `routers/sessions.py`, `requirements.txt`, `.env.example` → un solo proprietario/merge.
- **Tempo:** la parte più rischiosa è DB + auth; se slitta, TTS può restare mock e l'audio può essere disattivato.

---

## 11. Demo checklist

1. [ ] Registrazione (nickname + PIN) e login.
2. [ ] Upload CV → `cv_json`.
3. [ ] `/start` → `sessionId`, prima domanda, audio (o fallback).
4. [ ] 6 turni: domanda → risposta → valutazione → prossima domanda.
5. [ ] Una risposta **volutamente scarsa** → metriche basse.
6. [ ] `/end` → report, `paura_superata`, `metrica_paura`, `prossime_paure`.
7. [ ] Modale "Promozione Paura" → scelta nuova paura → `PATCH update-fear`.
8. [ ] Mostrare `python test_enorme.py` 88/88; `--live` quando serve dimostrare l'LLM reale.
9. [ ] Mostrare branch/PR e i documenti aggiornati.
10. [ ] Mostrare la CI verde su una PR di prova (quando il Blocco 0.5 è fatto).
