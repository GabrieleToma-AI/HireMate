# AGENTS.md — contesto operativo di HireMate

> **Cos'è questo file.** È il contesto che l'agente LLM riceve automaticamente all'inizio di ogni nuova chat (DeepSeek Harness carica `AGENTS.md` dal root del progetto). Descrive **ciò che non cambia** a ogni commit: architettura, regole di dominio, contratti, convenzioni, trappole. Lo **stato** del progetto (cosa è fatto, cosa manca, ultimi commit) **non** sta qui: sta in [TODO.md](TODO.md) e [RECAP.md](RECAP.md).
>
> **Regola d'oro:** se questo file e il codice si contraddicono, **vince il codice**. Allora o il codice ha un bug, o un invariante è cambiato e questo file va aggiornato — non il contrario.

---

## 1. Il progetto in breve

HireMate è un **simulatore di colloqui HR** per studenti degli ITS ICT del Piemonte. Uno studente inserisce il corso, tre risposte di profilazione soft skill e (opzionalmente) il CV in PDF; il backend genera domande comportamentali, valuta le risposte e produce un report gamificato che gli dice se ha superato la sua paura principale.

- **Lingua del prodotto e del codice:** italiano (identificatori, messaggi, commenti).
- **Tono:** professionale, diretto, da HR vero. Non "coccoloso", non un amico.
- **Target:** studenti junior IT, spesso ansiosi: le domande devono essere realistiche ma comprensibili.
- **Team:** 3 AI engineer (Python/backend) + 3 AR/VR & game (frontend).
- **Stack:** Python 3.14, FastAPI, Pydantic v2, `google-genai`, `pypdf`, OpenAI SDK compatibile per FreeLLMAPI/DeepSeek. Supabase (DB e auth) e Azure TTS (voce avatar) sono previsti ma vivono in stream di lavoro separati.
- **Vincolo:** progetto scolastico. Deve restare **corto, completo, funzionante e spiegabile al professore**. Preferire soluzioni semplici e deterministiche a quelle eleganti.

L'utente che ti parla è lo **Stream 3 / GenAI core**: proprietario di `agenti/`, `routers/`, `main.py`, test e documenti.

---

## 2. Mappa dei documenti

| File | Ruolo | Quando leggerlo |
|---|---|---|
| `AGENTS.md` (questo) | Regole stabili, architettura, invarianti, trappole | Sempre, è già caricato |
| `README.md` | Panoramica, API, setup, test, stato sintetico | Per primo dopo questo |
| `FUNZIONAMENTO.md` | Guida didattica file per file + regole di lettura del codice + Q&A del prof | Per capire *come* funziona il codice |
| `RECAP.md` | Diario dei lavori, changelog, errori corretti, **scelte** di codice e feature | Per capire *perché* il codice è così |
| `TODO.md` | Cosa manca: task generale + task per ciascuno dei 3 AI engineer, contratto API, regole, demo | Per lavorare |

**Lo stato attuale non è in questo file.** Se ti serve sapere cosa è implementato: `git log`, `git status`, `README.md` (sezione stato) e soprattutto il codice. Non fidarti della memoria della chat precedente né di un documento che afferma "fatto" senza una verifica.

---

## 3. Come lavorare in una nuova chat

1. **Leggi il contesto già caricato** (`AGENTS.md`) e, se serve il dettaglio, `README.md` → `FUNZIONAMENTO.md` → `RECAP.md` → `TODO.md`.
2. **Verifica lo stato reale**: `git status`, `git branch --show-current`, `git log --oneline -5`. Non assumere che il branch sia `main` né che l'albero sia pulito.
3. **Esegui i test** prima di toccare qualsiasi cosa: `python test_enorme.py`. Se non sono verdi, il problema è precedente al tuo intervento: dillo.
4. **Leggi il codice coinvolto** prima di modificarlo (`read`, non `cat`). Le firme, i nomi dei campi e i contratti contano più dei commenti.
5. **Modifica il minimo** che risolve il problema, con un test che lo dimostra. Una modifica per volta.
6. **Riporta nell'ordine**: cosa hai cambiato → perché → come verificarlo → come spiegarlo al prof → impatto sui colleghi.
7. **Non committare di iniziativa.** Commit, push e merge solo su richiesta esplicita dell'utente.

