# 🧾 RECAP — diario dei lavori e scelte

Registro di **cosa è stato fatto** e **perché il codice è così**. Sostituisce i vecchi `recap_18_11*.md`, `cambiamenti_ultimo_push.md`, `handoff.md` e le decisioni sparse nel `piano_lavoro_18_11.md`.

> Stato aggiornato al **20/11/2026**. Cosa manca: [TODO.md](TODO.md). Come funziona il codice: [FUNZIONAMENTO.md](FUNZIONAMENTO.md).

---

## 1. Stato in una frase

Il backend GenAI di HireMate è **mergiato su `main`**, con profilo validato, paura misurata sulla metrica specifica (7.5/10), cronologia nell'Interviewer, Evaluator severo, endpoint CV, catena LLM a tre provider e **88 test offline verdi**. Mancano: endpoint `/turn`, Supabase, auth, TTS/visemi e frontend.

---

## 2. Cosa c'è oggi nel repository

```text
main.py              FastAPI + CORS + router
corsi.py             14 corsi ITS
profilo.py           3 liste + METRICA_PER_PAURA + soglia 7.5
agenti/
  llm.py             FreeLLMAPI -> Gemini Lite -> DeepSeek
  interviewer.py     domanda con cronologia
  evaluator.py       valutazione 1-10
  reporter.py        report + regola paura
  cv_parser.py       PDF -> JSON
routers/
  sessions.py        /start, /end + contratti /turn
  cv.py              POST /api/cv/parse
test_enorme.py       88 test offline (91 con --live)
test_reporter.py     regola paura, offline
test_sistema.py, test_interviewer.py, test_int_eval.py, test_api_full.py
requirements.txt     dipendenze dirette, UTF-8
.env.example         modello delle variabili
README.md, FUNZIONAMENTO.md, RECAP.md, TODO.md
```

**Non presenti:** `database/`, `routers/users.py`, `routers/turn.py`, `agenti/tts.py`, `static/`, frontend.

---

## 3. Diario cronologico

| Quando | Cosa | Commit |
|---|---|---|
| 17/11, 23:14 | Primo backend GenAI: `/start`, `/end`, Reporter, test end-to-end. È il punto di partenza del ciclo di lavoro. | `3a15197` |
| 18/11, pomeriggio | Analisi in sola lettura: trovati 3 errori gravi + 13 secondari (sezione 5). | — |
| 18/11, 21:40 | Implementazione: `profilo.py`, paura per metrica, `cronologia`, Evaluator severo, CV parser, `routers/cv.py`, CORS, `turnId` univoco, test allineati. | `b27e44c` |
| 18/11, 21:48 | Suite `test_enorme.py` (88 test) + changelog. | `0c0d192` |
| 18/11, 21:54 | Modalità `--live` (91 test) e documenti aggiornati. | `26226f1` |
| 18/11, 21:56 | Guida al test e ai cambiamenti. | `09496ef` |
| 18/11, 21:58 | Handoff per riprendere in una nuova chat. | `87fb062` |
| 19/11, 02:52 | Terza risorsa LLM DeepSeek + timeout per provider. | `ed73019` |
| 19/11, 02:52 | Regole di lettura del codice + handoff aggiornato. | `fa994a6` |
| 19/11, 11:44 | Split del lavoro rimasto tra i 3 AI engineer. | `6523869` |
| 19/11, 12:03 | Merge della PR #1: il backend è su `main`. | `e62ac4c` |
| 19/11, sera | Consolidamento documenti: da 9 `.md` sparsi a 4 file (README + FUNZIONAMENTO + RECAP + TODO). | — |
| 19/11, 20:13 | Merge della PR #2: i 4 documenti sono su `main`. | `468fe3b` |
| 20/11, 00:27 | Contratto `sessionId` (obbligatorio in `/start`, opzionale in `/turn` e `/end`) e merge della PR #3. | `2cc7462` |
| 20/11, 00:33 | Merge della PR #4: lo stato dei documenti non dipende più dagli hash. | `73e8188` |
| 20/11 | Merge della PR #5: `AGENTS.md` come quinto documento; `test_enorme.py` accetta il nuovo `.md` e ne limita la dimensione. | `352e7d4` |
| 20/11 | Allineamento documenti: cinque file, Blocco 0.5 (guardrail) nel TODO, diagnosi dei prompt in §6.9. | — |

---

