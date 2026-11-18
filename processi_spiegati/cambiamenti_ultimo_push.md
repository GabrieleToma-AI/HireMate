# Cambiamenti dall'ultimo push GitHub

**Ultimo push:** `origin/main` = `3a15197` — *"feat: completato backend GenAI, aggiunto Reporter, test end-to-end e definita logica di profilazione dinamica"*.
**Stato attuale:** branch locale `feature/genai-core`, commit `b27e44c` + commit successivo con `test_enorme.py` e questo changelog. **Non è stato fatto push**: `main` non è stato toccato.

Questo documento elenca, file per file, cosa è cambiato rispetto a `origin/main`.

---

## Riepilogo

- **26 file cambiati:** 10 nuovi, 16 modificati.
- **Nuovi file:** `profilo.py`, `agenti/cv_parser.py`, `routers/cv.py`, `test_reporter.py`, `test_enorme.py`, `processi_spiegati/piano_lavoro_18_11.md`, `processi_spiegati/recap_18_11.md`, `processi_spiegati/recap_18_11_2.md`, questo changelog, `processi_spiegati/guida_test_e_cambiamenti.md`.
- **File modificati:** `.env.example`, `README.md`, `agenti/evaluator.py`, `agenti/interviewer.py`, `agenti/llm.py`, `agenti/reporter.py`, `corsi.py`, `input_registrazione.txt`, `main.py`, `processi_spiegati/funzionamento.md`, `requirements.txt`, `routers/sessions.py`, `test_api_full.py`, `test_int_eval.py`, `test_interviewer.py`, `test_sistema.py`.
- **Non tracciati da git:** `.env` (chiavi) e `venv/` (ambiente), già in `.gitignore`.

---

## File per file