### Stile delle risposte all'utente

- Solo la risposta diretta, breve, senza preamboli.
- **Sempre un esempio concreto** (un file, una riga, un comando, un numero).
- Se una deduzione è incerta, dichiarala come tale; la motivazione dell'utente prevale sulla deduzione.
- Quando l'utente studia il codice, **non modificare file**: leggere e spiegare. Le modifiche le fa lui di mano, salvo richiesta esplicita.

---

## 4. Architettura

```text
Frontend (React / Three.js)
      │ HTTP + JSON
main.py  (FastAPI + CORS)
   ├── routers/cv.py        POST /api/cv/parse
   └── routers/sessions.py  POST /api/session/*
          │
      agenti/  (interviewer, evaluator, reporter, cv_parser)
          │
      agenti/llm.py  → FreeLLMAPI → Gemini Lite → DeepSeek
          │
      dati statici: corsi.py, profilo.py  (iniettati nei prompt, niente RAG)
```

| Livello | File | Responsabilità |
|---|---|---|
| Ingresso HTTP | `main.py` | Creare l'app, CORS, montare router e (in futuro) `static/`. Nessuna logica di dominio. |
| Contratti | `routers/*.py` | Validare input (Pydantic), mappare eccezioni → HTTP, chiamare gli agenti. |
| Logica AI | `agenti/*.py` | Costruire i prompt, interpretare le risposte, applicare le regole di dominio. |
| Rete LLM | `agenti/llm.py` | Catena provider, timeout, retry, fallback, estrazione JSON. |
| Dati | `corsi.py`, `profilo.py` | Knowledge base statica: nessun database, nessun RAG. |

**Separation of Concerns** è un requisito, non un consiglio: un router non costruisce prompt, un agente non conosce HTTP, `llm.py` non conosce il dominio.

---

## 5. Dominio: le regole che non cambiano

### 5.1 Profilazione (3 domande, validazione stretta)

Tre campi, ognuno validato contro la lista ufficiale in `profilo.py`. Un valore fuori lista → **422** (Pydantic), prima di qualsiasi chiamata all'LLM.

| Campo | Domanda | Lista |
|---|---|---|
| `ansia_principale` | "Cosa ti spaventa di più all'idea di fare un colloquio?" | `PAURE_DISPONIBILI` (4) |
| `stile_gestione_problemi` | "Quando ti trovi di fronte a un problema difficile, come reagisci?" | `STILI_GESTIONE_PROBLEMI` (4) |
| `timore_critico` | "Se il colloquio andasse male, quale pensi sarebbe il motivo principale?" | `TIMORI_CRITICI` (4) |

### 5.2 La regola della paura superata

Ogni paura è misurata da **una metrica specifica**, non dall'overall:

| Paura | Metrica | Soglia |
|---|---|---|
| Restare senza parole | `chiarezza` | 7.5/10 |
| Non sembrare abbastanza preparato tecnicamente | `esempi_concreti` | 7.5/10 |
| Fare una figuraccia con il recruiter | `struttura_star` | 7.5/10 |
| Non saper parlare di me stesso | `chiarezza` | 7.5/10 |

- `paura_superata` = la metrica specifica (media di sessione) ≥ **7.5**, **oppure** sticky se era già `true` per la **stessa** paura.
- Lo sticky richiede **entrambi** i campi: `paura_superata is True` **e** `paura_attuale == ansia_principale`. Se la paura cambia, il flag riparte da `false`.
- `metrica_paura` dice quale metrica ha fatto scattare la promozione.
- `prossime_paure` = le altre 3 paure della lista, e solo se `paura_superata` è `true`.
- La regola è **in Python puro** (`agenti/reporter.py`), deterministica e testata: l'LLM non decide i progressi, scrive solo il testo.

### 5.3 Punteggi e report

