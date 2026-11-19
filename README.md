# 📋 HIREMATE — Backend GenAI

Simulatore di colloqui HR per studenti ITS ICT Piemonte. Il backend gestisce la profilazione, la generazione delle domande, la valutazione delle risposte e il report finale gamificato.

- **Lingua:** italiano.
- **Target:** studenti junior IT (tono professionale, diretto, non "coccoloso").
- **Team:** 3 AI engineer (Python) + 3 AR/VR & game (frontend).
- **Stack:** Python 3.14.8, FastAPI, Pydantic v2, `google-genai`, `pypdf`; Supabase e Azure TTS in arrivo.

---

## 📚 I documenti del progetto

Da questo momento i documenti sono **quattro** e stanno tutti nella root del progetto: niente più file sparsi che si duplicano.

| Documento | Cosa contiene | Quando leggerlo |
|---|---|---|
| **`README.md`** (questo file) | Panoramica, struttura, API, setup, test, stato del progetto | Per primo |
| [`FUNZIONAMENTO.md`](FUNZIONAMENTO.md) | Guida didattica: cosa fa ogni file, flusso completo, concetti da esame, regole di lettura del codice, come funzionano i test, domande del prof | Per capire il codice |
| [`RECAP.md`](RECAP.md) | Diario dei lavori, changelog, errori trovati e corretti, scelte di codice e di feature, come riprendere il progetto | Per capire *perché* il codice è così |
| [`TODO.md`](TODO.md) | Cosa manca: TO DO generale + TO DO per ciascuno dei 3 AI engineer, contratto API, regole di lavoro, demo checklist | Per lavorare |

Ordine consigliato in una nuova chat: **README → FUNZIONAMENTO → RECAP → TODO**.

---

## 🏗️ Struttura

| File | Cosa fa |
|---|---|
| `main.py` | Crea FastAPI, configura il CORS, include i router. |
| `corsi.py` | 14 corsi ITS con materie e focus HR; `get_dettagli_corso()`; `CorsoNonValidoError`. |
| `profilo.py` | Le 3 liste della profilazione, `METRICA_PER_PAURA`, `SOGLIA_METRICA_PAURA = 7.5`. |
| `agenti/llm.py` | Wrapper LLM: FreeLLMAPI → Gemini Lite → DeepSeek, timeout per provider, 2 retry su Gemini, JSON robusto. |
| `agenti/interviewer.py` | Genera la domanda (prima o successiva, con `cronologia`), temperatura 0.8. |
| `agenti/evaluator.py` | Valuta la trascrizione: chiarezza, STAR, esempi, suggerimento, better answer; voti 1-10. |
| `agenti/reporter.py` | Report finale: overall, stats, `paura_attuale`, `metrica_paura`, `paura_superata`, `prossime_paure`, badges. |
| `agenti/cv_parser.py` | Estrae il testo dal PDF con `pypdf` e lo trasforma in JSON. |
| `routers/sessions.py` | Modelli Pydantic e endpoint `/start`, `/end`; contratti `/turn`. |
| `routers/cv.py` | Endpoint `POST /api/cv/parse` (PDF → JSON). |
| `test_enorme.py` | Suite principale: 88 test offline, 91 con `--live`. |
| `test_reporter.py` | Test offline della regola "paura superata". |
| `test_sistema.py`, `test_interviewer.py`, `test_int_eval.py`, `test_api_full.py` | Test con LLM reale / API reale. |
| `.env.example` | Modello delle variabili d'ambiente (da copiare in `.env`). |
| `.gitignore` | Esclude `venv/`, `.env`, `__pycache__/`. |

### Stato attuale (19/11/2026)

