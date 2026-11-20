# 🔍 FUNZIONAMENTO — come è fatto HireMate e come si legge

Guida didattica: cosa fa ogni file, come scorre una richiesta, quali concetti servono per spiegare il progetto al professore, e le **regole di lettura del codice** da usare quando ci si mette al lavoro.

> **Come usare questo file.** Leggi prima il [README](README.md) per la panoramica. Qui trovi il "perché" del codice. Le regole di sezione 5 sono **di metodo, non di stato**: valgono a ogni nuova modifica, anche quando il codice cambia.

---

## 1. Architettura in una pagina

```text
┌─────────────┐
│  Frontend   │  React / Three.js (team AR/VR)
└──────┬──────┘
       │ HTTP + JSON
┌──────▼──────────────────────────────────────────┐
│  main.py  (FastAPI + CORS)                      │
│    ├── routers/cv.py       POST /api/cv/parse   │
│    └── routers/sessions.py POST /api/session/*  │
└──────┬──────────────────────────────────────────┘
       │ chiamate async
┌──────▼──────────────────────────────────────────┐
│  agenti/                                        │
│    interviewer.py  → genera la domanda          │
│    evaluator.py    → valuta la risposta         │
│    reporter.py     → report + regola paura      │
│    cv_parser.py    → PDF → JSON                 │
│         └── tutti passano da llm.py             │
└──────┬──────────────────────────────────────────┘
       │ fallback a cascata
┌──────▼──────────────────────────────────────────┐
│  llm.py: FreeLLMAPI → Gemini Lite → DeepSeek    │
└─────────────────────────────────────────────────┘

Dati statici, iniettati nei prompt:
  corsi.py   → 14 corsi ITS (materie + focus HR)
  profilo.py → 3 liste del profilo + regola paura
```

| Livello | File | Responsabilità |
|---|---|---|
| Ingresso HTTP | `main.py` | Creare l'app, CORS, montare i router. Non contiene logica. |
| Contratti | `routers/*.py` | Validare i dati, mappare gli errori, chiamare gli agenti. |
| Logica AI | `agenti/*.py` | Costruire i prompt, interpretare le risposte, applicare le regole. |
| Rete LLM | `agenti/llm.py` | Chiamare i provider, timeout, retry, fallback, parsing JSON. |
| Dati | `corsi.py`, `profilo.py` | Knowledge base statica: nessun database, nessun RAG. |

---

## 2. I file, uno per uno

### 2.1 `main.py` — il buttafuori

Crea l'app FastAPI, abilita il CORS e collega i router.

```python
app.include_router(sessions.router, prefix="/api/session", tags=["Session"])
app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
```

- **CORS:** il frontend gira su un'altra origine (Vite `:5173`, Next `:3000`); senza `CORSMiddleware` il browser bloccherebbe le chiamate. Le origini arrivano da `CORS_ALLOW_ORIGINS`, separate da virgola.
- **Endpoint di servizio:** `GET /` (messaggio di benvenuto) e `GET /api/health` (stato di engine, database, llm).
- **Avvio:** `uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)` dentro `if __name__ == "__main__"`.

**Concetto:** *Separation of Concerns*. `main.py` monta i pezzi; non sa cosa sia una domanda di colloquio.

**Cosa succede senza:** il server non parte, oppure il browser dell'utente blocca ogni chiamata.

### 2.2 `corsi.py` — la knowledge base dei corsi

Dizionario `CORSI_ITS` con **14 corsi**, ognuno con `area`, `materie` e `focus_hr`.

```python
def get_dettagli_corso(nome_corso: str) -> dict:
    if nome_corso not in CORSI_ITS:
        raise CorsoNonValidoError(f"Corso non valido: '{nome_corso}'. ...")
    return CORSI_ITS[nome_corso]
```

`CorsoNonValidoError` eredita da `ValueError`: Pydantic la trasforma in un `422` prima ancora di entrare nell'endpoint.

**Concetto:** *Context Stuffing*. I dati certi dei corsi vengono iniettati nel prompt, senza RAG: 14 voci statiche non giustificano un database vettoriale.

**Cosa succede senza:** l'LLM inventerebbe materie e corsi inesistenti.

### 2.3 `profilo.py` — la knowledge base del profilo

Le 3 liste ufficiali della profilazione e la regola della paura:

```python
PAURE_DISPONIBILI = [
    "Restare senza parole",
    "Non sembrare abbastanza preparato tecnicamente",
    "Fare una figuraccia con il recruiter",
    "Non saper parlare di me stesso",
]
# ...STILI_GESTIONE_PROBLEMI, TIMORI_CRITICI

METRICA_PER_PAURA = {
    "Restare senza parole": "chiarezza",
    "Non sembrare abbastanza preparato tecnicamente": "esempi_concreti",
    "Fare una figuraccia con il recruiter": "struttura_star",
    "Non saper parlare di me stesso": "chiarezza",
}
SOGLIA_METRICA_PAURA = 7.5
```