- Le tre metriche sono **interi 1-10**. L'Evaluator le limita in Python (`max(1, min(10, int(...)))`): l'LLM sfora.
- L'overall 0-100 è una media pesata: **Chiarezza 40%, STAR 30%, Esempi 30%**, moltiplicata per 10.
- Il report contiene sia chiavi storiche in inglese (`overall_previous`, `overall_current`, `stats_previous`, `stats_current`, `badges`, `improvements`, `final_tip`) sia campi nuovi in italiano (`paura_attuale`, `metrica_paura`, `paura_superata`, `prossime_paure`). **Non tradurre le chiavi inglesi:** rompe il frontend.
- Il vecchio nome `fear_overcome` è superato: usare `paura_superata`.

### 5.4 Durata del colloquio

`DOMANDE_PER_COLLOQUIO = 6` è indicativo: il colloquio si chiude quando ci sono abbastanza informazioni, non con un timer. L'endpoint dei turni imposta `colloquio_terminato` e il client mostra il report.

### 5.5 Corsi

14 corsi ITS in `corsi.py`, ognuno con `area`, `materie`, `focus_hr`. `get_dettagli_corso()` solleva `CorsoNonValidoError(ValueError)` per un corso inesistente → **422**.

### 5.6 Glossario

- **Profilo soft skill**: i 3 campi sopra.
- **Turno**: una coppia domanda + trascrizione dello studente.
- **Valutazione**: i 3 voti + suggerimento + better answer.
- **Paura**: `ansia_principale`, non il `timore_critico`.
- **Promozione**: il passaggio a una nuova paura dopo averla superata.
- **Completamento**: colloquio chiuso con `colloquio_terminato = true`.

---

## 6. Prompt e LLM: invarianti di comportamento

### 6.1 Catena provider

1. **FreeLLMAPI** — locale, gratuito, spesso spento. Timeout corto.
2. **Gemini `gemini-3.5-flash-lite`** — provider di riferimento. **2 retry** su 503/429/quota/timeout, con attesa breve; nessun retry su errori non temporanei (es. 400).
3. **DeepSeek `deepseek-flash`** — a pagamento, **ultima risorsa**, nessun retry: l'errore deve arrivare in fretta.

