# HireMate GenAI API – Spiegazione dei file

## 📄 1. `main.py` (Il Buttafuori)

È il punto di ingresso. Il suo unico compito è avviare il server e collegare i router.

```python
app = FastAPI(title="HireMate GenAI API")
app.include_router(sessions.router, prefix="/api/session", tags=["Session"])
```

**Cosa spiega:** L'uso di `FastAPI` per creare l'applicazione e `include_router` per smistare le chiamate al file corretto.

---

## 📄 2. `corsi.py` (La Knowledge Base Statica)

Contiene il dizionario `CORSI_ITS` con i 14 corsi, le materie e i focus HR.

```python
def get_dettagli_corso(nome_corso: str) -> dict:
    if nome_corso not in CORSI_ITS:
        raise ValueError(f"Corso non valido: '{nome_corso}'.")
    return CORSI_ITS[nome_corso]
```

**Cosa spiega:** Il concetto di **Context Stuffing** (iniettare dati certi nel prompt invece di usare un RAG) e il **Fail Fast** (se il corso è sbagliato, lancia un errore subito invece di far crashare l'LLM).

---

## 📄 3. `agenti/llm.py` (Il Centralino Telefonico)

Il wrapper che nasconde la complessità delle API esterne. Gestisce il doppio fallback.

```python
sequenza = [_chiama_freellmapi, _chiama_gemini]
for provider in sequenza:
    try:
        return await provider(system_prompt, user_prompt, temperature)
    except LLMError as e:
        logger.warning(f"Fallback attivato: {e}")
```

```python
response_format={"type": "json_object"}
```

**Cosa spiega:** Il pattern **Fallback** (se il primo provider è offline, usa il secondo) e l'uso di `response_format` per obbligare l'LLM a restituire JSON validi, evitando crash nel codice Python.

---

## 📄 4. `agenti/interviewer.py` (L'HR Manager)

Genera le domande basandosi sul corso, sul CV e sul profilo psicologico.

```python
async def genera_domanda(corso: str, profilo_soft_skill: dict, cv_json: dict | None = None) -> str:
```

```xml
<role>
Sei un HR Manager esperto...
</role>
<context>
Ansia principale: {ansia}...
</context>
```

**Cosa spiega:** L'uso di **Prompt XML** (`<role>`, `<context>`) per dare struttura alle istruzioni, l'**Asincronia** (`async def`) per non bloccare il server, e il passaggio di un unico oggetto `profilo_soft_skill` per mantenere il codice pulito.

---

## 📄 5. `agenti/evaluator.py` (Il Coach)

Valuta la risposta dell'utente su 3 metriche e genera suggerimenti.

```python
system_prompt = f"""
2. Assegna tre voti interi da 1 a 10...
   - **chiarezza**: ...
   - **struttura_star**: ...
   - **esempi_concreti**: ...
"""
risultato = await chiama_llm_json(..., temperature=0.3)
```

**Cosa spiega:** L'uso di una `temperature=0.3` (bassa) per rendere la valutazione oggettiva e ripetibile, e la capacità dell'LLM di restituire un JSON strutturato con voti e suggerimenti personalizzati.

---

## 📄 6. `routers/sessions.py` (Lo Sportello API)

Riceve le richieste HTTP e le traduce in comandi Python. Usa Pydantic per la validazione.

```python
class SessionStartRequest(BaseModel):
    corso: str
    profilo_soft_skill: dict
    cv_json: dict | None = None
```

```python
@router.post("/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
```

**Cosa spiega:** Il concetto di **Validazione dei Dati** (se il frontend manda un JSON sbagliato, FastAPI risponde con `422 Unprocessable Content` prima ancora di chiamare l'LLM, risparmiando tempo e soldi).

---

## 📄 7. `.env` e `.gitignore` (La Sicurezza)

- `.env`: contiene `GEMINI_API_KEY`, `FREELLMAPI_BASE_URL`, ecc.
- `.gitignore`: contiene `venv/`, `.env`, `__pycache__/`.

**Cosa spiega:** La separazione tra codice e configurazione. Le chiavi API non devono mai finire su GitHub per motivi di sicurezza.

---

## 🧠 I 3 Concetti Fondamentali da Ricordare (Per l'esame)

1. **Separation of Concerns:** ogni file fa una cosa sola. `llm.py` sa come chiamare l'AI; `interviewer.py` sa cosa chiedere; `corsi.py` sa i dati.
2. **Defensive Programming:** usiamo `try/except` in ogni file, i `BaseModel` di Pydantic per validare l'input, e il `.get()` sui dizionari per evitare i `KeyError`.
3. **Agentic Workflow:** non c'è un unico mega-prompt confuso, ma una catena di agenti specializzati (Interviewer -> Evaluator -> Reporter) che si passano i dati in formato JSON.