| File | Stato | Cosa è cambiato rispetto a `3a15197` |
|---|---|---|
| `profilo.py` | **Nuovo** | Le 3 liste ufficiali della profilazione (`PAURE_DISPONIBILI`, `STILI_GESTIONE_PROBLEMI`, `TIMORI_CRITICI`), la mappa `METRICA_PER_PAURA` e `SOGLIA_METRICA_PAURA = 7.5`. |
| `agenti/reporter.py` | Modificato | La paura si supera sulla **metrica specifica** (non sull'overall): mappa paura → metrica, soglia 7.5, sticky per la stessa paura, reset se la paura cambia. Aggiunti `metrica_paura`, `prossime_paure` (le altre 3 paure). Rimossi `json` inutilizzato e commento duplicato. |
| `agenti/interviewer.py` | Modificato | Nuovo parametro `cronologia`: inserisce `<Cronologia>` nel prompt, non ripete le domande, usa un `user_prompt` "prima/prossima". Temperatura portata da 0.7 a 0.8. Rimosso il wrappaggio `ValueError` → `LLMError`. |
| `agenti/evaluator.py` | Modificato | Prompt più severo: risposte vuote/incoerenti/fuori tema/senza esempi → voti **1-3**. Voti sempre interi 1-10; `suggerimento` e `better_answer` sempre presenti. Rimosso import inutilizzato. |
| `agenti/llm.py` | Modificato | Solo `gemini-3.5-flash-lite` (rimosso il fallback a un secondo modello Gemini), 2 retry con backoff su 503/429/timeout, timeout configurabile, `_estrai_json` tollerante a code fence/testo extra, `raise ... from e`, rimosso `OpenAIError` inutilizzato. |
| `agenti/cv_parser.py` | **Nuovo** | Estrae il testo dal PDF con `pypdf`; PDF corrotto → `ValueError`; trasforma il testo in JSON (`competenze`, `progetti`) con il wrapper LLM. |
| `routers/cv.py` | **Nuovo** | Endpoint `POST /api/cv/parse`: accetta PDF max 5 MB, restituisce `{"cv_json": {...}}`; errori 415 (tipo), 400 (vuoto/illeggibile), 413 (troppo grande), 503 (LLM), 500 (generico). |
| `routers/sessions.py` | Modificato | Validazione **stretta** delle 3 risposte contro `profilo.py` (422); modelli `Valutazione`, `ValutazioneCompleta`, `Turno`, `TurnRequest`, `TurnResponse`; `DOMANDE_PER_COLLOQUIO = 6`; `turnId` univoco (`uuid4`); `visemes` con `default_factory`; errori 400/422/503/500 senza dettagli interni. `report_precedente` marcato temporaneo. |
| `corsi.py` | Modificato | Aggiunta `CorsoNonValidoError(ValueError)`; `get_dettagli_corso()` la solleva per un corso inesistente. |
| `main.py` | Modificato | Aggiunto `CORSMiddleware` configurabile con `CORS_ALLOW_ORIGINS`; incluso il router CV; health check aggiornato a "FreeLLMAPI / Gemini 3.5 Flash-Lite". |
| `requirements.txt` | Modificato | Riscritto in **UTF-8** (era UTF-16 con BOM), solo dipendenze dirette; aggiunti `google-genai==3.4.0`, `pypdf==7.1.1`, `python-multipart==0.0.34`; rimosso il vecchio `google-generativeai` e il dump delle dipendenze transitive. |
| `.env.example` | Modificato | `GEMINI_MODEL=gemini-3.5-flash-lite` come modello unico, rimosso `GEMINI_FALLBACK_MODEL`; aggiunti `LLM_TIMEOUT_SECONDS`, `LLM_RETRY_DELAY_SECONDS`, `CORS_ALLOW_ORIGINS` (include `localhost:3000` per Next.js). |
| `input_registrazione.txt` | Modificato | `timore_critico` allineato alla lista ufficiale: `"Non ho abbastanza esperienza tecnica per il ruolo"`. |
| `README.md` | Modificato | Riscritto: architettura attuale, liste della profilazione, regola paura per metrica, contratti `/start`/`/end`/`/turn`/`/api/cv/parse`, setup, test, divisione del lavoro, sicurezza. |
| `processi_spiegati/funzionamento.md` | Modificato | Riscritto in forma didattica: nuovi file (`profilo.py`, `cv_parser.py`, `routers/cv.py`), cronologia, regola per metrica, validazione, concetti da esame e domande del prof. |
| `processi_spiegati/piano_lavoro_18_11.md` | **Nuovo** | Piano di lavoro e decisioni: analisi iniziale, errori trovati, accordo di lavoro, dettaglio paura, decisioni finali (sezione 11), stato dei test. |
| `processi_spiegati/recap_18_11.md` | **Nuovo** | Recuperato il recap del progetto che era fuori da git; marcato come **documento storico** e corretta la parte modelli (niente 3.8). |
| `processi_spiegati/recap_18_11_2.md` | **Nuovo** | Recap dei lavori di oggi: file toccati, regola per metrica, cronologia, CV, auth/DB, test e TODO. |
| `test_reporter.py` | **Nuovo** | Test offline del Reporter: 7.4/7.5 per ogni metrica, mappa paura → metrica, sticky, reset, 3 opzioni esatte, default. |
| `test_enorme.py` | **Nuovo** | Suite enorme: 88 test offline (mock LLM) su profilo, corsi, retry/timeout/fallback, interviewer/cronologia, evaluator, reporter, modelli/API, CV, CORS e documenti; con `--live` aggiunge 3 test reali su Gemini Lite (91 totali). |
| `test_api_full.py` | Modificato | Profilo ufficiale, stampa di `paura_superata`, `metrica_paura`, `prossime_paure`; verifica le due sessioni (prima bassa, seconda alta). |
| `test_int_eval.py` | Modificato | Passa `profilo_soft_skill` (non più `paura_colloquio`/`reazione_problema`/`paura_fallimento`); exit code 1 in caso di errore; UTF-8. |
| `test_interviewer.py` | Modificato | Passa `profilo_soft_skill` (non più `soft_skill`); exit code 1; UTF-8. |
| `test_sistema.py` | Modificato | Firma aggiornata, profilo ufficiale, exit code 1 se un test fallisce, UTF-8; niente `soft_skill`. |
| `processi_spiegati/cambiamenti_ultimo_push.md` | **Nuovo** | Questo changelog. |
| `processi_spiegati/guida_test_e_cambiamenti.md` | **Nuovo** | Guida per eseguire il test, capire le sezioni, spiegare le modifiche ai compagni e rispondere alle domande. |

---

## File invariati rispetto a `3a15197`

- `.gitignore` — già esclude `venv/`, `.env`, `__pycache__/`.
- `agenti/__init__.py`, `routers/__init__.py` — file vuoti.
- `.env` — non tracciato (chiavi), invariato.
- `venv/` — ambiente locale, non tracciato.

---

## Note per il merge

- **`routers/sessions.py`** e **`main.py`** sono area di Collega 2 (API/audio): le modifiche sono su branch e vanno coordinate prima del merge.
- **`requirements.txt`** ora include `pypdf` e `python-multipart` per il CV; Collega 1 aggiungerà `supabase` e `pypdf` è già pronto.
- **`report_precedente`** è ancora un trasporto temporaneo dal client: la fonte di verità sarà Supabase.
- **`/turn`** non è ancora un endpoint: ci sono solo i modelli `TurnRequest`/`TurnResponse` pronti per Collega 2.
- **Test:** `python test_enorme.py` è offline (mock LLM) e passa con 88/88.