## 4. Changelog file per file (ciclo GenAI)

Rispetto a `3a15197` sono cambiati **27 file: 11 nuovi, 16 modificati**. (I documenti di allora sono oggi confluiti nei 5 file attuali: vedi sezione 10.)

| File | Stato | Cosa è cambiato rispetto a `3a15197` |
|---|---|---|
| `profilo.py` | **Nuovo** | Le 3 liste ufficiali della profilazione (`PAURE_DISPONIBILI`, `STILI_GESTIONE_PROBLEMI`, `TIMORI_CRITICI`), la mappa `METRICA_PER_PAURA` e `SOGLIA_METRICA_PAURA = 7.5`. |
| `agenti/reporter.py` | Modificato | La paura si supera sulla **metrica specifica** (non sull'overall): mappa paura → metrica, soglia 7.5, sticky per la stessa paura, reset se la paura cambia. Aggiunti `metrica_paura`, `prossime_paure` (le altre 3 paure). |
| `agenti/interviewer.py` | Modificato | Nuovo parametro `cronologia`: inserisce `<Cronologia>` nel prompt, non ripete le domande, usa un `user_prompt` "prima/prossima". Temperatura da 0.7 a 0.8. |
| `agenti/evaluator.py` | Modificato | Prompt più severo: risposte vuote/incoerenti/fuori tema/senza esempi → voti **1-3**. Voti sempre interi 1-10; `suggerimento` e `better_answer` sempre presenti. |
| `agenti/llm.py` | Modificato | Solo `gemini-3.5-flash-lite` per Gemini (rimosso il secondo modello di fallback), 2 retry su 503/429/timeout, timeout configurabile, `_estrai_json` tollerante a code fence e testo extra, `raise ... from e`, errori accumulati. |
| `agenti/cv_parser.py` | **Nuovo** | Estrae il testo dal PDF con `pypdf`; PDF corrotto → `ValueError`; trasforma il testo in JSON (`competenze`, `progetti`) con il wrapper LLM. |
| `routers/cv.py` | **Nuovo** | `POST /api/cv/parse`: PDF max 5 MB → `cv_json`; errori 415/400/413/503/500. |
| `routers/sessions.py` | Modificato | Validazione stretta del profilo (422); modelli `Valutazione`, `ValutazioneCompleta`, `Turno`, `TurnRequest`, `TurnResponse`; `DOMANDE_PER_COLLOQUIO = 6`; `turnId` univoco; `visemes` con `default_factory`; errori 400/422/503/500 senza dettagli interni. |
| `corsi.py` | Modificato | `CorsoNonValidoError(ValueError)`; `get_dettagli_corso()` la solleva per un corso inesistente. |
| `main.py` | Modificato | `CORSMiddleware` configurabile con `CORS_ALLOW_ORIGINS`; incluso il router CV; health check aggiornato. |
| `requirements.txt` | Modificato | Riscritto in **UTF-8** (era UTF-16 con BOM), solo dipendenze dirette: `google-genai==3.4.0`, `pypdf==7.1.1`, `python-multipart==0.0.34`; rimosso `google-generativeai`. |
| `.env.example` | Modificato | Modello unico Lite, timeout per provider, `LLM_RETRY_DELAY_SECONDS`, `CORS_ALLOW_ORIGINS`, chiavi DeepSeek; rimosso `GEMINI_FALLBACK_MODEL`. |
| `input_registrazione.txt` | Modificato | `timore_critico` allineato alla lista ufficiale: `"Non ho abbastanza esperienza tecnica per il ruolo"`. |
| `test_reporter.py` | **Nuovo** | Test offline del Reporter: 7.4/7.5 per ogni metrica, mappa paura → metrica, sticky, reset, 3 opzioni, default. |
| `test_enorme.py` | **Nuovo** | Suite: 88 test offline (mock LLM) su profilo, corsi, retry/timeout/fallback, interviewer/cronologia, evaluator, reporter, modelli/API, CV, CORS e documenti; `--live` aggiunge 3 test reali. |
| `test_api_full.py` | Modificato | Profilo ufficiale; stampa `paura_superata`, `metrica_paura`, `prossime_paure`; verifica le due sessioni (prima bassa, seconda alta). |
| `test_int_eval.py` | Modificato | Passa `profilo_soft_skill` (non più `paura_colloquio`/`reazione_problema`/`paura_fallimento`); exit code 1 in caso di errore; UTF-8. |
| `test_interviewer.py` | Modificato | Passa `profilo_soft_skill` (non più `soft_skill`); exit code 1; UTF-8. |
| `test_sistema.py` | Modificato | Firma aggiornata, profilo ufficiale, exit code 1 se un test fallisce, UTF-8. |
| Documenti | Modificati | README, funzionamento, piano, recap, changelog, guida, handoff, regole, split: **oggi tutti confluiti nei 5 file attuali**. |

### File rimasti invariati

`.gitignore` (già esclude `venv/`, `.env`, `__pycache__/`), `agenti/__init__.py`, `routers/__init__.py` (vuoti), `.env` (non tracciato), `venv/` (non tracciato).

---

## 5. Errori trovati e corretti

L'analisi iniziale (18/11, in sola lettura) doveva trovare **3 errori**; ne sono emersi 3 gravi e 13 secondari. Il progetto era stato scritto da un modello "a basso effort": i documenti dichiaravano cose che il codice non faceva.

### 5.1 [ALTA] `requirements.txt` non riproducibile: il server non parte da un'installazione pulita

**Evidenza**

- `agenti/llm.py` usa `from google import genai` (nuovo SDK `google-genai`), ma `requirements.txt` elencava `google-generativeai==0.8.6` (SDK legacy) e **non** `google-genai`.
- Nel `venv` c'era `google_genai-3.4.0`, ma non `google/generativeai`: l'ambiente era stato aggiustato a mano e non corrispondeva al file.
- `requirements.txt` era salvato in **UTF-16 LE con BOM**.

**Impatto:** su un'altra macchina l'import di `main.py` fallisce con `ImportError: cannot import name 'genai' from 'google'`.

**Fix applicato:** `requirements.txt` riscritto in UTF-8 con le dipendenze dirette e le versioni del venv (`fastapi==0.163.1`, `uvicorn==0.54.0`, `pydantic==2.14.3`, `python-dotenv==1.2.4`, `openai==3.52.0`, `google-genai==3.4.0`, `httpx==0.28.1`, poi `python-multipart`, `pypdf`); rimosso `google-generativeai`.

**Come spiegarlo al prof:** «Le dipendenze sono la lista della spesa del progetto: se manca un pacchetto, il programma non parte. Il codice usava il pacchetto nuovo di Google, ma la lista conteneva quello vecchio; inoltre il file era in un formato di testo strano (UTF-16), poco leggibile dagli strumenti.»

### 5.2 [ALTA] I test chiamavano gli agenti con parametri che non esistevano più

**Evidenza:** le firme erano già `genera_domanda(corso, profilo_soft_skill, ...)` e `valuta_risposta(corso, profilo_soft_skill, ...)`, ma `test_interviewer.py` e `test_sistema.py` passavano `soft_skill=`, e `test_int_eval.py` passava `paura_colloquio=`, `reazione_problema=`, `paura_fallimento=`.

**Impatto:** `TypeError` prima di qualsiasi chiamata all'LLM: nessun test poteva passare. In più `test_sistema.py` stampava "FALLITO" **senza exit code diverso da zero**: una CI sarebbe risultata verde con i test rotti.

**Fix applicato:** test allineati al nuovo contratto (`profilo_soft_skill`), contatore di fallimenti e `sys.exit(1)`, funzioni async rinominate `run_*` per evitare problemi di collezione con pytest, `test_api_full.py` aggiornato ai nuovi campi.

### 5.3 [MEDIA] Il report non restituiva lo stato della paura (feature dichiarata ma assente)

**Evidenza:** il recap dichiarava `fear_overcome` e la modale frontend, ma `agenti/reporter.py` restituiva solo `overall_previous/current`, `stats_previous/current`, `badges`, `improvements`, `final_tip`. Nessuna occorrenza di `fear_overcome` o `paura_superata` nei `.py`.

**Impatto:** la modale "Promozione Paura" non si sarebbe mai attivata.

**Fix applicato:** la regola completa (sezione 6.3), con `paura_attuale`, `metrica_paura`, `paura_superata`, `prossime_paure`.

### 5.4 Errori secondari

| # | Problema | Evidenza | Stato |
|---|---|---|---|
| 1 | Manca CORS: un frontend su un'altra origine viene bloccato | `main.py` | **Fatto**: `CORSMiddleware` configurabile |
| 2 | Fallback Gemini Flash → Flash-Lite incoerente con i documenti | `agenti/llm.py`, README | **Fatto**: solo `gemini-3.5-flash-lite` |
| 3 | Corso non valido restituiva `503` invece di `400/422` | interviewer + sessions | **Fatto**: `CorsoNonValidoError(ValueError)` → 422 |
| 4 | `/end` si fidava delle `valutazioni` del client, senza range né lunghezza minima | `routers/sessions.py` | **Fatto**: `Valutazione` 0-10 + `min_length=1` (resta il limite "client": serve `/turn`) |
| 5 | Gli errori generici restituivano `str(e)` al client | `routers/sessions.py` | **Fatto**: log interno + messaggio generico |
| 6 | `turnId` fisso `"mock-turn-001"` | `routers/sessions.py` | **Fatto**: `uuid4().hex` |
| 7 | `visemes: list = []` come default mutabile | `routers/sessions.py` | **Fatto**: `Field(default_factory=list)` |
| 8 | Import inutilizzati e commento duplicato | reporter, evaluator | **Fatto**: pulizia |
| 9 | Punteggi mancanti contati come 0 nelle medie | `agenti/reporter.py` | **Fatto**: validazione + liste non vuote |
| 10 | JSON dell'LLM non ripulito da code fence | `agenti/llm.py` | **Fatto**: `_estrai_json` |
| 11 | `LLMError` rilanciato senza `from e` | `agenti/llm.py` | **Fatto**: `raise ... from e` |
| 12 | Nessun timeout sulle chiamate Gemini (FreeLLMAPI ne aveva uno) | `agenti/llm.py` | **Fatto**: timeout per provider |
| 13 | `/turn` assente: l'Evaluator non è raggiungibile e i voti sono falsificabili | `routers/sessions.py` | **Rinviato**: è lavoro di Collega 2 (vedi [TODO.md](TODO.md)) |

---

## 6. Scelte di codice e di feature

### 6.1 Tabella delle decisioni

| Tema | Decisione | Perché | Alternativa scartata |
|---|---|---|---|
| Catena LLM | FreeLLMAPI → Gemini Lite → DeepSeek | gratuita, poi affidabile, poi a pagamento come ultima risorsa | un solo provider (un guasto spegne il servizio) |
| Timeout | 3s / 6s / 30s | i primi devono liberare il turno, l'ultima deve riuscire | timeout uguali (attesa inutile di 30s) |
| Retry | 2 retry solo su Gemini, su 503/429/timeout | è il provider di riferimento; FreeLLMAPI e DeepSeek devono fallire in fretta | retry su tutti (costo e latenza) |
| Modello Gemini | solo `gemini-3.5-flash-lite` | un solo modello = contratto semplice e testabile | fallback tra due modelli Gemini |
| Modello DeepSeek | id API `deepseek-flash` | è l'id che risponde; `deepseek-chat` è un alias vecchio | nome commerciale "V4.1 Flash" (non è l'id) |
| JSON dall'LLM | `response_format` + `_estrai_json` | i modelli aggiungono code fence o testo | parsing ingenuo (falliva a ogni variazione) |
| Errori LLM | accumulati in una lista e uniti | si vede quale provider è caduto | solo l'ultimo errore (ingannevole) |
| Paura superata | metrica **specifica** ≥ 7.5 | la paura riguarda una competenza, non la media | overall ≥ 75/100 (nasconde le debolezze) |
| Sticky | resta superata per la stessa paura | non far perdere i progressi | ricalcolo ogni sessione |
| Reset | se cambia `ansia_principale` | la nuova paura non è stata affrontata | sticky "globale" (sarebbe falsa) |
| `paura_attuale` | incluso nel report | serve a capire a quale paura si riferisce il flag | solo booleano (ambiguo dopo un cambio) |
| Nomi campi | nuovi campi in italiano, chiavi storiche in inglese | contratto frontend: non si rompono `overall_*` e `stats_*` | tradurre tutto (rompeva il frontend) |
| `prossime_paure` | le altre 3 paure della Domanda 2 | la lista ne ha 4: escludendo quella attuale restano 3 card | `next_fear_options` (nome inglese non concordato) |
| Validazione profilo | stretta contro `profilo.py` → 422 | input inventati non arrivano all'LLM | stringhe libere |
| Corso | `CorsoNonValidoError(ValueError)` → 422 | errore semantico corretto, non 503 | 503 per corso errato |
| Errori HTTP | 400/422/413/415/503/500 + messaggi generici | il client capisce cosa correggere senza leak | `str(e)` al client |
| `turnId` | `uuid4().hex` | univoco per turno | id fisso "mock-turn-001" |
| `visemes` | `Field(default_factory=list)` | default mutabile condiviso è un bug classico | `= []` |
| Colloquio | `DOMANDE_PER_COLLOQUIO = 6`, non un timer | si chiude quando ci sono informazioni, senza rifiuti bruschi | limite di 10 minuti rigido |
| Cronologia | lista di `{domanda, trascrizione}` nel prompt | senza storia l'HR ripete le domande | nessuna memoria |
| Temperature | interviewer 0.8, evaluator 0.2, reporter 0.4, cv 0.2 | creatività dove serve variare, determinismo dove serve giudicare | una temperatura unica |
| CV | `pypdf` + LLM, max 5 MB, solo PDF | semplice e senza OCR; il PDF non si salva | OCR (fuori perimetro) |
| Stato sessione | Supabase come fonte di verità (in arrivo) | persistenza vera, `/end` non si fida del client | solo client (falsificabile) |
| `report_precedente` | trasporto temporaneo dal client | fa funzionare la sticky prima del DB | rimuoverlo subito (rompeva la feature) |
| Auth | nickname + PIN 4 cifre, hash bcrypt, JWT breve, rate limit | PIN corto → serve protezione | PIN in chiaro o senza rate limit |
| Test | offline con mock + live a parte | veloce, gratis, deterministico | solo test live (quota e lentezza) |
| Git | branch + PR verso `main` | non rompere `main`, review tra pari | commit diretti su `main` |
| Documenti | 5 file stabili: `AGENTS.md` (regole) + 4 di progetto | 9 file duplicavano le stesse informazioni | un `.md` per ogni sessione (illeggibile) |

