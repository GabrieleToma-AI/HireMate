# HireMate GenAI API – Spiegazione dei file

Guida semplice per capire cosa fa ogni file e come spiegarlo al professore.

## 📄 1. `main.py` (Il Buttafuori)

È il punto di ingresso: crea l'app FastAPI, abilita il CORS (il frontend gira su un'altra porta) e collega i router.

```python
app.include_router(sessions.router, prefix="/api/session", tags=["Session"])
app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
```

**Concetto:** *Separation of Concerns*: `main.py` non contiene logica, solo il montaggio dei pezzi.

---

## 📄 2. `corsi.py` (La Knowledge Base dei corsi)

Dizionario `CORSI_ITS` con 14 corsi, le materie e il focus HR.

```python
def get_dettagli_corso(nome_corso: str) -> dict:
    if nome_corso not in CORSI_ITS:
        raise CorsoNonValidoError(f"Corso non valido: '{nome_corso}'.")
    return CORSI_ITS[nome_corso]
```

**Concetto:** *Context Stuffing*: i dati certi dei corsi vengono iniettati nel prompt, senza RAG. `CorsoNonValidoError` è un `ValueError`: Pydantic lo trasforma in `422`.

---

## 📄 3. `profilo.py` (La Knowledge Base del profilo)

Le 3 liste della profilazione (paure, reazioni, timori) e la regola della paura:

```python
METRICA_PER_PAURA = {
    "Restare senza parole": "chiarezza",
    "Non sembrare abbastanza preparato tecnicamente": "esempi_concreti",
    "Fare una figuraccia con il recruiter": "struttura_star",
    "Non saper parlare di me stesso": "chiarezza",
}
SOGLIA_METRICA_PAURA = 7.5
```

**Concetto:** una sola fonte di verità per le opzioni; il backend valida i valori e il frontend mostra le stesse card.

---

## 📄 4. `agenti/llm.py` (Il Centralino Telefonico)

Wrapper unico per gli LLM:

1. prova **FreeLLMAPI** (`auto:fastest`, timeout 5s);
2. se fallisce, prova **Gemini `gemini-3.5-flash-lite`**;
3. su `503`/`429`/quota fa **2 retry** con attesa;
4. `_estrai_json` tollera i code fence markdown.

```python
sequenza = [_chiama_freellmapi, _chiama_gemini]
```

**Concetto:** *Fallback* e *resilienza*: se un provider è giù, il servizio resta disponibile. `LLMError` è l'errore comune.

---

## 📄 5. `agenti/interviewer.py` (L'HR Manager)

Genera **una** domanda comportamentale.

```python
async def genera_domanda(corso, profilo_soft_skill, cv_json=None, cronologia=None) -> str:
```

- usa corso, CV e profilo psicologico;
- se riceve `cronologia` (lista di `{"domanda", "trascrizione"}`), la inserisce nel prompt e **non ripete** le domande;
- temperatura 0.8 per variare le formulazioni;
- vieta frasi fatte come "Prenditi pure un momento per riflettere".

**Concetto:** *Prompt XML* (`<role>`, `<context>`, `<instructions>`) e *memoria della conversazione*.

---

## 📄 6. `agenti/evaluator.py` (Il Coach)

Valuta la trascrizione su 3 metriche (1-10): `chiarezza`, `struttura_star`, `esempi_concreti`.
Restituisce anche `suggerimento` (max 2 frasi) e `better_answer` (60-120 parole).

Istruzione importante: se la risposta è vuota, incoerente, fuori tema o senza esempi, i voti sono **1-3**. Non si premia lo sforzo.
I voti vengono riportati in sicurezza tra 1 e 10 con `max(1, min(10, int(...)))`.

**Concetto:** *temperatura bassa* (0.3) per una valutazione ripetibile; *prompt engineering* per calibrare la severità.

---

## 📄 7. `agenti/reporter.py` (Il Career Coach)

Calcola in Python l'`overall` 0-100 (Chiarezza 40%, STAR 30%, Esempi 30%) e gestisce la paura:

