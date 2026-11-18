# HireMate — Piano di lavoro e decisioni

**Data:** 18/11/2026 — aggiornato la sera
**Stato:** implementazione fatta (punti 1-8). Nessun commit: le modifiche sono nel working tree.
**Come riprendere:** leggi il recap `recap_18_11_2.md` (canonico) e la sezione 11 per le decisioni finali.

> **Nota:** le sezioni 5.x e 6 descrivono la prima proposta (paura con overall 75). La regola definitiva è nella **sezione 11**: metrica specifica >= 7.5.

---

## Decisioni del 18/11 (pomeriggio/sera)

- **Soglia:** 75/100 (non 70).
- **Sticky:** una volta superata, la paura resta superata per la stessa paura.
- **Nomi in italiano:** `paura_superata` (al posto di `fear_overcome`), `paura_attuale`, `prossime_paure`, `PAURE_DISPONIBILI`, `SOGLIA_PAURA_SUPERATA`.
- **Lista paure:** fornita dall'utente (le 4 opzioni della Domanda 2). Vedi sezione 5.7.
- **Prossime paure:** le altre 3 opzioni della Domanda 2, esclusa quella superata.
- **Nome campo:** `prossime_paure` (confermato).
- **Numero minimo di sessioni:** no, basta la soglia 75 (confermato).
- **Implementazione:** fatta stasera; vedi `recap_18_11_2.md`.

---

## 0. Richieste ricevute (riassunto)

1. Analizzare il progetto e trovare **3 possibili errori**.
2. Non modificare nulla durante l'analisi.
3. Correggere successivamente **tutti** gli errori trovati.
4. Tenere presente che il progetto è stato scritto da **Gemini 3.5 Flash Lite a basso effort**: aspettarsi incoerenze tra documentazione e codice.
5. Il progetto è **scolastico**: deve restare semplice, corto, completo, funzionante e facilmente spiegabile al professore.
6. Sarà disponibile **in locale per 6 persone** (3 AI engineer + 3 AR/VR e game) e servirà come prova delle competenze tecniche per futuri colloqui.
7. Definire **come lavorare** e come strutturare l'output: cosa ho fatto, come è modificato, come spiegarlo al professore.
8. Ogni tot messaggi: un **recap** e un file `.md` da aggiungere in `processi_spiegati/`.
9. Analizzare la cartella dei documenti esplicativi: cosa è fatto, cosa è da fare, come è diviso il lavoro.
10. Dettagliare il **"punto 3"** (`fear_overcome`, oggi `paura_superata`) prima di implementarlo.
11. Non implementare nulla ora: creare questo file di ripresa.

---

## 1. Contesto

- **Progetto:** HireMate, simulatore di colloqui HR con agenti AI (Interviewer → Evaluator → Reporter).
- **Cartella:** `C:\Users\gabri\OneDrive\Desktop\HireMate` (Windows, venv locale, Python 3.14.8).
- **Documenti di riferimento:**
  - `README.md` — architettura, flusso, divisione del lavoro.
  - `processi_spiegati/funzionamento.md` — spiegazione didattica dei file.
  - `processi_spiegati/recap_18_11.md` — stato del progetto e roadmap (non tracciato da git).
  - `input_registrazione.txt` — esempio di profilo soft skill.

### Divisione del lavoro (dai documenti)

| Stream | Persona | Responsabilità | File / aree |
|---|---|---|---|
| 1 | GenAI core (tu) | Interviewer, Evaluator, Reporter, wrapper LLM | `agenti/`, `corsi.py`, `main.py` |
| 2 | Collega 1 | Data & CV | `database/supabase_client.py`, `agenti/cv_parser.py`, `PATCH /api/users/update-fear` |
| 3 | Collega 2 | API & audio | `routers/`, `agenti/tts.py`, endpoint `/turn` |
| 4-6 | Team AR/VR & game | UI, avatar, report animato | frontend |

---

## 2. Accordo di lavoro (concordato il 18/11)

### 2.1 Lingua e registro
Italiano **semplice e didattico**: frasi corte, niente gergo inutile; ogni concetto tecnico spiegato con "cos'è, perché serve, cosa succede senza".

### 2.2 Workflow quando viene chiesta una modifica
1. Leggere i file coinvolti e il contratto API.
2. Applicare la modifica **minima e spiegabile**.
3. Eseguire test offline (import, validazione, funzioni con mock) e, solo se serve, test end-to-end.
4. **Non committare**: le modifiche restano nel working tree.
5. Consegnare il riepilogo nell'ordine: *cosa ho cambiato → perché → come verificarlo → come spiegarlo al prof → impatto sui colleghi*.