### 6.2 Catena LLM in dettaglio

```text
FreeLLMAPI (locale, 3s, 0 retry)
   └─ fallisce → Gemini gemini-3.5-flash-lite (6s, 3 tentativi con attesa 1.5s)
        └─ fallisce → DeepSeek deepseek-flash (30s, 0 retry)
             └─ fallisce → LLMError con TUTTI gli errori
```

- `max_retries=0` sui client OpenAI-compatibili (FreeLLMAPI, DeepSeek): i retry li gestisce il wrapper solo per Gemini.
- `_errore_temporaneo` decide se ritentare; un `400` non viene ritentato.
- La chiave DeepSeek è opzionale: se manca, la catena lo salta e lo dice nel messaggio finale.
- DeepSeek è **a pagamento**: non usarlo nei test di massa (i test offline non chiamano nessun provider).

### 6.3 La regola della paura in dettaglio

| Paura (Domanda 2) | Metrica | Soglia |
|---|---|---|
| Restare senza parole | `chiarezza` | 7.5/10 |
| Non sembrare abbastanza preparato tecnicamente | `esempi_concreti` | 7.5/10 |
| Fare una figuraccia con il recruiter | `struttura_star` | 7.5/10 |
| Non saper parlare di me stesso | `chiarezza` | 7.5/10 |