```python
metrica_paura = METRICA_PER_PAURA[ansia]
media_paura = {"chiarezza": media_chiarezza, ...}[metrica_paura]
paura_superata = paura_superata_precedente or round(media_paura, 1) >= 7.5
```

- **Sticky:** se era già superata per la stessa paura, resta superata.
- Se la paura cambia, riparte da `false`.
- `prossime_paure` = le altre 3 paure della Domanda 2.
- L'LLM genera `badges`, `improvements`, `final_tip`.

**Concetto:** la regola di gamification è in Python puro (deterministica e testabile); l'LLM scrive solo il testo del report.

---

## 📄 8. `agenti/cv_parser.py` (Il Lettore di CV)

```python
def estrai_testo_pdf(contenuto: bytes) -> str:
    lettore = PdfReader(io.BytesIO(contenuto))
    ...
async def estrai_cv_json(contenuto: bytes) -> dict:
    return await chiama_llm_json(SYSTEM_PROMPT, testo, temperature=0.2)
```

**Concetto:** pipeline PDF → testo → JSON strutturato. `pypdf` legge il PDF, l'LLM estrae solo competenze e progetti.

---

## 📄 9. `routers/sessions.py` (Lo Sportello API)

Modelli Pydantic e endpoint:

- `ProfiloSoftSkill`: valida le 3 risposte contro le liste di `profilo.py` (422 se sbagliate).
- `Valutazione`: 3 voti tra 0 e 10.
- `SessionStartRequest/Response`: `/start`.
- `EndSessionRequest/Response`: `/end`.
- `TurnRequest/TurnResponse` + `Turno`: **contratto pronto per Collega 2** per `/turn`.
- `DOMANDE_PER_COLLOQUIO = 6`: il colloquio si chiude quando ci sono abbastanza informazioni, non con un timer brusco.

**Concetto:** *validazione dei dati*: FastAPI risponde `422` prima di chiamare l'LLM, risparmiando tempo e quota. Gli errori interni non vengono esposti al client.

---

## 📄 10. `routers/cv.py` (Lo Sportello del CV)

`POST /api/cv/parse`: riceve un PDF (max 5 MB), controlla il tipo, chiama `cv_parser` e restituisce `{"cv_json": ...}`.
Errori: `415` tipo errato, `400` PDF vuoto/illeggibile, `413` troppo grande, `503` LLM giù.

---

## 📄 11. `.env` e `.gitignore` (La Sicurezza)

- `.env` contiene le chiavi (FreeLLMAPI, Gemini); non va committato.
- `.gitignore` esclude `venv/`, `.env`, `__pycache__/`.
- Le chiavi non vanno mai stampate o incollate.

---

## 🧠 I concetti da ricordare

1. **Separation of Concerns:** router = HTTP, agenti = prompt/LLM, `llm.py` = API/fallback, `profilo.py`/`corsi.py` = dati.
2. **Context Stuffing:** i 14 corsi e le 3 liste stanno nel prompt; niente RAG.
3. **Validazione:** Pydantic blocca input sbagliati prima dell'LLM.
4. **Resilienza:** FreeLLMAPI → Gemini Lite, retry su 503, timeout.
5. **Gamification:** la paura si supera sulla metrica specifica (7.5/10) e resta superata; il report propone le altre 3 paure.
6. **Memoria:** `cronologia` permette domande di follow-up senza ripetizioni.
7. **Sicurezza:** chiavi fuori dal codice e da git; PIN con hash bcrypt (Collega 1).

## 🎤 Domande probabili del prof

- Perché non usate un RAG per i corsi? → 14 corsi statici: il context stuffing è più semplice e senza latenza.
- Perché la paura non usa l'overall? → ogni paura riguarda una competenza specifica.
- Cosa succede se Gemini è in 503? → 2 retry con attesa, poi errore 503 chiaro al client.
- Perché i test offline? → `test_reporter.py` non consuma quota; gli altri verificano l'integrazione reale.
- Perché `report_precedente` arriva dal client? → è temporaneo; la fonte di verità sarà Supabase.