- `main` = `e62ac4c` (PR #1 già mergiata): il backend GenAI è **pushato**.
- Funzionanti e testati: `/api/cv/parse`, `/api/session/start`, `/api/session/end`.
- Non ancora implementati: `POST /api/session/turn`, Supabase, auth, TTS/visemi, `sessionId`, montaggio `static/`.
- Test: **88/88 offline**; **91/91 con `--live`** (3 chiamate reali).

---

## 🔄 Flusso di una sessione

```text
1. (opzionale) PDF del CV ──► POST /api/cv/parse ──► cv_json
2. profilo + corso + cv_json ──► POST /api/session/start ──► prima domanda
3. risposta dello studente ──► POST /api/session/turn ──► valutazione + prossima domanda
   (ripetere per ~6 turni)
4. valutazioni ──► POST /api/session/end ──► report + paura superata + prossime paure
```

> Il passo 3 è **il pezzo che manca**: i modelli `Turno`, `TurnRequest` e `TurnResponse` sono pronti in `routers/sessions.py`, ma l'endpoint lo implementa Collega 2 (vedi [TODO.md](TODO.md)).

---

## 🧭 Profilazione (3 domande)

**Q2 — Ansia** (`ansia_principale`): *"Cosa ti spaventa di più all'idea di fare un colloquio?"*

1. Restare senza parole
2. Non sembrare abbastanza preparato tecnicamente
3. Fare una figuraccia con il recruiter
4. Non saper parlare di me stesso

**Q3 — Reazione ai problemi** (`stile_gestione_problemi`): *"Quando ti trovi di fronte a un problema difficile, come reagisci?"*

1. Mi blocco e mi faccio prendere dal panico
2. Chiedo subito aiuto a un collega o a un tutor
3. Faccio ricerche infinite finché non trovo la soluzione
4. Mi prendo una pausa e ci riprovo con calma

**Q4 — Timore di fallimento** (`timore_critico`): *"Se il colloquio andasse male, quale pensi sarebbe il motivo principale?"*

1. Non ho saputo spiegare bene le mie competenze
2. Ero troppo in ansia e non riuscivo a concentrarmi
3. Non ho abbastanza esperienza tecnica per il ruolo
4. Non mi sono preparato abbastanza sull'azienda

La validazione è **stretta**: un valore fuori lista restituisce `422` e non arriva mai all'LLM.

---

## 🎯 Regola "paura superata"

| Paura (Domanda 2) | Metrica |
|---|---|
| Restare senza parole | `chiarezza` |
| Non sembrare abbastanza preparato tecnicamente | `esempi_concreti` |
| Fare una figuraccia con il recruiter | `struttura_star` |
| Non saper parlare di me stesso | `chiarezza` |

- La paura è superata quando **la metrica specifica** arriva a **7.5/10**, non quando l'overall è alto.
- **Sticky:** una volta superata per la stessa paura, resta superata anche se nella sessione successiva la metrica scende.
- Se la paura cambia, il flag riparte da `false`: la nuova paura non è ancora stata affrontata.
- `metrica_paura` dice quale metrica ha fatto scattare la promozione.
- `prossime_paure` contiene le altre 3 paure della Domanda 2 (solo se `paura_superata` è `true`).

La regola è in Python puro (`agenti/reporter.py`): deterministica, testabile, senza LLM.

---

## 🔌 API

### `POST /api/cv/parse`

Multipart con campo `file` (PDF, max 5 MB) → `{"cv_json": {"competenze": [...], "progetti": [...]}}`.
Errori: `415` tipo non PDF, `400` file vuoto/PDF illeggibile/senza testo, `413` troppo grande, `503` LLM giù, `500` generico.

### `POST /api/session/start`

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

Risposta:

```json
{"turnId": "turn-...", "questionText": "...", "audioUrl": null, "visemes": [], "gesture": "explain"}
```

### `POST /api/session/turn` — **da implementare**

Contratto già pronto in `routers/sessions.py`: `TurnRequest` (`corso`, `profilo_soft_skill`, `cv_json`, `domanda`, `trascrizione`, `cronologia`) → `TurnResponse` (`turnId`, `valutazione`, `prossimaDomanda`, `colloquio_terminato`, `audioUrl`, `visemes`, `gesture`).

Dopo `DOMANDE_PER_COLLOQUIO = 6` domande, `colloquio_terminato` diventa `true` e `prossimaDomanda` è `null`. Dettagli e obiettivi in [TODO.md](TODO.md).

### `POST /api/session/end`

```json
{
  "corso": "Cyber Security Specialist",
  "profilo_soft_skill": {"ansia_principale": "...", "stile_gestione_problemi": "...", "timore_critico": "..."},
  "valutazioni": [{"chiarezza": 8, "struttura_star": 7, "esempi_concreti": 9}],
  "report_precedente": null
}
```

Risposta: `overall_previous`, `overall_current`, `stats_previous`, `stats_current`, `paura_attuale`, `metrica_paura`, `paura_superata`, `prossime_paure`, `badges`, `improvements`, `final_tip`.

> `report_precedente` è **temporaneo**: la fonte di verità sarà Supabase. Finché `/end` accetta `valutazioni` dal client, un client scorretto può mandare voti alti.

### Altri endpoint

| Metodo | Percorso | Cosa fa |
|---|---|---|
| `GET` | `/` | Messaggio di benvenuto e link a `/docs`. |
| `GET` | `/api/health` | Health check (engine, database, llm, status). |

### Codici di errore

| Codice | Significato |
|---|---|
| `422` | Input non valido (corso, profilo, voti fuori range, lista vuota). Scatta prima di chiamare l'LLM. |
| `400` | `CorsoNonValidoError` sollevata dentro l'endpoint (difensivo); oppure PDF non leggibile. |
| `413` | PDF oltre 5 MB. |
| `415` | File non PDF. |
| `503` | LLM non disponibile dopo i fallback: messaggio generico, nessun dettaglio interno. |
| `500` | Errore interno: log completo sul server, messaggio generico al client. |

---

## ⚙️ Setup

```powershell
cd C:\Users\gabri\OneDrive\Desktop\HireMate
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env    # poi inserisci le chiavi vere
python main.py                 # http://127.0.0.1:8000/docs
```

`.env` non va mai committato (è in `.gitignore`). Variabili previste da `.env.example`:

| Variabile | Default / esempio | A cosa serve |
|---|---|---|
| `FREELLMAPI_BASE_URL` | `http://localhost:3001/v1` | Endpoint locale del primo provider. |
| `FREELLMAPI_API_KEY` | segnaposto | Chiave FreeLLMAPI. |
| `FREELLMAPI_MODEL` | `auto:fastest` | Modello FreeLLMAPI. |
| `FREELLMAPI_TIMEOUT_SECONDS` | `3` | Timeout corto: se è giù si passa subito a Gemini. |
| `GEMINI_API_KEY` | segnaposto | Chiave Gemini. |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Modello unico Gemini. |
| `GEMINI_TIMEOUT_SECONDS` | `6` | Timeout del singolo tentativo (i retry restano). |
| `DEEPSEEK_API_KEY` | segnaposto | Chiave DeepSeek (a pagamento, ultima risorsa). |
| `DEEPSEEK_MODEL` | `deepseek-flash` | Id API del modello DeepSeek V4.1 Flash. |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | Endpoint DeepSeek (compatibile OpenAI). |
| `DEEPSEEK_TIMEOUT_SECONDS` | `30` | Timeout più lungo: è l'ultima risorsa. |
| `LLM_RETRY_DELAY_SECONDS` | `1.5` | Attesa tra i retry di Gemini su 503/429/timeout. |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173,...` | Origini autorizzate per il frontend. |

---

## 🧪 Test

```powershell
python test_enorme.py          # 88 test offline, mock LLM, nessuna quota
python test_enorme.py --live   # 91 test (aggiunge 3 chiamate reali a Gemini Lite)
```

Output atteso:

```text
TOTALE: 88   PASSATI: 88   FALLITI: 0
🎉 TUTTI I TEST SONO PASSATI
```

Con `--live` l'output atteso è `TOTALE: 91   PASSATI: 91   FALLITI: 0` (le 3 chiamate reali dipendono da chiavi e quota).

| Comando | Cosa verifica | Rete |
|---|---|---|
| `python test_enorme.py` | 9 sezioni: profilo, corsi, LLM, interviewer, evaluator, reporter, modelli/API, CV, config e documenti | no |
| `python test_enorme.py --live` | le 3 sezioni live: domanda vera, evaluator severo, reporter con LLM | sì |
| `python test_reporter.py` | regola "paura superata" (soglia 7.4/7.5, sticky, reset) | no |
| `python test_sistema.py` | corsi + LLM + evaluator | sì |
| `python test_interviewer.py` | due domande, con e senza CV | sì |
| `python test_int_eval.py` | catena Interviewer → Evaluator | sì |
| `python test_api_full.py` | `/start` e `/end` via HTTP (richiede il server attivo su `:8000`) | sì |

Cosa testa ogni sezione e come leggere i fallimenti: [FUNZIONAMENTO.md](FUNZIONAMENTO.md#6-i-test-come-funzionano-e-cosa-coprono).

---

## 👥 Divisione del lavoro

- **Stream 3 — GenAI core (tu):** `agenti/`, `corsi.py`, `profilo.py`, `main.py`, `routers/`, test e documenti.
- **Stream 1 — Collega 1:** Supabase (`users`, `sessions`, `turns`, `fears_history`), auth nickname + PIN con hash bcrypt, `PATCH /api/users/update-fear`, CV salvato nel DB.
- **Stream 2 — Collega 2:** endpoint `/turn`, Azure TTS + visemi, audio anche su `/start`, `/end` server-side.
- **Team AR/VR & game:** UI game-style, avatar 3D sincronizzato con gli audio, modale "Promozione Paura", report animato.

Le attività dettagliate, con criteri di accettazione e matrice file → proprietario, sono in [TODO.md](TODO.md).

---

## 🔐 Sicurezza

- `.env` è in `.gitignore`, non è tracciato e non compare nella history.
- Le chiavi non vanno mai stampate, incollate in chat, messe in un `.md` o committate.
- La chiave Gemini free è autorizzata **solo per i test**, caricata dall'app con `python-dotenv`.
- Il progetto è dentro OneDrive: se la cartella viene condivisa o sincronizzata fuori dal PC, le chiavi vanno **ruotate**.
- PIN dello studente: solo hash bcrypt, mai in chiaro, mai nei log (Collega 1).
- Errori generici al client: i dettagli (e le chiavi) restano nei log del server.
- `main` non si tocca direttamente: branch + PR con review (vedi [TODO.md](TODO.md#8-regole-di-lavoro-e-definition-of-done)).