Regola: i primi due devono liberare il turno in fretta (l'utente è in attesa davanti a una domanda), l'ultima deve riuscire. Se tutti falliscono, `LLMError` elenca **tutti** gli errori, non solo l'ultimo. Gli endpoint traducono `LLMError` in **503** generico.

### 6.2 Prompt

- Struttura XML: `<role>`, `<context>`, `<instructions>`, `<output_format>`, e input in tag dedicati (`<domanda>`, `<trascrizione>`, `<Cronologia>`).
- Output **solo JSON**; `chiama_llm_json` estrae il JSON anche da code fence o testo extra.
- Temperature: interviewer **0.8** (varietà), evaluator **0.2** (ripetibilità), reporter **0.4**, cv_parser **0.2**.
- Le domande sono **comportamentali**, mai tecniche. Vietato "Prenditi pure un momento per riflettere" e formule ripetute.
- Se c'è `cronologia`, l'Interviewer non ripete le domande e costruisce il follow-up sulla risposta precedente.
- Ogni categoria vaga va sostituita con i casi concreti che deve coprire. Esempio: non "valuta severamente le risposte povere" ma "vuota, incoerente, fuori tema o senza esempi concreti → 1-3".

### 6.3 Anti-invenzione

- L'Interviewer può usare il CV, non inventare esperienze.
- L'Evaluator non inventa esperienze nella `better_answer`: se mancano, usa il segnaposto `[un tuo esempio reale]`.
- Il CV parser estrae solo `competenze` e `progetti`; se un dato non c'è, lascia la lista vuota.

---

## 7. API: contratto e convenzioni

### 7.1 Endpoint previsti

| Metodo | Percorso | Ruolo |
|---|---|---|
| `POST` | `/api/cv/parse` | PDF (max 5 MB) → `{"cv_json": {...}}` |
| `POST` | `/api/session/start` | Valida corso e profilo, genera la prima domanda e `sessionId`/`turnId` |
| `POST` | `/api/session/turn` | Valuta la trascrizione, aggiorna la cronologia, genera la prossima domanda (+ audio), imposta `colloquio_terminato` |
| `POST` | `/api/session/end` | Report finale: overall, medie, paura superata, prossime paure |
| `GET` | `/` e `/api/health` | Servizio e health check |

**Quali sono montati davvero lo dice `main.py`.** I modelli dei turni possono esistere in `routers/sessions.py` anche quando l'endpoint non è ancora attivo: il contratto e l'implementazione sono due cose separate.

### 7.2 Convenzioni JSON

- Le risposte usano camelCase per i campi "di trasporto": `turnId`, `sessionId`, `questionText`, `audioUrl`, `prossimaDomanda`, `colloquio_terminato`.
- Le richieste e il dominio usano snake_case: `profilo_soft_skill`, `ansia_principale`, `struttura_star`, `esempi_concreti`.
- `audioUrl` e `visemes` hanno sempre un fallback: `null` e `[]`. Il colloquio deve funzionare anche senza TTS.
- `visemes` è `[{"time": <ms>, "visemeId": <int>}]`.

### 7.3 Errori HTTP

| Codice | Quando |
|---|---|
| `422` | Input non valido: profilo fuori lista, corso inesistente, voti fuori range, lista vuota. Scatta **prima** dell'LLM. |
| `400` | PDF vuoto/illeggibile/senza testo; `CorsoNonValidoError` sollevata dentro l'endpoint (difensivo). |
| `413` | PDF oltre 5 MB. |
| `415` | File non PDF. |
| `503` | LLM non disponibile dopo i fallback. Messaggio generico. |
| `500` | Errore interno. Log completo sul server, messaggio generico al client. |

**Mai esporre `str(eccezione)` al client.** I dettagli (e le chiavi) restano nei log.

### 7.4 Stato della sessione (in transizione)

- `sessionId` esiste per collegare `users → sessions → turns` quando ci sarà il database.
- Senza DB, la cronologia viaggia nel payload e `report_precedente` arriva dal client: è **temporaneo**, la fonte di verità sarà Supabase.
- `/end` che si fida delle valutazioni del client è un limite noto della transizione: non introdurne altri.

---

## 8. Test

- **Suite principale:** `test_enorme.py`. Offline, mock di ogni client di rete, nessuna quota. È la rete di sicurezza: **deve restare verde**.
- **Modalità live:** `python test_enorme.py --live` aggiunge poche chiamate reali a Gemini Lite. Serve a dimostrare che il modello è collegato, non a provare la logica.
- **Script di integrazione:** `test_reporter.py` (offline), `test_sistema.py`, `test_interviewer.py`, `test_int_eval.py`, `test_api_full.py` (richiede il server attivo su `:8000`). Alcuni stampano soltanto: se non hanno assert, non sono test.
- **Regole:** ogni nuovo client di rete va mockato **anche nei test che non lo nominano**; le asserzioni usano frammenti distintivi, mai singole lettere (`"a" in "fallito"` è sempre vero); un test che passa con un input sbagliato è peggio di un test mancante.
- **Comandi:** vedi `README.md`. Attiva il venv prima: `.\venv\Scripts\Activate.ps1`.

---

## 9. Convenzioni di codice

- **Lingua:** italiano per nomi di dominio, messaggi utente, commenti e documenti. Inglese solo dove è un contratto esterno (chiavi storiche del report, nomi di campi standard).
- **Async:** tutte le funzioni che chiamano l'LLM sono `async`. Nessuna chiamata bloccante nei router.
- **Pydantic v2:** `field_validator` con `@classmethod`, `Field(ge=..., le=..., min_length=...)`, `default_factory` per le liste.
- **Errori:** eccezioni di dominio (`CorsoNonValidoError`, `LLMError`) mappate nei router; mai `raise HTTPException` dentro gli agenti.
- **Tipi:** type hint su firme e valori di ritorno; `dict | None` invece di `Optional[dict]`.
- **Nomi:** `snake_case` in Python, `camelCase` solo nei modelli di trasporto HTTP.
- **Nessun segreto nel codice.** Chiavi solo da `.env` via `python-dotenv`.

---

## 10. Git e collaborazione

- **Mai commit su `main`.** Branch per ogni lavoro (`feature/...`, `docs/...`), PR verso `main`, merge con merge commit.
- **PR piccole e tematiche.** Una modifica logica per PR: contratto, prompt, docs. Non mescolare.
- **Niente `.env`, `venv/`, `__pycache__` nei commit.** `.env` non è mai stato tracciato e non deve entrarci.
- **Un solo proprietario per file.** `main.py`, `routers/sessions.py`, `requirements.txt`, `.env.example` sono condivisi: chi li tocca lo coordina. `routers/turn.py` e `agenti/tts.py` sono di Collega 2; `database/` e `routers/users.py` di Collega 1.
- **`main` deve restare sempre funzionante**: è quello che il professore apre per la demo.
- **Encoding:** tutto UTF-8. Mai `pip freeze > requirements.txt` (su PowerShell scrive UTF-16 e riempie il file di dipendenze transitive): le dipendenze si aggiungono a mano, dirette e pinnate.
- **Commit message:** prefisso (`feat:`, `fix:`, `docs:`, `test:`) + italiano, corpo con il perché.

---

## 11. Trappole note (impara dagli errori già fatti)

1. **Il default nel codice non è la configurazione.** `os.getenv("X", "default")` viene ignorato se `.env` definisce `X`: prima di dire "il modello è Y" controlla il `.env`, non `llm.py`.
2. **Il nome commerciale non è l'id API.** DeepSeek V4.1 Flash si chiama `deepseek-flash`; `deepseek-chat` è un alias vecchio; `gemini-4.1-flash` non esiste.
3. **Un provider nuovo si verifica in quattro passi:** `GET /models` con la chiave vera, una call reale sul contratto del progetto, un errore voluto (modello inesistente) che deve diventare `LLMError` e non eccezione grezza, poi la catena completa con i primi provider forzati a fallire.
4. **PowerShell e la codifica.** `>` e `Out-File` possono scrivere UTF-16 (BOM `FF FE`). Se un file di testo diventa "binario" in `git diff`, è successo questo: riscrivilo in UTF-8.
5. **Mockare i client di rete non basta una volta.** Aggiungendo un provider vanno patchati anche i test che attraversano la catena senza nominarlo, altrimenti la suite "offline" fa chiamate vere.
6. **Non fidarti dei documenti come prova.** Questo progetto è stato scritto in parte da un modello "a basso effort": i documenti hanno dichiarato feature inesistenti (es. `fear_overcome`). Il codice e i test sono la verità.
7. **OneDrive.** La cartella è sincronizzata: non condividerla e considera che può bloccare temporaneamente i file (errori EIO su scrittura).
8. **Errori di rete nel sandbox.** `git fetch` può fallire con `SEC_E_NO_CREDENTIALS` in un ambiente non interattivo: non è un problema del repo, le operazioni git le fa l'utente nel suo terminale.
9. **`/end` oggi si fida del client.** Non è una svista: è la transizione verso Supabase. Non aggiungere altre fiducie temporanee.
10. **Le liste del profilo sono un contratto col frontend.** Card diverse = paure sconosciute. Se cambiano, cambiano insieme backend, frontend e test.

---

## 12. Come spiegare il progetto al professore (in 30 secondi)

> «HireMate simula un colloquio HR. Il backend valida il profilo dello studente, genera domande comportamentali con un LLM, valuta ogni risposta su tre metriche oggettive e produce un report. La regola di gamification è in Python, non nell'LLM: una paura si supera quando la competenza specifica arriva a 7.5/10, e resta superata. L'LLM è trattato come un servizio inaffidabile: catena di tre provider, timeout, retry e fallback, e una suite di test offline che non consuma quota.»

---

## 13. Quando aggiornare questo file

Aggiornalo **solo** se cambia uno di questi:

- l'architettura o il ruolo di un file;
- una regola di dominio (soglie, mappe paura → metrica, pesi dell'overall, numero di domande);
- un contratto API o la convenzione dei nomi;
- una nuova trappola che ha già causato un bug.

**Non** aggiornarlo per: commit, stato dei task, conteggio dei test, branch, esiti di una sessione. Quello è materiale per `TODO.md` e `RECAP.md`.

Tienilo sotto i ~32 KB: viene iniettato a ogni nuova chat e consuma contesto.
