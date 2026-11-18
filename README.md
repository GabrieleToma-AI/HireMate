# 📋 HIREMATE — Backend GenAI

Simulatore di colloqui HR per studenti ITS ICT Piemonte. Il backend gestisce la profilazione, le domande, la valutazione delle risposte e il report finale gamificato.

- **Lingua:** italiano.
- **Target:** studenti junior IT (tono professionale, diretto, non "coccoloso").
- **Team:** 3 AI engineer (Python) + 3 AR/VR & game (frontend).
- **Stack:** Python 3.14, FastAPI, Pydantic, Supabase (in arrivo), Gemini `gemini-3.5-flash-lite`, Azure TTS (Collega 2).

---

## 🏗️ Struttura

| File | Cosa fa |
|---|---|
| `main.py` | Crea FastAPI, CORS, include i router. |
| `corsi.py` | 14 corsi ITS con materie e focus HR; `get_dettagli_corso()`. |
| `profilo.py` | Le 3 liste della profilazione + `METRICA_PER_PAURA` + soglia 7.5. |
| `agenti/llm.py` | Wrapper LLM: FreeLLMAPI → Gemini Lite, timeout, 2 retry, JSON robusto. |
| `agenti/interviewer.py` | Genera la domanda (prima o successiva, con `cronologia`). |
| `agenti/evaluator.py` | Valuta la trascrizione: chiarezza, STAR, esempi, suggerimento, better answer. |
| `agenti/reporter.py` | Report finale: overall, stats, paura superata, prossime paure, badges. |
| `agenti/cv_parser.py` | Estrae testo dal PDF e lo trasforma in JSON. |
| `routers/sessions.py` | Modelli Pydantic e endpoint `/start`, `/end`; contratti `/turn`. |
| `routers/cv.py` | Endpoint `/api/cv/parse` (PDF → JSON). |
| `test_*.py` | Test di sistema e integrazione. |
| `processi_spiegati/` | Spiegazioni didattiche e recap. |

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

La validazione è **stretta**: un valore fuori lista restituisce `422`.

---

## 🎯 Regola "paura superata"

| Paura | Metrica |
|---|---|
| Restare senza parole | `chiarezza` |
| Non sembrare abbastanza preparato tecnicamente | `esempi_concreti` |
| Fare una figuraccia con il recruiter | `struttura_star` |
| Non saper parlare di me stesso | `chiarezza` |

- La paura è superata quando **la metrica specifica** arriva a **7.5/10** (non l'overall).
- **Sticky:** una volta superata per la stessa paura, resta superata.
- Se la paura cambia, il flag riparte da `false`.
- `prossime_paure` contiene le altre 3 paure della Domanda 2.

---

## 🔌 API

### `POST /api/cv/parse`
Multipart con `file` PDF (max 5 MB) → `{"cv_json": {"competenze": [...], "progetti": [...]}}`.

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

### `POST /api/session/turn` (da implementare, Collega 2)
Contratto pronto in `routers/sessions.py`: `TurnRequest` (`corso`, `profilo_soft_skill`, `cv_json`, `domanda`, `trascrizione`, `cronologia`) → `TurnResponse` (`turnId`, `valutazione`, `prossimaDomanda`, `colloquio_terminato`, `audioUrl`, `visemes`, `gesture`).
Dopo `DOMANDE_PER_COLLOQUIO = 6` domande, `colloquio_terminato = true`.

### `POST /api/session/end`
```json
{
  "corso": "Cyber Security Specialist",
  "profilo_soft_skill": { "...": "..." },
  "valutazioni": [{"chiarezza": 8, "struttura_star": 7, "esempi_concreti": 9}],
  "report_precedente": null
}
```
Risposta: `overall_previous/current`, `stats_previous/current`, `paura_attuale`, `metrica_paura`, `paura_superata`, `prossime_paure`, `badges`, `improvements`, `final_tip`.

> `report_precedente` è **temporaneo**: la fonte di verità sarà Supabase. `/end` non deve fidarsi del client appena il DB sarà pronto.

---

## ⚙️ Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # inserisci le chiavi
python main.py           # http://127.0.0.1:8000/docs
```

`.env` (non committare): `FREELLMAPI_*`, `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.5-flash-lite`, `CORS_ALLOW_ORIGINS`, `LLM_TIMEOUT_SECONDS`.

### Test
```bash
python test_reporter.py      # offline, regola paura
python test_sistema.py       # Gemini + evaluator
python test_interviewer.py
python test_int_eval.py
python test_api_full.py      # richiede il server attivo su :8000
```

---

## 👥 Divisione del lavoro

- **GenAI core (tu):** `agenti/`, `corsi.py`, `profilo.py`, `main.py`, `routers/`, test.
- **Collega 1:** Supabase (`users`, `sessions`, `turns`, `fears_history`), auth nickname+PIN (hash bcrypt), `PATCH /api/users/update-fear`, rifinitura `cv_parser.py`.
- **Collega 2:** endpoint `/turn`, Azure TTS + visemi, salvataggio valutazioni.
- **Team AR/VR:** UI game-style, avatar, modale "Promozione Paura", report animato.

---

## 🔐 Sicurezza

- `.env` è in `.gitignore` e non è mai stato committato.
- Le chiavi non vanno mai stampate, incollate o committate.
- PIN: solo hash bcrypt, mai in chiaro.
- Il progetto è in OneDrive: attenzione alla condivisione della cartella.
