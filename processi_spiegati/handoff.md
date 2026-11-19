# Handoff — stato HireMate (18/11/2026)

> Leggere questo file all'inizio di una nuova chat. Contiene tutto il necessario per riprendere senza rileggere la conversazione precedente.

## In una frase

Backend GenAI di HireMate pronto e testato sul branch **`feature/genai-core`**: profilo validato, paura misurata sulla metrica specifica (7.5), cronologia nell'Interviewer, Evaluator severo, endpoint CV, retry LLM, test enormi. **Non è stato fatto push**; `main` è fermo all'ultimo push GitHub.

## Git

- **Ultimo push GitHub:** `origin/main` = `3a15197`.
- **Branch locale:** `feature/genai-core`.
- **Commit:** `b27e44c` (backend), `0c0d192` (test/changelog), `26226f1` (live/docs), `09496ef` (guida). Worktree pulito.
- **File vs ultimo push:** 27 (11 nuovi, 16 modificati).
- **Push:** non fatto. Comando quando deciso: `git push -u origin feature/genai-core`.
- **Mai** committare `.env` o `venv/`.

## Decisioni congelate

| Tema | Decisione |
|---|---|
| Modello LLM | Catena `FreeLLMAPI` → `gemini-3.5-flash-lite` → `deepseek-flash` (DeepSeek V4.1 Flash, a pagamento, ultima risorsa). Niente 3.8. Timeout corti sui primi due, più lungo su DeepSeek. |
| Retry | 2 retry con backoff su 503/429/timeout. |
| Paura superata | Metrica **specifica** ≥ 7.5/10, non l'overall. Sticky per la stessa paura; reset se la paura cambia. |
| Mappa paura → metrica | "Restare senza parole" → `chiarezza`; "Non sembrare abbastanza preparato tecnicamente" → `esempi_concreti`; "Fare una figuraccia con il recruiter" → `struttura_star`; "Non saper parlare di me stesso" → `chiarezza`. |
| Profilo | Validazione stretta contro le 3 liste di `profilo.py`; valore fuori lista → 422. |
| Colloquio | `cronologia` nell'Interviewer, niente ripetizioni, temperatura 0.8; `DOMANDE_PER_COLLOQUIO = 6` indicativo. |
| Turni | `TurnRequest`/`TurnResponse` pronti in `routers/sessions.py`; endpoint `/turn` a **Collega 2**. |
| Stato sessione | Fonte di verità: **Supabase** (Collega 1). Oggi `report_precedente` è un trasporto temporaneo dal client. |
| Auth | Nickname + PIN su Supabase, PIN hash **bcrypt** (Collega 1). |
| CV | `POST /api/cv/parse`: PDF max 5 MB → `cv_json` con `pypdf` + LLM. |
| Python | 3.14 (venv attuale); dipendenze dei colleghi aggiunte quando servono. |

## File da leggere, in ordine

1. `processi_spiegati/handoff.md` (questo file).
2. `processi_spiegati/regole_di_lettura_del_codice.md` — **metodo di lavoro**: stile delle risposte, come interpretare domande e modifiche, fase di sola lettura.
3. `processi_spiegati/cambiamenti_ultimo_push.md` — cosa è cambiato file per file rispetto a `3a15197`.
4. `processi_spiegati/guida_test_e_cambiamenti.md` — come eseguire il test e spiegarlo.
5. `processi_spiegati/recap_18_11_2.md` — recap dei lavori e TODO.
6. `README.md` — architettura e contratti API.
7. `processi_spiegati/piano_lavoro_18_11.md`, sezione 11 — decisioni finali.

## Comandi

```powershell
cd C:\Users\gabri\OneDrive\Desktop\HireMate
.\venv\Scripts\Activate.ps1

python test_enorme.py          # 88 test offline, mock LLM
python test_enorme.py --live   # 91 test (3 chiamate reali Gemini Lite)

python main.py                 # server su http://127.0.0.1:8000/docs
```

Test separati con Gemini: `test_sistema.py`, `test_interviewer.py`, `test_int_eval.py`, `test_api_full.py` (richiede server attivo).

## Test: stato

- `test_enorme.py` offline: **88/88**.
- `test_enorme.py --live`: **91/91** (evaluator su risposta povera: 4/1/1; reporter: 80/100).
- `test_sistema.py`, `test_interviewer.py`, `test_int_eval.py`, `test_api_full.py`: verdi nelle esecuzioni precedenti.
- FreeLLMAPI non era attivo: il fallback su Gemini Lite ha funzionato.

## Aperto / prossimi passi

- **Collega 2:** endpoint `POST /api/session/turn` usando `TurnRequest`/`TurnResponse`, Evaluator, TTS/visemi, `colloquio_terminato` dopo 6 domande.
- **Collega 1:** Supabase (`users`, `sessions`, `turns`, `fears_history`), auth nickname+PIN bcrypt, `PATCH /api/users/update-fear`, rifinitura `cv_parser.py`.
- **Team AR/VR:** card delle 4 paure, modale "Promozione Paura", report animato con `metrica_paura`.
- **DB:** `/end` legge il report precedente dal DB; si rimuove il trasporto temporaneo `report_precedente`.
- **Test reali utente scarso:** l'Evaluator è severo, ma la valutazione è server-side solo quando `/turn` salva i voti; finché `/end` accetta `valutazioni` dal client, un client scorretto può mandare voti alti.
- **Push/merge:** branch `feature/genai-core`; avvisare Collega 2 per `routers/sessions.py` e `main.py`.

## Regole per la nuova chat

- Non modificare `.env` e non stampare chiavi.
- Non fare push su `main`; si lavora su `feature/genai-core`.
- Prima di modificare: leggere il file e il changelog.
- Dopo ogni modifica: test offline, poi eventualmente live.
- Se Gemini dà 503: aspettare e riprovare; i test offline restano validi.

## Messaggio pronto per aprire la nuova chat

> Continuo il progetto HireMate. Leggi in ordine `processi_spiegati/handoff.md`, `processi_spiegati/cambiamenti_ultimo_push.md` e `processi_spiegati/guida_test_e_cambiamenti.md`. Non modificare `.env`, non stampare chiavi, non fare push su `main`. Poi riassumimi lo stato e i prossimi passi.