- `paura_superata` = la metrica specifica (media della sessione, arrotondata a 1 decimale) ≥ 7.5, **oppure** sticky se era già `true` per la stessa paura.
- Il confronto sticky richiede **entrambi** i campi: `paura_superata is True` **e** `paura_attuale == ansia`.
- `prossime_paure` = le altre 3 della lista, solo se `paura_superata` è `true`.
- Il flag viaggia nel report: il client lo rimanda in `report_precedente` alla sessione successiva. Non serve il DB per la regola, serve per non fidarsi del client.
- **Non** è previsto un numero minimo di sessioni: con 7.5 alla prima sessione la paura risulta già superata (deciso così).

Esempio numerico: valutazioni `chiarezza 7.5`, `struttura_star 1`, `esempi_concreti 1` → overall basso ma paura "Restare senza parole" **superata**, perché conta solo la chiarezza.

**Evoluzione della decisione:** la prima proposta (18/11, pomeriggio) era *overall ≥ 75/100*; la sera stessa è stata scartata perché un overall alto può nascondere una competenza debole. La regola definitiva è quella della tabella: metrica specifica ≥ 7.5.

I quattro nomi da non confondere:

| Nome | Cosa è | Dove vive |
|---|---|---|
| `PAURE_DISPONIBILI` | Le 4 paure selezionabili in registrazione (Domanda 2) | `profilo.py` |
| `paura_superata` | Booleano: la metrica specifica ha raggiunto 7.5 (o era già superata per la stessa paura) | Risposta di `/end` |
| `prossime_paure` | Le altre 3 paure da proporre per la sessione successiva | Risposta di `/end` |
| `paura_attuale` | Testo della paura a cui si riferisce il flag (serve per la sticky) | Risposta di `/end` |