**Concetto:** una sola fonte di verità. Backend e frontend devono mostrare le stesse card; il backend rifiuta tutto il resto con `422`.

**Cosa succede senza:** ogni file inventerebbe le proprie etichette e il confronto `ansia == "..."` non funzionerebbe più.

### 2.4 `agenti/llm.py` — il centralino telefonico

Un unico punto di ingresso per tutti gli LLM: `chiama_llm_json(system_prompt, user_prompt, temperature)`.

La catena, in ordine di costo crescente:

1. **FreeLLMAPI** (`auto:fastest`, timeout `3s`): locale e gratuito, ma spesso spento.
2. **Gemini `gemini-3.5-flash-lite`** (timeout `6s`): il provider di riferimento. Su `503`/`429`/quota/timeout fa **2 retry** con attesa (`LLM_RETRY_DELAY_SECONDS`, default 1.5s); su errori non temporanei (es. `400`) non ritenta.
3. **DeepSeek `deepseek-flash`** (timeout `30s`): è a pagamento, quindi **ultima risorsa**: nessun retry, così l'errore arriva in fretta.

```python
sequenza = [_chiama_freellmapi, _chiama_gemini, _chiama_deepseek]
```

Dettagli che contano:

- `_estrai_json` tollera i code fence markdown (```` ```json ````) e il testo prima/dopo l'oggetto JSON.
- `_errore_temporaneo` riconosce `503`, `429`, `UNAVAILABLE`, `RESOURCE_EXHAUSTED`, `RATE LIMIT`, `TIMEOUT`.
- Il timeout di Gemini è applicato con `asyncio.wait_for`, perché il client non ne ha uno suo.
- Se tutti falliscono, `LLMError` contiene **tutti** gli errori (`" | ".join`), non solo l'ultimo.

**Concetto:** *fallback* e *resilienza*. Un provider giù non spegne il servizio.

**Cosa succede senza:** al primo `503` di Gemini l'utente vedrebbe un errore, con il colloquio interrotto.

### 2.5 `agenti/interviewer.py` — l'HR manager

Genera **una** domanda comportamentale.

```python
async def genera_domanda(corso, profilo_soft_skill, cv_json=None, cronologia=None) -> str:
```

- usa corso, CV e profilo psicologico (ansia, stile, timore);
- se riceve `cronologia` (lista di `{"domanda", "trascrizione"}` o di modelli `Turno`), la inserisce nel prompt dentro `<Cronologia>` e **non ripete** le domande;
- temperatura **0.8**: serve variare le formulazioni;
- saluto/conferma e domanda restano nella stessa stringa;
- vieta frasi fatte tipo "Prenditi pure un momento per riflettere".

La scelta "prima domanda / domanda successiva" cambia il `user_prompt`, non il system prompt.

**Concetto:** *prompt XML* (`<role>`, `<context>`, `<instructions>`, `<output_format>`) + *memoria della conversazione*.

**Cosa succede senza `cronologia`:** l'Interviewer pone sempre "la prima domanda" e il colloquio non è realistico.

### 2.6 `agenti/evaluator.py` — il coach

Valuta la trascrizione su 3 metriche intere (1-10): `chiarezza`, `struttura_star`, `esempi_concreti`. Restituisce anche `suggerimento` (max 2 frasi) e `better_answer` (60-120 parole).

```python
for chiave in ("chiarezza", "struttura_star", "esempi_concreti"):
    risultato[chiave] = max(1, min(10, int(risultato.get(chiave, 1))))
```

Istruzione importante nel prompt: se la risposta è **vuota, incoerente, fuori tema o senza esempi** → voti **1-3**. Non si premia lo sforzo né la lunghezza.

**Concetto:** *temperatura bassa* (0.2) per una valutazione ripetibile; *prompt engineering* per calibrare la severità; *clamp* in Python perché l'LLM a volte sfora.

**Cosa succede senza il clamp:** un `11` o uno `0` finirebbe nel report e romperebbe medie e grafici.

### 2.7 `agenti/reporter.py` — il career coach

Calcola in **Python puro** l'`overall` 0-100 (Chiarezza 40%, STAR 30%, Esempi 30%) e applica la regola della paura:

```python
metrica_paura = METRICA_PER_PAURA.get(ansia, "chiarezza")
media_paura = {"chiarezza": media_chiarezza,
               "struttura_star": media_star,
               "esempi_concreti": media_esempi}[metrica_paura]

paura_superata_precedente = bool(
    report_precedente
    and report_precedente.get("paura_superata") is True
    and report_precedente.get("paura_attuale") == ansia
)
paura_superata = paura_superata_precedente or round(media_paura, 1) >= 7.5
```

- **Sticky:** se era già superata *per la stessa paura*, resta superata.
- Se la paura cambia, il confronto con `paura_attuale` fallisce e il flag riparte da `false`.
- `prossime_paure` = le altre 3 paure della Domanda 2, solo se `paura_superata` è `true`.
- `metrica_paura` rende esplicito quale metrica ha fatto scattare la promozione.
- L'LLM (temperatura 0.4) genera solo `badges`, `improvements` e `final_tip`.
- Se la lista `valutazioni` è vuota → `LLMError` (mai una divisione per zero).

**Concetto:** la gamification è deterministica e testabile; l'LLM scrive il testo, non decide i progressi.

**Cosa succede senza la regola in Python:** ogni sessione sarebbe un giudizio diverso e non riproducibile.

### 2.8 `agenti/cv_parser.py` — il lettore di CV

```python
def estrai_testo_pdf(contenuto: bytes) -> str:
    lettore = PdfReader(io.BytesIO(contenuto))
    pagine = [(pagina.extract_text() or "") for pagina in lettore.pages]
    ...

async def estrai_cv_json(contenuto: bytes) -> dict:
    return await chiama_llm_json(SYSTEM_PROMPT, testo, temperature=0.2)
```

- PDF corrotto → `ValueError("PDF non leggibile.")`.
- PDF senza testo estraibile (scansione/immagine) → `ValueError` → l'endpoint risponde `400`.
- Il prompt estrae **solo** `competenze` e `progetti`, senza inventare.

**Concetto:** pipeline PDF → testo → JSON strutturato. `pypdf` legge, l'LLM struttura.

**Cosa succede senza:** il CV resterebbe un allegato inutile, o un testo libero difficile da usare nel prompt.

### 2.9 `routers/sessions.py` — lo sportello del colloquio

Modelli Pydantic e due endpoint.

| Modello | A cosa serve |
|---|---|
| `ProfiloSoftSkill` | Valida le 3 risposte contro le liste di `profilo.py` (`422` se sbagliate). |
| `Valutazione` / `ValutazioneCompleta` | 3 voti 0-10 + suggerimento + better answer. |
| `SessionStartRequest/Response` | `/start`. |
| `EndSessionRequest/Response` | `/end`. |
| `Turno`, `TurnRequest`, `TurnResponse` | **Contratto pronto** per l'endpoint `/turn` di Collega 2. |

- `DOMANDE_PER_COLLOQUIO = 6`: il colloquio si chiude quando ci sono abbastanza informazioni, non con un timer brusco.
- `MAX_TRASCRIZIONE = 2000`, `MAX_DOMANDA = 500`, `MAX_CV_JSON = 4096`: limiti di input applicati dai modelli (`Field(max_length=...)` e tipo `CvJson`, che misura i byte del JSON). Scattano prima dell'LLM, quindi un payload abnorme costa `422` e zero quota. Anche `Turno` (la cronologia) li eredita.
- `turnId = f"turn-{uuid4().hex}"`: univoco a ogni chiamata.
- `visemes: list = Field(default_factory=list)`: niente default mutabile condiviso tra richieste.
- Errori: `CorsoNonValidoError` → `400`, `LLMError` → `503`, altro → `500` con log dettagliato e messaggio generico.
- `/start` restituisce `audioUrl=None`, `visemes=[]`, `gesture="explain"`: i campi ci sono già, li riempirà la TTS.

**Concetto:** *validazione dei dati*. FastAPI risponde `422` prima di chiamare l'LLM: si risparmiano tempo e quota.

**Cosa succede senza:** un valore inventato arriverebbe al prompt e l'utente pagherebbe una chiamata per un errore suo.

### 2.10 `routers/cv.py` — lo sportello del CV

`POST /api/cv/parse`: riceve un PDF (max 5 MB), controlla il tipo, chiama `cv_parser` e restituisce `{"cv_json": ...}`.

Errori: `415` tipo errato, `400` file vuoto o PDF illeggibile/senza testo, `413` troppo grande, `503` LLM giù, `500` generico.

**Concetto:** l'upload è la parte più "sporca" del sistema; va isolata e con limiti espliciti.

### 2.11 `.env` e `.gitignore` — la sicurezza

- `.env` contiene le chiavi (FreeLLMAPI, Gemini, DeepSeek); non va committato.
- `.env.example` è il modello da copiare, con segnaposto al posto delle chiavi.
- `.gitignore` esclude `venv/`, `.env`, `__pycache__/`, `*.pyc`.
- Le chiavi non vanno mai stampate, incollate in chat o messe in un `.md`.

**Concetto:** *security by default*: la configurazione segreta sta fuori dal codice e fuori da git.

---

## 3. Il flusso completo di una sessione

### Oggi (codice reale)

1. **Profilazione (frontend).** Lo studente risponde alle 3 domande; il frontend manda i valori esatti di `profilo.py`.
2. **CV (opzionale).** `POST /api/cv/parse` → `cv_json` con competenze e progetti.
3. **`POST /api/session/start`.** Pydantic valida corso e profilo; l'Interviewer chiama l'LLM e restituisce `sessionId`, `turnId` e `questionText`. Nessuna persistenza: il server non ricorda la sessione.
4. **Turni (mancante).** Oggi non esiste un endpoint che valuti un singolo turno: le valutazioni le fornisce il client direttamente a `/end`. L'endpoint `/turn` esiste solo come contratto.
5. **`POST /api/session/end`.** Il Reporter calcola medie e overall, applica la regola della paura, chiama l'LLM per badges/improvements/final_tip e restituisce il report. Le `valutazioni` arrivano dal client: è temporaneo.

### Dopo l'integrazione (obiettivo)

1. **Registrazione/login** → token; il profilo sta in `users`.
2. **CV** → `cv_json` salvato in `users.cv_json`.
3. **`/start`** → crea `sessions`, genera `sessionId`, salva il primo turno, restituisce la domanda + audio.
4. **`/turn`** (×6) → valuta, salva il turno, aggiorna la cronologia, genera la prossima domanda, restituisce audio + visemi. Al sesto: `colloquio_terminato = true`.
5. **`/end`** → legge tutto dal DB, calcola il report, propone le altre 3 paure.
6. **Promozione paura** → il frontend mostra la modale; `PATCH /api/users/update-fear` cambia `ansia_principale` e scrive `fears_history`.

### Perché `/turn` è il pezzo mancante

Senza `/turn` mancano tre cose in una: la **valutazione server-side** (oggi falsificabile), il **salvataggio dei turni** (oggi nessuno storico) e la **prossima domanda** (oggi il frontend non può andare avanti da solo). È assegnato a Collega 2: vedi [TODO.md](TODO.md#4-to-do--collega-2-stream-2-turn-api-e-audio).

---

## 4. I concetti da esame

| Concetto | Dove si vede | Come spiegarlo in una frase |
|---|---|---|
| Separation of Concerns | struttura dei file | Router = HTTP, agenti = prompt/LLM, `llm.py` = rete/fallback, `profilo.py`/`corsi.py` = dati. |
| Context Stuffing | `corsi.py`, `profilo.py` nei prompt | I 14 corsi e le 3 liste stanno nel prompt: niente RAG, meno latenza e meno pezzi. |
| Validazione dei dati | Pydantic (`BaseModel`) | Gli input si controllano prima di chiamare l'LLM: si risparmiano tempo e soldi. |
| Resilienza / fallback | `agenti/llm.py` | Se un provider non risponde, si prova il successivo con timeout crescenti. |
| Profilazione dinamica / gamification | `paura_superata`, `metrica_paura`, `prossime_paure` | La paura si supera sulla competenza specifica e il colloquio successivo si adatta. |
| Memoria della conversazione | `cronologia` nell'Interviewer | Senza storico l'HR ripeterebbe le stesse domande. |
| Sicurezza delle chiavi | `.env`, `.gitignore` | Le chiavi stanno fuori dal codice e fuori da git. |
| Contratto API | `routers/sessions.py`, `agenti/reporter.py` | Frontend e backend si scambiano JSON con campi concordati: se cambia un campo, cambiano entrambi. |
| Refactoring e test | `test_*.py` | Quando cambia la firma di una funzione, i test vanno aggiornati, altrimenti non verificano più nulla. |
| Test offline vs live | `test_enorme.py` | Il mock prova i casi limite; il live dimostra che il modello è collegato. |

---

## 5. Regole di lettura del codice

> File di metodo, non di stato. Servono a mantenere continuità tra una chat e l'altra: come si legge HireMate, come si interpretano le domande, come si ricava una regola da una modifica fatta a mano.

### 5.1 Una categoria vaga si definisce per estensione

Quando in un prompt o in una validazione compare una parola astratta, il modello (o il codice) la interpreta in modo incoerente. Si sostituisce la parola con i **casi concreti** che deve coprire.

Esempi reali:

- `agenti/cv_parser.py` — da *"linguaggi, strumenti, tecnologie"* a *"linguaggi di programmazione, strumenti informatici utilizzati, tecnologie"*; *"progetti"* → *"…compresi progetti realizzati"*. Motivo: "strumenti" si tirava dentro qualsiasi cosa (anche "teamwork") e "progetti" rischiava di far scartare i lavori personali.
- `agenti/evaluator.py` — non *"valuta severamente le risposte povere"* ma *"vuota, incoerente, fuori tema o senza esempi concreti → 1-3"*. La categoria "povera" è sostituita dai quattro casi che la compongono.

**Come si applica:** ogni volta che si scrive o si rivede un prompt, una soglia o una validazione, ci si chiede *"quale parola qui è interpretabile in due modi?"* e la si esplicita con esempi.

### 5.2 Protocollo di interpretazione

Per ogni domanda o modifica dell'utente si ricostruisce, in tre punti:

1. **cosa** ha chiesto o cambiato;
2. **quale dubbio** rivela (di solito un'ambiguità che codice o prompt non risolvono);
3. **la regola generale** che se ne ricava.

Se la deduzione è sbagliata, l'utente la corregge. **La motivazione dichiarata prevale sempre sulla deduzione**, e la correzione va registrata qui.

### 5.3 Stile delle risposte

- Solo la risposta diretta, breve, senza contorno.
- **Sempre un esempio concreto** che chiarisca l'affermazione.
- Niente preamboli, niente riepiloghi di ciò che l'utente ha appena detto.

### 5.4 Fase di studio: sola lettura

Durante lo studio del codice **non si modificano file**. Le modifiche le fa l'utente di propria mano, mentre studia.

Eccezioni ammesse: creare o aggiornare documenti su richiesta esplicita; nessun intervento su codice, `.env` o `venv/`.

### 5.5 Come crescono queste regole

Ogni nuova regola appresa si aggiunge qui, **con l'esempio del progetto che l'ha generata**, così resta verificabile e non si trasforma in teoria astratta.

### 5.6 L'ultima risorsa è la più affidabile e la più lenta

Catena dei provider: **FreeLLMAPI (3s) → Gemini Lite (6s) → DeepSeek (30s, a pagamento)**.

Regola: si ordina per costo e affidabilità **crescenti**, e si dà più tempo all'ultima, perché è quella che *deve* riuscire. I primi devono liberare il turno in fretta: l'utente è in attesa davanti a una domanda di colloquio.

Esempio: se i tre timeout fossero uguali, un servizio locale spento farebbe attendere 30s prima di arrivare al provider che funziona. Il test lo blinda: `TIMEOUT_FREELLMAPI <= 5`, `TIMEOUT_GEMINI <= 10`, `TIMEOUT_DEEPSEEK >= TIMEOUT_GEMINI`.

### 5.7 Gli errori si accumulano, non si sovrascrivono

Prima: `LLMError(f"... Errore: {ultimo_errore}")` — si perdeva il guasto di FreeLLMAPI, che è il primo della catena e quindi il più probabile.

Ora: gli errori si raccolgono in lista e si uniscono (`" | ".join`).

Esempio: un guasto del solo DeepSeek e uno di tutti e tre producevano lo stesso messaggio; oggi il secondo dice *quale* provider è caduto.

### 5.8 Un test che asserisce una lettera non prova niente

In `test_fallback_tutti` c'era `assert "a" in str(errore)`: `"a"` è contenuta in "f**a**llito", quindi l'asserzione era vera sempre, anche col messaggio sbagliato.

Regola: nelle asserzioni su stringhe si usano **frammenti distintivi** (es. `"free giù"`), mai singole lettere o parole comuni.

### 5.9 Un nuovo client di rete va mockato anche nei test che non lo nominano

`test_fallback` faceva patch solo di `_chiama_freellmapi` e `_chiama_gemini`. Aggiunto DeepSeek, con la chiave presente nel `.env` quei test avrebbero fatto **chiamate vere** dentro una suite che promette "nessuna quota".

Regola: quando si aggiunge un client di rete, si cerca ogni test che attraversa quella catena e lo si patcha, **anche se il test non lo cita**.

### 5.10 Il default nel codice non è la configurazione

`MODELLO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")`: se il `.env` definisce la variabile, il default **non viene mai usato**. Il default è documentazione, non verità.

Esempio: per passare a un modello della famiglia 4 sarebbe stato inutile cambiare `llm.py`, perché il `.env` fissava già `GEMINI_MODEL=gemini-3.5-flash-lite`. Prima di dire "il modello è X" si controlla il `.env`, non il codice.

Corollario: un nome di modello non si dà per buono. Si verifica con `ListModels` **e** con una `generateContent` vera sul contratto del progetto (JSON + `system_instruction`): `gemini-4.1-flash` non esiste, e dei quattro `gemini-4-*` solo `hydrogen` rispondeva con la chiave disponibile (gli altri 429 per quota).

Corollario 2: **il nome commerciale non è l'id API.** DeepSeek V4.1 Flash si chiama `deepseek-flash`; `deepseek-chat` è l'alias delle generazioni precedenti, e `deepseek-4.1-flash` non esiste. Stesso errore di `gemini-4.1-flash`: il nome leggibile del modello non è quello che va nella richiesta.

### 5.11 Un provider nuovo si verifica in quattro passi

Non basta che il codice compili: l'ordine dei controlli è quello che distingue "sembra funzionare" da "funziona".

1. **`GET /models`** con la chiave vera → l'id esiste? (`deepseek-flash` ✅, `deepseek-v4-pro` ✅)
2. **Call reale** sul contratto del progetto (JSON + `system_instruction`, temperatura vera) → risponde? (2.3s, JSON pulito)
3. **Errore volutamente sbagliato** (modello inesistente) → l'eccezione arriva come `LLMError` e non come eccezione grezza del client? Altrimenti la catena non la intercetta e l'API risponde 500 invece di 503.
4. **Catena completa** con i primi provider forzati a fallire → il fallback arriva davvero in fondo? (FreeLLMAPI giù + Gemini giù → DeepSeek, 1.1s)

Poi la suite offline deve restare verde, anche con la chiave nel `.env` (i test mockano i provider).

### 5.12 La sola lettura si sospende solo su richiesta esplicita

La fase di studio resta in sola lettura finché l'utente non chiede un'azione: commit e push sono ammessi **su richiesta esplicita**, mai di iniziativa, e restano confinati al branch di lavoro. `main` non si tocca e `.env` non entra in git.

Esempio (19/11): l'utente ha chiesto di committare e pushare le modifiche fino ad allora. Fatto su `feature/genai-core`, poi PR #1 mergiata in `main`.

### 5.13 Lo stato del remoto si verifica sul remoto

`git branch -a` mente quando i ref sono stantii. Il 20/11 il repository locale mostrava `main` a `2cc7462` e due branch che su GitHub non esistevano più: il `fetch` falliva con `SEC_E_NO_CREDENTIALS` e nessuno aggiornava i ref. La verità sta su GitHub (`GET /repos/{owner}/{repo}/git/refs`), non nel locale.

- `SEC_E_NO_CREDENTIALS` non è un problema del repo: le operazioni git le fa l'utente nel suo terminale.
- Su OneDrive `git fetch --prune` può chiedere più volte `Deletion of directory ... failed`: rispondere **`n`**, poi `git update-ref -d <ref>` per i ref rimasti. Sono reparse point di OneDrive, non branch veri.
- **Divisione dei compiti (preferenza dell'utente):** le modifiche si fanno in **VS Code**; branch, commit e push dal **terminale di VS Code**; pull request, merge e cancellazione dei branch dal **sito GitHub**.
- **Lo stato si scrive in un punto solo:** la sezione "Stato attuale" del README e il diario del RECAP. Ripetere hash, date e numeri di PR in cinque file è il modo più rapido per farli divergere.

### 5.14 Un check verde non visto fallire non è una prova

La CI può essere verde perché **non esegue niente**: file sbagliato, comando sbagliato, evento che non la triggera. L'unico modo per sapere che il check misura qualcosa è rompere il codice di proposito e vedere il rosso.

Esempio (20/11): `SOGLIA_METRICA_PAURA` portata da 7.5 a 8.0 su un branch usa-e-getta ha fatto cadere 4 test (`La soglia è 7.5` più tre del Reporter) e, con la protezione attiva, ha reso grigio il pulsante di merge. Senza quella prova la protezione sarebbe stata solo una casella spuntata.

Corollario: la prova si fa su un branch che poi si chiude senza mergiare, e si chiude con la suite di nuovo verde — `84/88` con la modifica, `88/88` dopo. Un rosso senza il ritorno al verde non distingue un test rotto da un errore di configurazione.

### 5.15 Un fatto, un proprietario

La duplicazione non è il problema: lo è ripetere lo **stato** in documenti che non lo possiedono. Il 20/11 `88/88` era scritto in 55 punti e `main` in sei; ogni merge lasciava indietro qualcosa.

- **Stato** (conteggi, PR, commit, branch, quanti documenti): un solo posto — "Stato attuale" del README e diario del RECAP. Gli altri rimandano.
- **Struttura dei file**: tabella del README. FUNZIONAMENTO spiega i file, non li elenca; il RECAP non ridisegna l'albero.
- **Contratto API attuale**: README. TODO tiene solo ciò che è in transizione (`/turn`, `/end` dal DB, auth).
- **Decisioni e perché**: RECAP §6. FUNZIONAMENTO cita la regola, non la decisione.
- **Storia**: il diario del RECAP non si riscrive, anche quando i numeri cambiano.
- **`AGENTS.md`**: eccezione dichiarata: duplica i valori stabili perché è il contesto dell'agente, ma se contraddice il codice vince il codice.

Esempio: aggiungere un caso a `test_enorme.py` costa due modifiche nel README (numero e output) e una a `CASI_ATTESI` nella suite, non venti sparse in quattro documenti.

---

## 6. I test: come funzionano e cosa coprono

### 6.1 In 30 secondi

- `test_enorme.py` è la suite principale, **offline**: non chiama nessun LLM, non consuma quota, dura pochi secondi. I numeri aggiornati stanno nel [README](README.md#-test).
- Con `--live` aggiunge **3 chiamate vere** a Gemini Lite.
- `test_hardening_input.py` è la seconda suite offline: verifica i limiti di input e che oltre il limite arrivi `422`.
- Ogni suite controlla anche **quanti** casi ha eseguito (`CASI_ATTESI`): se qualcuno cancella un test, il totale non torna e l'esecuzione esce con codice 1.
- L'output finale riporta `TOTALE`, `PASSATI`, `FALLITI`; se un test fallisce compare `❌ nome del test -> errore` con il traceback.
- **In CI** (`.github/workflows/test.yml`) girano esattamente `python test_enorme.py` e `python test_hardening_input.py` su `windows-latest` con Python 3.14, a ogni PR e a ogni push su `main`; `main` è protetta e il merge richiede il check `suite offline`. I test live restano fuori: chiavi e quota non stanno nella CI.

### 6.2 Mock vs live: la spiegazione semplice

Immagina un'auto:

- **Test offline = crash test con il manichino.** Proviamo tutti gli urti possibili senza rischiare persone vere. Il manichino è il "finto LLM": simuliamo `503`, timeout, JSON rotto, voti sballati. Velocissimo, gratis, ripetibile.
- **Test live = giro su strada con l'auto vera.** Facciamo 3 chiamate reali a Gemini Lite per verificare che il motore sia collegato e che l'Evaluator non premi una risposta povera.

Servono entrambi: il crash test non dimostra che l'auto parte; il giro su strada non può simulare tutti gli incidenti.

### 6.3 Cosa testa, sezione per sezione

| Sezione | Cosa verifica | Esempio concreto | Perché conta |
|---|---|---|---|
| **1. Profilo e metriche** | Le 4 paure, i 4 stili, i 4 timori, la mappa paura → metrica, soglia 7.5 e validazione stretta | `"Paura inventata"` → `422` | Se il frontend manda un valore diverso, il backend non lo accetta |
| **2. Corsi** | 14 corsi completi; corso inesistente → `CorsoNonValidoError` | `SOC Analyst` esiste, `Corso Inventato` no | Evita domande su corsi inesistenti |
| **3. LLM** | JSON, code fence, retry 2 su `503/429/timeout`, nessun retry su `400`, fallback FreeLLMAPI → Gemini → DeepSeek | 2 errori 503 + 1 successo = 3 tentativi | Il servizio non cade al primo errore temporaneo |
| **4. Interviewer** | Prima domanda, `cronologia`, nessuna ripetizione, CV nel prompt, temperatura 0.8 | con `D1/R1` la domanda successiva tiene conto della risposta | Senza memoria il colloquio non è realistico |
| **5. Evaluator** | Voti sempre 1-10, campi mancanti, prompt severo, voti come stringhe | `0 → 1`, `11 → 10` | L'LLM a volte sfora: il codice lo corregge |
| **6. Reporter** | Overall, stats precedenti, sticky, reset, 3 opzioni, metrica che batte l'overall, soglia 7.4/7.5 | chiarezza 7.5 con overall basso → paura superata | È la regola nuova: conta la competenza specifica |
| **7. Modelli e API** | Pydantic, `TurnRequest`/`TurnResponse`, `/start`, `/end`, `422/503/500`, `turnId` univoco, OpenAPI, CORS | profilo invalido → 422; LLM giù → 503 | Il frontend riceve errori chiari, non crash |
| **8. CV** | PDF → testo → JSON, PDF vuoto/corrotto, limite 5 MB, endpoint 200/415/400/413/503/500 | PDF valido → `{"cv_json": ...}` | Il CV non deve far crashare il server |
| **9. Config e documenti** | `requirements.txt` UTF-8 e dipendenze, `.env.example`, `.gitignore`, i 5 documenti (`AGENTS.md` compreso), il diario del RECAP (3 colonne, ordine cronologico, soglia di righe), input | niente `google-generativeai`, niente Gemini 3.8 | Il progetto si installa, i documenti sono allineati e il diario non perde righe |
| **10. LIVE** (solo `--live`) | Gemini vero: domanda reale, evaluator severo, reporter con LLM | risposta povera → 4/1/1 | Dimostra che il collegamento con l'LLM funziona davvero |

### 6.4 Se un test fallisce

- l'output mostra `❌ nome del test -> errore`;
- in fondo c'è il **traceback** con file e riga;
- i test offline non dipendono da Internet: un fallimento è quasi sempre un bug vero o un test da aggiornare;
- i test live possono fallire per `503`/quota: aspetta qualche minuto e rilancia.

I comandi per eseguirli sono nel [README](README.md#-test).

---

## 7. Come spiegarlo in 2 minuti

> «HireMate è un simulatore di colloqui. Il backend prende il profilo dello studente, genera domande, valuta le risposte e produce un report.
>
> Prima il progetto aveva tre problemi: i test non giravano più, la paura veniva superata con una media generale (quindi una competenza debole poteva nascondersi), e l'Interviewer non ricordava le domande precedenti.
>
> Oggi: le 3 risposte della profilazione sono validate contro liste ufficiali; la paura si supera solo quando **la metrica specifica** arriva a 7.5/10 (es. chiarezza per "restare senza parole"); una volta superata resta superata, ma se cambi paura riparte; l'Interviewer riceve la cronologia e non ripete; l'Evaluator dà 1-3 alle risposte povere; il backend ha CORS, errori HTTP chiari e un endpoint per il CV in PDF.
>
> La suite offline verifica i casi principali in pochi secondi, senza consumare quota. Con `--live` fa anche 3 chiamate vere a Gemini Lite: una domanda, una valutazione severa (4/1/1 su una risposta povera) e un report (80/100). I test offline servono per la logica e i casi limite; quelli live per dimostrare che l'LLM è davvero collegato.
>
> Il backend è mergiato in `main`. Mancano `/turn`, database, auth e voce dell'avatar: sono nel TODO diviso tra noi tre.»

---

## 8. Domande probabili e risposte

**Perché non usate un RAG per i corsi?**
14 corsi statici: il context stuffing è più semplice, senza latenza e senza infrastruttura. Un RAG avrebbe senso con centinaia di corsi che cambiano spesso.

**Perché la paura non usa l'overall?**
Perché ogni paura riguarda una competenza specifica: un overall alto può nascondere una debolezza. Se la paura è "restare senza parole", la metrica da guardare è la chiarezza. Lo dimostra il test: chiarezza 7.5 con STAR ed esempi a 1 → paura superata, overall basso.

**Perché 7.5 e non 8?**
7.5/10 è una soglia di padronanza: non basta la sufficienza, ma non è nemmeno impossibile. È una costante in `profilo.py`, si cambia in un punto.

**Cos'è lo "sticky"?**
Una volta superata per quella paura, resta superata anche se in una sessione successiva il voto scende. Se cambia la paura, riparte da zero: la nuova paura non è ancora stata affrontata.

**Perché serve `paura_attuale`?**
Per sapere a quale paura si riferisce il flag. Senza, dopo un cambio paura la sticky farebbe risultare già superata anche la nuova.

**Perché la regola della paura è in Python e non nell'LLM?**
Perché deve essere ripetibile e testabile: un LLM darebbe un giudizio diverso a ogni chiamata, e non si potrebbe garantire la soglia.

**Cosa succede se Gemini dà 503?**
Il wrapper fa 2 retry su 503/429/timeout con attesa; poi prova DeepSeek come ultima risorsa; se falliscono tutti, l'API risponde `503` con un messaggio chiaro. I test offline restano verdi.

**Cosa succede se DeepSeek manca o è a secco?**
La catena lo salta (`LLMError` "DeepSeek non configurato") e il messaggio finale elenca tutti i provider caduti: l'utente riceve un 503 generico, il log ha il dettaglio.

**Perché i test offline?**
Per verificare la logica e forzare casi difficili (503, timeout, JSON rotto, PDF corrotto) in modo veloce e deterministico, senza quota. I test live verificano il modello vero.

**Perché `report_precedente` arriva dal client?**
È temporaneo: la fonte di verità sarà Supabase. Oggi il client rimanda il report della sessione precedente per far funzionare la sticky.

**Perché un branch e non `main`?**
Per non rompere `main` e poter fare merge/PR dopo la review. La PR #1 è stata mergiata solo a test verdi.

**Cosa manca ancora?**
L'endpoint `/turn` (Collega 2), Supabase/auth (Collega 1), TTS/visemi (Collega 2), frontend (team AR/VR). Lato Stream 3 restano CI, protezione di `main`, hardening degli input e qualità dei test. Dettaglio in [TODO.md](TODO.md).

**Perché `python-multipart` e `pypdf`?**
`python-multipart` serve a FastAPI per ricevere l'upload del PDF; `pypdf` a leggerne il testo.

**Perché i voti sono 0-10 nella `Valutazione` e 1-10 nell'Evaluator?**
La `Valutazione` è il contratto API: il modello Pydantic accetta 0-10. L'Evaluator produce 1-10 (clamp) perché un voto 0 non ha senso per una risposta. Il clamp è coperto dai test.

**Perché l'Interviewer ha temperatura 0.8 e l'Evaluator 0.2?**
Creatività dove serve variare le domande, determinismo dove serve ripetibilità del giudizio.

**Cosa succede se il PDF è una scansione?**
`pypdf` non estrae testo → `ValueError` → `400` "Il PDF non contiene testo estraibile." OCR fuori perimetro.

**Come si legge il codice senza perdersi?**
Dall'esterno verso l'interno: `main.py` → router → agente → `llm.py` → dati in `corsi.py`/`profilo.py`. Le regole di sezione 5 valgono per ogni modifica.