### 2.3 Perimetro
**Si può toccare (GenAI core):**
`main.py`, `agenti/`, `corsi.py`, `profilo.py` (nuovo, se confermato), `routers/sessions.py`, `test_*.py`, `requirements.txt`, `.env.example`, `processi_spiegati/*.md`.

**Non si tocca:**
`venv/`, `.env` (la chiave si legge solo tramite l'app), `database/`, `agenti/tts.py`, `agenti/cv_parser.py`, frontend AR/VR.
Per queste aree si **segnala** cosa manca, senza scrivere codice.

### 2.4 Recap `.md`
Nome: `processi_spiegati/recap_<GG_MM>.md`.
Attenzione: esiste già `recap_18_11.md` (roadmap del progetto). Per non sovrascriverlo, i nuovi recap dello stesso giorno useranno un suffisso, es. `recap_18_11_2.md`.
Struttura:
1. **Cosa ho fatto** — changelog file per file, con prima/dopo.
2. **Come funziona** — flusso toccato, spiegato semplice.
3. **Come spiegarlo al prof** — 3-5 punti + concetto chiave.
4. **Domande possibili** — domande probabili e risposte brevi.
5. **Test eseguiti** — comandi e risultati.
6. **TODO / prossimi passi** — con la divisione tra colleghi e team AR/VR.

### 2.5 Test e chiavi
- È autorizzato l'uso della **chiave Gemini del `.env`** (free plan) **solo per i test**.
- La chiave **non va mai stampata** né incollata in chat o in file.
- In caso di `503`/quota: **aspettare qualche minuto e riprovare**; se persiste, passare ai test offline.
- FreeLLMAPI è opzionale (se non è attivo, il fallback su Gemini è già previsto).

---

## 3. Analisi dei documenti esistenti

### 3.1 Cosa contengono

- **`funzionamento.md`** — spiega i file uno per uno (main, corsi, llm, interviewer, evaluator, sessions, .env/.gitignore) con i concetti da esame: separation of concerns, context stuffing, fallback, validazione Pydantic, sicurezza delle chiavi. Non cita `reporter.py` né `/end`.
- **`recap_18_11.md`** — stato e roadmap: dichiara reporter completo con `fear_overcome` e fallback a 3 modelli, endpoint `/start` e `/end`; prossimi passi per Collega 1 (Supabase, cv_parser, update-fear), Collega 2 (`/turn`, Azure TTS + visemi), team AR/VR (UI, avatar, report animato).
- **`README.md`** — architettura e flusso + divisione in 3 stream e regole d'oro (branch, file separati, contratto API). Manca una sezione "come si avvia il progetto".
- **`input_registrazione.txt`** — esempio di profilo soft skill con `ansia_principale`, `stile_gestione_problemi`, `timore_critico`.

### 3.2 Stato reale vs dichiarato

| Area | Dichiarato nei documenti | Realtà nel codice |
|---|---|---|
| Interviewer | fatto | fatto (`agenti/interviewer.py`) |
| Evaluator | fatto | fatto, ma **non chiamato da nessun endpoint** |
| Reporter | fatto + `fear_overcome` | fatto, **senza `fear_overcome`** (oggi `paura_superata`) |
| `/api/session/start` | fatto | fatto |
| `/api/session/end` | fatto | fatto |
| `/api/session/turn` | da fare (Collega 2) | assente |
| Azure TTS + visemi | da fare | assente |
| Supabase (tabelle e client) | da fare | assente |
| CV parser | da fare | assente |
| `PATCH /api/users/update-fear` | da fare | assente |
| Frontend AR/VR | da fare | assente |
| Modello Gemini | Flash → Lite nel recap | **deciso: solo `gemini-3.5-flash-lite`** |

### 3.3 Incoerenze nei documenti

- `README.md` cita `routers/session.py` (singolare); il file reale è `routers/sessions.py`.
- `README.md` mette `/turn` tra i lavori di Collega 2; `recap_18_11.md` dice che `/start` e `/end` sono fatti e `/turn` è il prossimo passo: coerente, ma il README non è aggiornato.
- `funzionamento.md` descrive solo `/start` e non cita `reporter.py`.
- `recap_18_11.md` dice "completamente funzionante e testato", ma i test hanno firme vecchie e non girano.
- `README.md` dice di non lavorare su `main`, ma la history mostra commit diretti su `main`.
- `requirements.txt` non riproduce il `venv` (manca `google-genai`).
- Il recap è **non tracciato** da git: se il PC si rompe, si perde.

---

## 4. Errori trovati

### 4.1 [ALTA] `requirements.txt` non è riproducibile: il server non parte da un'installazione pulita

**Evidenza**
- `agenti/llm.py:7` usa `from google import genai`, poi `genai.Client` (`:26`) e `client.aio.models.generate_content` (`:61`): è il **nuovo SDK `google-genai`**.
- `requirements.txt:12-18` elenca `google-generativeai==0.8.6` (SDK legacy, espone `google.generativeai`) e **non** elenca `google-genai`.
- Nel `venv` c'è `google_genai-3.4.0.dist-info`, ma **non** esiste `venv/Lib/site-packages/google/generativeai`: l'ambiente è stato aggiustato a mano e non corrisponde al file.
- `requirements.txt` è salvato in **UTF-16 LE con BOM** (`FF FE`).

**Impatto**
Su un'altra macchina (o dopo `pip install -r requirements.txt` in un venv nuovo) l'import di `main.py` fallisce con `ImportError: cannot import name 'genai' from 'google'`: il backend non si avvia.

**Fix applicato**
Riscrivere `requirements.txt` in **UTF-8**, con le dipendenze dirette e le versioni del venv:
`fastapi==0.163.1`, `uvicorn==0.54.0`, `pydantic==2.14.3`, `python-dotenv==1.2.4`, `openai==3.52.0`, `google-genai==3.4.0`, `httpx==0.28.1`.
Rimuovere `google-generativeai` (non usato). Valutare se tenere `supabase` (previsto per Collega 1).

**Verifica**
Creare un venv pulito, `pip install -r requirements.txt`, `python -c "from google import genai"`, poi avviare `main.py`.

**Come spiegarlo al prof**
"Le dipendenze sono la lista della spesa del progetto: se manca un pacchetto, il programma non parte. Il codice usava il pacchetto nuovo di Google, ma la lista conteneva quello vecchio. Inoltre il file era salvato in un formato di testo strano (UTF-16), poco leggibile dagli strumenti."

---

### 4.2 [ALTA] I test chiamano gli agenti con parametri che non esistono più

**Evidenza**
- Firme attuali: `genera_domanda(corso, profilo_soft_skill, cv_json=None)` (`agenti/interviewer.py:5-9`) e `valuta_risposta(corso, profilo_soft_skill, domanda, trascrizione, cv_json=None)` (`agenti/evaluator.py:4-10`).
- `test_interviewer.py:8-11` e `:16-20` passano `soft_skill=`.
- `test_sistema.py:45-50` passa `soft_skill=`.
- `test_int_eval.py:28-34` e `:51-59` passano `paura_colloquio=`, `reazione_problema=`, `paura_fallimento=`.

**Impatto**
`TypeError: ... got an unexpected keyword argument 'soft_skill'` prima di qualsiasi chiamata all'LLM: nessun test può passare. In più `test_sistema.py` cattura l'eccezione e stampa "FALLITO" **senza exit code diverso da zero**: una CI risulterebbe verde anche con i test rotti.

**Fix applicato**
Aggiornare i test al nuovo contratto: passare un dizionario `profilo_soft_skill` con `ansia_principale`, `stile_gestione_problemi`, `timore_critico`.
Aggiungere un contatore di fallimenti e `sys.exit(1)` se qualcosa fallisce.
Rinominare le funzioni async `test_*` in `run_*` (o aggiungere `pytest-asyncio`) per evitare problemi di collezione con pytest.
Aggiornare `test_api_full.py` per verificare anche i nuovi campi del report.

**Verifica**
Eseguire `python test_sistema.py` e `python test_interviewer.py`: devono partire, chiamare l'LLM (chiave Gemini free) e uscire con codice 0 solo se tutto passa.

**Come spiegarlo al prof**
"I test sono script che chiamano le funzioni del progetto. Dopo il refactoring del profilo soft skill, i test erano rimasti ai vecchi nomi dei parametri: fallivano subito e non verificavano più niente. Allineare i test al nuovo contratto è parte del refactoring."

---

### 4.3 [MEDIA] Il report non restituisce lo stato della paura (feature dichiarata ma assente)

**Evidenza**
- `recap_18_11.md:17` dichiara `fear_overcome` (oggi rinominato `paura_superata`): "se l'utente ha superato la sua paura" e "prepara le opzioni per la prossima paura".
- `recap_18_11.md:69`: la modale frontend si apre quando `fear_overcome` è `true`.
- `agenti/reporter.py:77-89` restituisce solo `overall_previous`, `overall_current`, `stats_previous`, `stats_current`, `badges`, `improvements`, `final_tip`.
- Nessuna occorrenza di `fear_overcome` (né di `paura_superata`) nei file `.py`.

**Impatto**
La modale di "Promozione Paura" non si attiverà mai; il frontend riceve `undefined` e il contratto con il team AR/VR è incompleto.

**Fix applicato**
Dettaglio completo nella sezione 5.

**Come spiegarlo al prof**
"La paura è un dato del profilo. A fine colloquio calcoliamo un punteggio 0-100; se supera la soglia di 75, consideriamo la paura superata e proponiamo tre paure nuove. Il frontend mostra la modale e, se l'utente accetta, aggiorna il profilo: è profilazione dinamica."

---

### 4.4 Sospetti secondari (da valutare insieme ai 3 principali)

| # | Problema | Evidenza | Fix proposto |
|---|---|---|---|
| 1 | Manca CORS: un frontend su un'altra origine viene bloccato dal browser | `main.py:6-12` | `CORSMiddleware` con origini configurabili (es. `localhost:5173`) |
| 2 | Fallback Gemini Flash → Flash-Lite | `agenti/llm.py:31-33`; `README.md:23`; `recap_18_11.md:25-27` | **Deciso: solo `gemini-3.5-flash-lite`**; resta il fallback FreeLLMAPI → Gemini |
| 3 | Corso non valido restituisce `503` invece di `400/422` | `agenti/interviewer.py:15-18` + `routers/sessions.py:62-63` | Eccezione `CorsoNonValidoError(ValueError)` e mappatura corretta |
| 4 | `/end` si fida delle `valutazioni` del client, senza range né lunghezza minima | `routers/sessions.py:29-33` | Modello Pydantic `Valutazione` con 3 voti 0-10 e `min_length=1` |
| 5 | Gli errori generici restituiscono `str(e)` al client | `routers/sessions.py:64-65`, `:84-85` | Log interno + messaggio generico |
| 6 | `turnId` fisso `"mock-turn-001"` | `routers/sessions.py:55` | `uuid4().hex` |
| 7 | `visemes: list = []` come default mutabile | `routers/sessions.py:26` | `Field(default_factory=list)` |
| 8 | Import inutilizzati e commento duplicato | `agenti/reporter.py:1`, `:22-23`; `agenti/evaluator.py:2` | Pulizia |
| 9 | Punteggi mancanti contati come 0 nelle medie | `agenti/reporter.py:15-17` | Validazione o clamp esplicito |
| 10 | JSON dell'LLM non ripulito da eventuali code fence | `agenti/llm.py:52`, `:70` | Helper `_estrai_json` |
| 11 | `LLMError` rilanciato senza `from e` | `agenti/llm.py:54`, `:72` | `raise LLMError(...) from e` |
| 12 | Nessun timeout sulle chiamate Gemini (FreeLLMAPI ha 5s) | `agenti/llm.py:61` | Timeout configurabile |
| 13 | `/turn` assente: l'Evaluator non è raggiungibile e i voti sono falsificabili | `routers/sessions.py` | **Rinviato**: è lavoro assegnato a Collega 2 nel recap |

> Nota: il punto 13 non è un bug da correggere ora, è una feature pianificata. Va segnalato a Collega 2.

---

## 5. Punto 3 in dettaglio: `paura_superata` e `prossime_paure`

### 5.1 Le quattro cose da non confondere

| Nome | Cosa è | Dove vive |
|---|---|---|
| `PAURE_DISPONIBILI` | Le 4 paure selezionabili in registrazione (Domanda 2) | `profilo.py` (nuovo, come `corsi.py`) |
| `paura_superata` | Booleano: `true` se lo studente ha superato la paura attuale | Risposta di `/end` |
| `prossime_paure` | Fino a 3 paure alternative da proporre per la sessione successiva | Risposta di `/end` |
| `paura_attuale` | Testo della paura a cui si riferisce il flag (serve per la sticky) | Risposta di `/end` |

> Nota: le chiavi già esistenti del report (`overall_previous`, `overall_current`, `stats_previous`, `stats_current`, `badges`, `improvements`, `final_tip`) restano in inglese per non rompere il contratto col frontend. I nuovi campi sono in italiano.

- `paura_superata` è il nuovo nome di `fear_overcome` (il recap storico usa ancora il nome inglese). Sblocca la modale "Promozione Paura".
- `prossime_paure` sono **le altre 3 paure** della Domanda 2 (la lista ne ha 4): si esclude solo quella superata. La scelta viene salvata con `PATCH /api/users/update-fear` (Collega 1) e diventa la nuova `ansia_principale`.
- `PAURE_DISPONIBILI` deve essere **la stessa lista dell'onboarding**: se il frontend ha testi diversi, le card mostrerebbero paure sconosciute. Va comunicata a Collega 1 e al team AR/VR.
- Il campo `fear_overcome` del recap e del contratto frontend va aggiornato in `paura_superata`.
- Il team frontend chiamava il campo `next_fear_options`: il campo definitivo è `prossime_paure` (confermato). Il frontend dovrà usare questo nome.

### 5.2 Regola decisa

- **Soglia:** 75/100 (l'`overall` è la media pesata × 10, quindi 75 = 7.5/10).
- **Sticky:** una volta superata, la paura resta superata **per la stessa paura**, anche se in una sessione successiva il punteggio scende.
- **Reset:** il flag torna `false` solo se cambia la paura (`ansia_principale`), perché la nuova paura non è ancora stata affrontata.
- **Opzioni:** `prossime_paure` vengono restituite solo quando `paura_superata` è `true`; sono le altre 3 paure della Domanda 2.
- **Esclusione:** si esclude solo la paura attuale (`ansia_principale`). Il `timore_critico` non c'entra: è un'altra domanda.
- **Persistenza:** per ora la sticky viaggia dentro `report_precedente` (il client lo rimanda a ogni sessione). La persistenza vera richiede il database di Collega 1.
- **Numero minimo di sessioni:** non previsto dalla regola attuale: con 75 alla prima sessione la paura risulterebbe già superata. Se "servono molte sessioni" va imposto un minimo (es. 3), serve un contatore nel report o nel DB.

### 5.3 Codice applicato

**File `profilo.py` (creato)** (stesso stile di `corsi.py`):

```python
# Domanda 2 — "Cosa ti spaventa di più all'idea di fare un colloquio?"
PAURE_DISPONIBILI = [
    "Restare senza parole",
    "Non sembrare abbastanza preparato tecnicamente",
    "Fare una figuraccia con il recruiter",
    "Non saper parlare di me stesso",
]

# Domanda 3 — "Quando ti trovi di fronte a un problema difficile, come reagisci?"
STILI_GESTIONE_PROBLEMI = [
    "Mi blocco e mi faccio prendere dal panico",
    "Chiedo subito aiuto a un collega o a un tutor",
    "Faccio ricerche infinite finché non trovo la soluzione",
    "Mi prendo una pausa e ci riprovo con calma",
]

# Domanda 4 — "Se il colloquio andasse male, quale pensi sarebbe il motivo principale?"
TIMORI_CRITICI = [
    "Non ho saputo spiegare bene le mie competenze",
    "Ero troppo in ansia e non riuscivo a concentrarmi",
    "Non ho abbastanza esperienza tecnica per il ruolo",
    "Non mi sono preparato abbastanza sull'azienda",
]
```

**In `agenti/reporter.py`:**

```python
from profilo import PAURE_DISPONIBILI

SOGLIA_PAURA_SUPERATA = 75.0
```

Dopo il calcolo di `overall_attuale`:

```python
# Sticky: true se era già true per la stessa paura
paura_superata_precedente = bool(
    report_precedente
    and report_precedente.get("paura_superata") is True
    and report_precedente.get("paura_attuale") == ansia
)

paura_superata = (
    paura_superata_precedente
    or overall_attuale >= SOGLIA_PAURA_SUPERATA
)

prossime_paure = (
    [p for p in PAURE_DISPONIBILI if p != ansia][:3]
    if paura_superata else []
)
```

Nel dizionario di ritorno:

```python
"paura_attuale": ansia,
"paura_superata": paura_superata,
"prossime_paure": prossime_paure,
```

### 5.4 Contratto JSON (esempio)

```json
{
  "overall_previous": 58.0,
  "overall_current": 76.0,
  "stats_current": { "chiarezza": 7.5, "struttura_star": 7.0, "esempi_concreti": 8.0 },
  "paura_attuale": "Restare senza parole",
  "paura_superata": true,
  "prossime_paure": [
    "Non sembrare abbastanza preparato tecnicamente",
    "Fare una figuraccia con il recruiter",
    "Non saper parlare di me stesso"
  ],
  "badges": ["..."],
  "improvements": ["..."],
  "final_tip": "..."
}
```

### 5.5 Perché serve `paura_attuale`

Senza, dopo che l'utente cambia paura, la sticky resterebbe `true` e la nuova paura risulterebbe già superata. Con `paura_attuale` il confronto è esplicito: il flag vale solo per la paura a cui si riferisce.
Il dato viaggia nel report: il client lo rimanda in `report_precedente` alla sessione successiva. Non serve il database per questa regola.

### 5.6 Test previsti

- Soglia: `overall = 74.9` → `false`; `overall = 75.0` → `true`.
- Sticky: `report_precedente = {"paura_superata": true, "paura_attuale": "X"}`, `ansia = "X"`, `overall = 50` → `true`.
- Reset: stesso report ma `ansia = "Y"` → `false` (se `overall < 75`).
- `test_api_full.py`: verifica che `paura_superata` sia booleano e che, se `true`, `prossime_paure` abbia esattamente 3 elementi (le altre 3 della Domanda 2) e non contenga la paura attuale.
- Test deterministici con mock di `chiama_llm_json`: nessun consumo di quota.

### 5.7 Dati ufficiali della profilazione (forniti il 18/11, sera)

La lista non era presente nel progetto; è stata fornita dall'utente. Le tre domande di registrazione e le relative variabili sono queste.

**Domanda 2 — Ansia** (`ansia_principale`): "Cosa ti spaventa di più all'idea di fare un colloquio?"

```python
PAURE_DISPONIBILI = [
    "Restare senza parole",
    "Non sembrare abbastanza preparato tecnicamente",
    "Fare una figuraccia con il recruiter",
    "Non saper parlare di me stesso",
]
```

**Domanda 3 — Reazione ai problemi** (`stile_gestione_problemi`): "Quando ti trovi di fronte a un problema difficile, come reagisci?"

```python
STILI_GESTIONE_PROBLEMI = [
    "Mi blocco e mi faccio prendere dal panico",
    "Chiedo subito aiuto a un collega o a un tutor",
    "Faccio ricerche infinite finché non trovo la soluzione",
    "Mi prendo una pausa e ci riprovo con calma",
]
```

**Domanda 4 — Timore di fallimento** (`timore_critico`): "Se il colloquio andasse male, quale pensi sarebbe il motivo principale?"

```python
TIMORI_CRITICI = [
    "Non ho saputo spiegare bene le mie competenze",
    "Ero troppo in ansia e non riuscivo a concentrarmi",
    "Non ho abbastanza esperienza tecnica per il ruolo",
    "Non mi sono preparato abbastanza sull'azienda",
]
```

**Nota per `prossime_paure`:** la Domanda 2 ha esattamente 4 opzioni, quindi escludendo quella superata restano sempre 3 card. Le altre due liste servono per validare il profilo e per documentare il frontend; il reporter usa solo `PAURE_DISPONIBILI`.

**Dove metterle:** nuovo `profilo.py` nella root, come `corsi.py` (knowledge base statica). In alternativa, se preferisci un file per dominio, `paure.py` solo per le paure e le altre liste dove serve.

### 5.8 Come spiegarlo al prof

"La paura è un dato del profilo soft skill. A fine colloquio il backend calcola un punteggio oggettivo 0-100 come media pesata delle tre metriche. Se arriva a 75 (7.5/10), la paura è superata: il report lo segnala con `paura_superata: true` e propone le altre tre paure della Domanda 2. Una volta superata, la paura resta superata per quella stessa paura, anche se in una sessione successiva il punteggio scende: è una scelta di gamification, per non far perdere i progressi. Il frontend mostra la modale e, se l'utente accetta, aggiorna il profilo tramite l'endpoint del Collega 1. È profilazione dinamica: il colloquio successivo viene calibrato sulla nuova paura."

### 5.9 Stato delle decisioni

- [x] Soglia: 75/100.
- [x] Sticky: resta superata per la stessa paura.
- [x] Nomi in italiano: `paura_superata`, `paura_attuale`, `prossime_paure`, `PAURE_DISPONIBILI`, `SOGLIA_PAURA_SUPERATA`.
- [x] Liste ufficiali delle 3 domande di profilazione (sezione 5.7).
- [x] Implementazione: fatta (vedi `recap_18_11_2.md`).

---

## 6. Piano di lavoro ordinato

| # | Intervento | File | Criterio di accettazione | Stato |
|---|---|---|---|---|
| 1 | Dipendenze riproducibili | `requirements.txt` | `pip install -r` in venv pulito + import `main` OK | fatto |
| 2 | Test allineati al contratto | `test_*.py` | Nessun `TypeError`; exit code 1 se un test fallisce | fatto |
| 3 | `paura_superata` + `prossime_paure` | `profilo.py`, `agenti/reporter.py`, `test_api_full.py` | Campi presenti; test 74.9/75 e sticky; 3 opzioni esatte | fatto |
| 4 | CORS | `main.py` | Preflight `OPTIONS` 200 dall'origine del frontend | fatto |
| 5 | Modello Gemini unico | `agenti/llm.py`, `.env.example` | `GEMINI_MODEL=gemini-3.5-flash-lite` | fatto |
| 6 | Errori HTTP e validazione | `corsi.py`, `agenti/interviewer.py`, `routers/sessions.py` | Corso invalido → 400/422; valutazioni fuori range → 422 | fatto |
| 7 | Pulizie e robustezza | `agenti/llm.py`, `agenti/reporter.py`, `agenti/evaluator.py`, `routers/sessions.py` | Import puliti, `turnId` unico, default non mutabili, JSON robusto | fatto |
| 8 | Primo recap di lavoro | `processi_spiegati/recap_18_11_2.md` | Scheda esame + changelog + test | fatto |

**Ordine consigliato:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.
Motivo: prima si rende il progetto installabile e verificabile, poi si aggiunge la feature, poi si rifinisce.

---

## 7. Da decidere al rientro

- [x] **Soglia paura**: 75/100 (deciso).
- [x] **Nomi**: `paura_superata`, `paura_attuale`, `prossime_paure`, `PAURE_DISPONIBILI` (deciso).
- [x] **Sticky**: resta superata per la stessa paura (deciso).
- [x] **Lista paure**: fornita (4 opzioni Domanda 2, sezione 5.7).
- [x] **Nome campo**: `prossime_paure` (confermato).
- [x] **Numero minimo di sessioni**: no, solo soglia 75 (confermato).
- [x] **Ambito**: corretti i 3 errori principali e i secondari 1-12 (tranne `/turn`).
- [x] **Nome recap**: `recap_18_11_2.md` creato.
- [ ] **Chiavi esistenti**: le chiavi già in inglese restano così (consigliato sì); da confermare solo se vuoi tradurle.
- [ ] **`/turn`**: resta a Collega 2 (consigliato).
- [ ] **Documenti**: aggiornare `README.md` e `funzionamento.md`? (da fare)
- [ ] **Chiavi**: ruotare? (solo se il `.env` è stato condiviso o sincronizzato fuori dal PC).

---

## 8. Sicurezza e privacy

- `.env` è in `.gitignore`, **non è tracciato** e **non compare nella history** di git (verificato con `git ls-files` e `git log --all -- .env`).
- Le chiavi **non vanno mai stampate** in chat, in file `.md`, in commit o in screenshot.
- La chiave Gemini free è autorizzata **solo per i test**, caricata dall'app tramite `python-dotenv`; in caso di `503` aspettare e riprovare.
- Il progetto è dentro **OneDrive**: la cartella viene sincronizzata nel cloud. Non condividerla con persone non fidate.
- **Nessun commit** verrà fatto senza richiesta esplicita.
- Il file `.env` **non è stato modificato**; i valori non sono mai stati riportati per intero.

---

## 9. Stato del repository (18/11/2026, sera)

- `git status`: 13 file modificati e 5 non tracciati (`profilo.py`, `test_reporter.py`, `recap_18_11_2.md`, `piano_lavoro_18_11.md`, `recap_18_11.md`).
- `git diff`: modifiche a `.env.example`, `agenti/`, `corsi.py`, `main.py`, `requirements.txt`, `routers/sessions.py`, `test_*.py`.
- Nessun commit; `.env` e `venv/` non toccati.
- `requirements.txt` è ora UTF-8 (senza BOM).
- Test eseguiti: `test_reporter.py`, `test_sistema.py`, `test_interviewer.py`, `test_int_eval.py`, `test_api_full.py`, più un controllo API offline con TestClient. Tutti verdi.

---

## 10. Concetti da esame collegati

| Concetto | Dove si vede | Come spiegarlo in una frase |
|---|---|---|
| Gestione delle dipendenze | `requirements.txt` | La lista dei pacchetti deve descrivere esattamente ciò che serve per avviare il progetto. |
| Contratto API | `routers/sessions.py`, `agenti/reporter.py` | Frontend e backend si scambiano JSON con campi concordati; se cambia un campo, cambiano entrambi. |
| Refactoring e test | `test_*.py` | Quando cambia la firma di una funzione, i test vanno aggiornati, altrimenti non verificano più nulla. |
| Validazione dei dati | Pydantic (`BaseModel`) | I dati in ingresso vengono controllati prima di chiamare l'LLM: si risparmiano tempo e soldi. |
| Resilienza / fallback | `agenti/llm.py` | Se un provider non risponde, si prova il successivo; il servizio resta disponibile. |
| Separation of concerns | struttura dei file | Ogni file fa una cosa: `llm.py` chiama l'AI, `interviewer.py` decide le domande, `corsi.py` sa i corsi. |
| Profilazione dinamica / gamification | `paura_superata`, `stats_previous` | Il colloquio si adatta alla persona e il report mostra i progressi tra sessioni. |
| Sicurezza delle chiavi | `.env`, `.gitignore` | Le chiavi stanno fuori dal codice e fuori da git. |

### Domande probabili del prof
1. Perché il progetto non partiva su un altro PC? → dipendenza mancante e file in UTF-16.
2. Perché i test non giravano? → firme cambiate nel refactoring.
3. Come decidi se una paura è superata? → soglia 75/100 + sticky sulla stessa paura, regola Python deterministica.
4. Perché non usi l'LLM per decidere? → non sarebbe ripetibile né testabile.
5. Cosa succede se Gemini non risponde? → fallback e timeout; il client riceve un errore chiaro.
6. Perché usare Pydantic? → valida i dati prima di consumare quota.
7. Perché `paura_attuale`? → senza, dopo un cambio paura la sticky farebbe risultare già superata anche la nuova.

---

## 11. Decisioni finali (sera, dopo il questionario)

### Paura: metrica specifica, non overall
| Paura (Domanda 2) | Metrica | Soglia |
|---|---|---|
| Restare senza parole | `chiarezza` | 7.5/10 |
| Non sembrare abbastanza preparato tecnicamente | `esempi_concreti` | 7.5/10 |
| Fare una figuraccia con il recruiter | `struttura_star` | 7.5/10 |
| Non saper parlare di me stesso | `chiarezza` | 7.5/10 |

- `paura_superata` = la metrica specifica >= 7.5, oppure sticky se era già true per la stessa paura.
- `metrica_paura` dice quale metrica ha fatto scattare la promozione.
- `prossime_paure` = le altre 3 paure della Domanda 2.
- Nomi solo italiani: `paura_superata`, `paura_attuale`, `metrica_paura`, `prossime_paure`.

### `/turn` e cronologia
- `genera_domanda(..., cronologia=[...])` accetta la storia e non ripete le domande; temperatura 0.8.
- In `routers/sessions.py` ci sono `Turno`, `TurnRequest`, `TurnResponse`.
- L'endpoint `POST /api/session/turn` è di **Collega 2**; userà i modelli pronti, l'Evaluator, il TTS e imposterà `colloquio_terminato`.
- `DOMANDE_PER_COLLOQUIO = 6` è indicativo: si chiude quando ci sono abbastanza informazioni, senza rifiuti bruschi a tempo.

### CV
- `POST /api/cv/parse` riceve un PDF (max 5 MB) e restituisce `cv_json`.
- `agenti/cv_parser.py` usa `pypdf` + LLM; dipendenze aggiunte a `requirements.txt`.

### Validazione
- Le 3 risposte della profilazione sono validate **strettamente** contro `profilo.py` (422 se fuori lista).
- Corso validato (422); valutazioni 0-10 e lista non vuota; `turnId` univoco.

### Stato sessione e auth
- Fonte di verità: **Supabase** (Collega 1), appena pronto.
- Oggi `report_precedente` è solo un trasporto temporaneo dal client; non è uno store server-side.
- Auth nickname+PIN: **Collega 1**, PIN hash bcrypt, mai in chiaro.

### LLM
- Solo `gemini-3.5-flash-lite`; fallback FreeLLMAPI → Gemini.
- 2 retry con backoff su 503/429/quota.

### Ambiente e git
- Python **3.14** (venv attuale); dipendenze dei colleghi aggiunte quando servono.
- Branch **`feature/genai-core`** + commit; avvisare Collega 2 per `routers/sessions.py` e `main.py`.

### Documenti
- `README.md` e `funzionamento.md` aggiornati.
- `recap_18_11.md` è storico; `recap_18_11_2.md` è il log canonico dei lavori.

### Test
`test_reporter.py`, `test_sistema.py`, `test_interviewer.py`, `test_int_eval.py`, `test_api_full.py` e i controlli API offline sono verdi.

**Prossimo passo:** Collega 2 implementa `/turn` con i modelli pronti; Collega 1 prepara Supabase/auth; il team AR/VR usa le 4 paure e `metrica_paura`.