Esempio di report (contratto con il frontend):

```json
{
  "overall_previous": 58.0,
  "overall_current": 76.0,
  "stats_previous": {"chiarezza": 6.0, "struttura_star": 6.0, "esempi_concreti": 5.0},
  "stats_current": {"chiarezza": 7.5, "struttura_star": 7.0, "esempi_concreti": 8.0},
  "paura_attuale": "Restare senza parole",
  "metrica_paura": "chiarezza",
  "paura_superata": true,
  "prossime_paure": [
    "Non sembrare abbastanza preparato tecnicamente",
    "Fare una figuraccia con il recruiter",
    "Non saper parlare di me stesso"
  ],
  "badges": ["…", "…"],
  "improvements": ["…", "…"],
  "final_tip": "…"
}
```


### 6.4 Perché il report ha campi in due lingue

Le chiavi già usate dal frontend (`overall_previous`, `overall_current`, `stats_previous`, `stats_current`, `badges`, `improvements`, `final_tip`) restano in inglese per non rompere il contratto. I campi nuovi della gamification sono in italiano: `paura_attuale`, `metrica_paura`, `paura_superata`, `prossime_paure`. Il vecchio nome `fear_overcome` (usato nel recap storico) è **superato**: il frontend deve usare `paura_superata`.

### 6.5 Validazione e codici HTTP

- Profilo: ogni valore è confrontato con la lista ufficiale; un valore fuori lista → `422` (Pydantic), **prima** dell'endpoint.
- Corso: `get_dettagli_corso` solleva `CorsoNonValidoError(ValueError)` → `422`; il `400` negli endpoint è difensivo, per quando l'eccezione non passa da Pydantic.
- Valutazioni: 3 voti con `ge=0, le=10`, lista `min_length=1`.
- Turni: `TurnResponse.visemes` con `default_factory`, `gesture` con default `"explain"`.
- Errori LLM: `503` con messaggio "Servizio LLM non disponibile, riprova.".
- Errori interni: `500` generico; il dettaglio va nei log, mai al client.

### 6.6 Il contratto `/turn` è pronto, l'endpoint no

`Turno`, `TurnRequest` e `TurnResponse` sono definiti in `routers/sessions.py` e testati, ma nessun router espone `/turn`. La scelta è deliberata: l'endpoint tocca Evaluation, DB e TTS insieme, quindi è stato assegnato a Collega 2 con il contratto già congelato. Di conseguenza, oggi l'**Evaluator non è raggiungibile via API**: esiste come funzione (`valuta_risposta`) e nei test, ma nessun endpoint lo chiama. Finché manca `/turn`, `/end` accetta le valutazioni dal client: è l'ultimo pezzo "fidato" del sistema.

### 6.7 Test: la strategia

- Un'unica suite offline (`test_enorme.py`) con LLM mockato: copre logica, casi limite ed errori.
- Tre test live separati, attivati con `--live`: dimostrano che il collegamento reale funziona (domanda, valutazione severa, report).
- Test dedicati più piccoli (`test_reporter.py`, `test_sistema.py`, ...) per debug mirato.
- Le asserzioni usano frammenti distintivi, mai singole lettere (regola 5.8 di [FUNZIONAMENTO.md](FUNZIONAMENTO.md#58-un-test-che-asserisce-una-lettera-non-prova-niente)).
- I test dei documenti controllano che i 5 file contengano i concetti chiave: se si aggiorna un documento, quei test restano la rete di sicurezza.

### 6.8 Git e documenti

- Si lavora su branch (`feature/genai-core` per il ciclo GenAI), PR verso `main`, review.
- `.env` e `venv/` non entrano mai in git.
- I documenti sono stati consolidati: un file per funzione (panoramica, didattica, diario, task) invece di un file per sessione di lavoro. Meno duplicazione, meno rischio che uno resti indietro.

### 6.9 Diagnosi dei prompt (rimandata)

Analisi in sola lettura del 20/11: i prompt funzionano, ma hanno quattro difetti concreti. **Nessuna modifica applicata**: il piano è stato rimandato su richiesta dell'utente.

| # | Problema | Evidenza |
|---|---|---|
| 1 | **Evaluator senza rubrica**: le fasce 1-10 non sono definite, solo "risposta povera → 1-3" | `agenti/evaluator.py`, prompt; il test live accetta `media <= 6` mentre il prompt chiede 1-3 |
| 2 | **Interviewer senza numero di domanda né copertura dei temi**: non sa a che punto è il colloquio e può insistere su un solo tema | `agenti/interviewer.py`, `user_prompt` |
| 3 | **Reporter senza limiti di lunghezza** per `badges`, `improvements`, `final_tip` | `agenti/reporter.py`, prompt |
| 4 | **`test_int_eval.py` senza assert**: stampa soltanto, quindi non è un test | `test_int_eval.py`, funzione `main` |

Piano proposto e non eseguito, in tre commit separati: rubrica dell'Evaluator (fasce esplicite + soglia coerente col test live), Interviewer con numero di domanda e temi coperti, limiti di lunghezza nel Reporter. Il quarto punto va deciso a parte: o `test_int_eval.py` diventa un test con assert, o si rinomina `demo_int_eval.py` aggiornando i riferimenti.

---

## 7. Test: risultati

| Test | Esito | Note |
|---|---|---|
| `python test_enorme.py` | ✅ **88/88** | offline, mock LLM, nessuna quota |
| `python test_enorme.py --live` | ✅ **91/91** | 3 chiamate reali: domanda, evaluator 4/1/1, reporter 80.0 |
| `python test_reporter.py` | ✅ | 7.4 → non superata; 7.5 → superata; metrica specifica; sticky; reset |
| `python test_sistema.py` | ✅ | corsi, LLM, evaluator (FreeLLMAPI offline → Gemini Lite) |
| `python test_interviewer.py` | ✅ | due domande, con e senza CV |
| `python test_int_eval.py` | ✅ | Interviewer → Evaluator; risposta povera → 4/3/3 |
| `python test_api_full.py` | ✅ | `/start` 200; 26.6 → `paura_superata: false`; 82.0 → `true` con 3 paure; `metrica_paura: chiarezza` |
| TestClient offline | ✅ | profilo invalido 422; corso invalido 422; voto 11 → 422; lista vuota → 422; CORS 200 |
| CV endpoint | ✅ | tipo non PDF → 415; PDF senza testo → 400 |

Il **88/88 offline è verificato sul codice attuale**; il **91/91 live** è l'ultima esecuzione registrata e dipende da chiavi e quota, quindi va rilanciato quando serve dimostrarlo.

---

## 8. Prima / dopo in una tabella

| Area | Prima (`3a15197`) | Ora (`main`) |
|---|---|---|
| **Profilo** | Stringhe libere e valori di esempio | Le 3 liste ufficiali in `profilo.py`, validazione stretta (422) |
| **Paura** | Solo idea nel recap | Metrica specifica ≥ 7.5, sticky, reset se cambia paura, `metrica_paura`, `prossime_paure` |
| **Colloquio** | L'Interviewer faceva sempre "la prima domanda" | `cronologia`, nessuna ripetizione, temperatura 0.8; modelli `TurnRequest`/`TurnResponse` pronti |
| **Evaluator** | Prompt permissivo | Risposte vuote/fuori tema → 1-3; voti sempre 1-10 |
| **LLM** | Solo Lite, senza retry | Catena automatica FreeLLMAPI → Lite → DeepSeek, 2 retry su Gemini, timeout per provider, JSON robusto |
| **API** | Nessun CORS, `turnId` fisso, 503 per corso errato, errori interni esposti | CORS, `turnId` univoco, 422 per input errato, 400/422/503/500 generici |
| **CV** | Nessun endpoint | `POST /api/cv/parse`: PDF max 5 MB → `cv_json` con `pypdf` + LLM |
| **Dipendenze** | `requirements.txt` in UTF-16, mancava `google-genai` | UTF-8, `google-genai`, `pypdf`, `python-multipart` |
| **Test** | Firme vecchie, test rotti | Test allineati, `test_reporter.py` e `test_enorme.py` (88 offline / 91 live) |
| **Documenti** | README e funzionamento vecchi, 9 file sparsi | 5 file stabili: `AGENTS.md`, README, FUNZIONAMENTO, RECAP, TODO |

---

## 9. Come riprendere in una nuova chat

**Ordine di lettura:** `README.md` → `FUNZIONAMENTO.md` → `RECAP.md` → `TODO.md`.

**Comandi:**

```powershell
cd C:\Users\gabri\OneDrive\Desktop\HireMate
.\venv\Scripts\Activate.ps1

python test_enorme.py          # 88 test offline, mock LLM
python test_enorme.py --live   # 91 test (3 chiamate reali)

python main.py                 # server su http://127.0.0.1:8000/docs

git status
git log --oneline -5
```

**Regole:**

- Non modificare `.env`, non stampare chiavi.
- Non committare su `main`: branch + PR.
- Prima di modificare: leggere il file e questo recap.
- Dopo ogni modifica: test offline, poi eventualmente live.
- Se Gemini dà 503: aspettare e riprovare; i test offline restano validi.

**Messaggio pronto per aprire una nuova chat:**

> Continuo il progetto HireMate. Leggi in ordine `README.md`, `FUNZIONAMENTO.md`, `RECAP.md` e `TODO.md`. Non modificare `.env`, non stampare chiavi, non committare su `main`. Poi riassumimi lo stato e il prossimo task.

---

## 10. Mappa dei documenti assorbiti

Nessun contenuto è andato perso: i 9 `.md` precedenti sono stati distribuiti così.

| Vecchio file | Dove è finito |
|---|---|
| `funzionamento.md` | `FUNZIONAMENTO.md` §2 (file per file), §3 (flusso), §4 (concetti), §7-8 (pitch e Q&A) |
| `regole_di_lettura_del_codice.md` | `FUNZIONAMENTO.md` §5 (le 13 regole, aggiornate al merge) |
| `guida_test_e_cambiamenti.md` | `FUNZIONAMENTO.md` §6 (test, mock vs live), §7 (pitch); `README.md` (comandi); `RECAP.md` §4, §8 |
| `piano_lavoro_18_11.md` | `RECAP.md` §5 (errori), §6 (decisioni), §7 (test); `TODO.md` §8 (workflow) |
| `recap_18_11.md` (storico) | `RECAP.md` §1, §4 e §6 (stato e roadmap storica) e `TODO.md` (attività ancora aperte) |
| `recap_18_11_2.md` | `RECAP.md` §3, §4, §7 |
| `cambiamenti_ultimo_push.md` | `RECAP.md` §4 (changelog file per file) |
| `handoff.md` | `RECAP.md` §1, §9; `README.md` (stato attuale) |
| `split_lavoro.md` | `TODO.md` (tutto: task, contratto, matrice, regole, milestone, rischi, demo) |

---

## 11. Da fare adesso

Il dettaglio è in [TODO.md](TODO.md). In breve, in quest'ordine:

1. **CI su GitHub Actions** (`test.yml`: push e PR, Python 3.14 con fallback 3.13, `pip install -r requirements.txt`, `python test_enorme.py`) e poi **protezione di `main`** con il check obbligatorio: è ciò che rende vera la regola "solo a test verdi".
2. **Hardening degli input**: `max_length` su `trascrizione`, `domanda` e `cv_json` nei modelli di `routers/sessions.py`, con test dedicati.
3. **Igiene del repository**: `.gitattributes` (`* text=auto`) e `.editorconfig` UTF-8, per chiudere i due incidenti già visti (freeze UTF-16, fine riga incoerenti).
4. **Qualità dei test**: `test_int_eval.py` senza assert e `test_api_full.py` che esce 0 anche quando il server non è attivo.
5. **Baseline di demo**: server avviato, `test_api_full.py`, `/docs`, CORS e i codici 422/415/503 salvati come output attesi.
6. **Handoff del contratto al team AR/VR**: `sessionId`, `audioUrl`, `visemi {"time": ms, "visemeId": int}`, `metrica_paura`, `prossime_paure`.
7. **Integrazione** di Collega 2 (`/turn`, TTS) e Collega 1 (DB, auth, CV), poi frontend AR/VR, con review e merge a test verdi.
8. **Prompt tuning** (vedi §6.9): rimandato, non è bloccante.

Bloccato e da non iniziare ora: il punto 7 dipende dalle PR dei colleghi.
