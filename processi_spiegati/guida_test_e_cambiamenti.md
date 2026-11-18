# Guida: capire e spiegare il test enorme

Questa guida serve a te, per lanciare `test_enorme.py`, capire cosa stai testando e spiegarlo ai compagni e al professore.

---

## 1. In 30 secondi

- `test_enorme.py` è una suite di **88 test automatici offline**: non chiama Gemini, non consuma quota, dura pochi secondi.
- Con `--live` aggiunge **3 chiamate vere** a Gemini Lite e arriva a **91 test**.
- L'ultimo push su GitHub è `origin/main` = `3a15197`.
- Le novità sono sul branch **`feature/genai-core`**, con i commit `b27e44c`, `0c0d192`, `26226f1` (e questo documento).
- Rispetto all'ultimo push sono cambiati **26 file**: 10 nuovi e 16 modificati.

---

## 2. Come lo eseguo

Apri PowerShell nella cartella del progetto:

```powershell
cd C:\Users\gabri\OneDrive\Desktop\HireMate
.\venv\Scripts\Activate.ps1
```

Poi:

```powershell
python test_enorme.py          # 88 test offline
python test_enorme.py --live   # 91 test (3 chiamate reali a Gemini Lite)
```

Output atteso (offline):

```text
TOTALE: 88   PASSATI: 88   FALLITI: 0
🎉 TUTTI I TEST SONO PASSATI
```

Output atteso (live):

```text
TOTALE: 91   PASSATI: 91   FALLITI: 0
```

Se un test fallisce:

- l'output mostra `❌ nome del test -> errore`;
- in fondo c'è il **traceback** con il file e la riga;
- i test offline non dipendono da Internet: un fallimento è quasi sempre un bug vero o un test da aggiornare;
- i test live possono fallire per `503`/quota: aspetta qualche minuto e rilancia.

---

## 3. Cosa testa, sezione per sezione

| Sezione | Cosa verifica | Esempio concreto | Perché conta |
|---|---|---|---|
| **1. Profilo e metriche** | Le 4 paure, i 4 stili, i 4 timori, la mappa paura → metrica, soglia 7.5 e validazione stretta | `"Paura inventata"` → `422` | Se il frontend manda un valore diverso, il backend non lo accetta |
| **2. Corsi** | 14 corsi completi; corso inesistente → `CorsoNonValidoError` | `SOC Analyst` esiste, `Corso Inventato` no | Evita domande su corsi inesistenti |
| **3. LLM** | JSON, code fence, retry 2 su `503/429/timeout`, nessun retry su `400`, fallback FreeLLMAPI → Gemini | 2 errori 503 + 1 successo = 3 tentativi | Il servizio non cade al primo errore temporaneo |
| **4. Interviewer** | Prima domanda, `cronologia`, nessuna ripetizione, CV nel prompt, temperatura 0.8 | con `D1/R1` la domanda successiva tiene conto della risposta | Senza memoria il colloquio non è realistico |
| **5. Evaluator** | Voti sempre 1-10, campi mancanti, prompt severo, voti come stringhe | `0 → 1`, `11 → 10` | L'LLM a volte sfora: il codice lo corregge |
| **6. Reporter** | Overall, stats precedenti, sticky, reset, 3 opzioni, metrica che batte l'overall, soglia 7.4/7.5 | chiarezza 7.5 con overall basso → paura superata | È la regola nuova: conta la competenza specifica |
| **7. Modelli e API** | Pydantic, `TurnRequest`/`TurnResponse`, `/start`, `/end`, `422/503/500`, `turnId` univoco, OpenAPI, CORS | profilo invalido → 422; LLM giù → 503 | Il frontend riceve errori chiari, non crash |
| **8. CV** | PDF → testo → JSON, PDF vuoto/corrotto, limite 5 MB, endpoint 200/415/400/413/503/500 | PDF valido → `{"cv_json": ...}` | Il CV non deve far crashare il server |
| **9. Config e documenti** | `requirements.txt` UTF-8 e dipendenze, `.env.example`, `.gitignore`, README, funzionamento, recap, piano, input | niente `google-generativeai`, niente Gemini 3.8 | Il progetto si installa e i documenti sono allineati |
| **10. LIVE** (solo `--live`) | Gemini vero: domanda reale, evaluator severo, reporter con LLM | risposta povera → 4/1/1 | Dimostra che il collegamento con l'LLM funziona davvero |

---

## 4. Mock vs live: la spiegazione semplice

Immagina un'auto:

- **Test offline = crash test con il manichino.** Proviamo tutti gli urti possibili senza rischiare persone vere. Il manichino è il "finto LLM": simuliamo `503`, timeout, JSON rotto, voti sballati. Velocissimo, gratis, ripetibile.
- **Test live = giro su strada con l'auto vera.** Facciamo 3 chiamate reali a Gemini Lite per verificare che il motore sia collegato e che l'Evaluator non premi una risposta povera.

Servono entrambi: il crash test non dimostra che l'auto parte; il giro su strada non può simulare 88 incidenti diversi.

---

## 5. Cosa è cambiato dall'ultimo push (`3a15197`)

| Area | Prima (ultimo push) | Ora (branch `feature/genai-core`) |
|---|---|---|
| **Profilo** | Stringhe libere e valori di esempio | Le 3 liste ufficiali in `profilo.py`, validazione stretta (422) |
| **Paura** | Solo idea nel recap | Metrica specifica ≥ 7.5, sticky, reset se cambia paura, `metrica_paura`, `prossime_paure` (3 opzioni) |
| **Colloquio** | L'Interviewer faceva sempre "la prima domanda" | `cronologia`, nessuna ripetizione, temperatura 0.8; modelli `TurnRequest`/`TurnResponse` pronti |
| **Evaluator** | Prompt permissivo | Risposte vuote/fuori tema → 1-3; voti sempre 1-10 |
| **LLM** | Solo Lite, senza retry | Lite unico, 2 retry su 503/429/timeout, timeout, JSON robusto |
| **API** | Nessun CORS, `turnId` fisso, 503 per corso errato, errori interni esposti | CORS, `turnId` univoco, 422 per input errato, 400/422/503/500 generici |
| **CV** | Nessun endpoint | `POST /api/cv/parse`: PDF max 5 MB → `cv_json` con `pypdf` + LLM |
| **Dipendenze** | `requirements.txt` in UTF-16, mancava `google-genai` | UTF-8, `google-genai`, `pypdf`, `python-multipart` |
| **Test** | Firme vecchie, test rotti | Test allineati, `test_reporter.py` e `test_enorme.py` (88 offline / 91 live) |
| **Documenti** | README/funzionamento vecchi | README, funzionamento, recap, piano, changelog e questa guida |

Il dettaglio **file per file** è in `processi_spiegati/cambiamenti_ultimo_push.md`.

---

## 6. Come spiegarlo ai compagni in 2 minuti

> «HireMate è un simulatore di colloqui. Il backend prende il profilo dello studente, genera domande, valuta le risposte e produce un report.
>
> Prima il progetto aveva tre problemi: i test non giravano più, la paura veniva superata con una media generale (quindi una competenza debole poteva nascondersi), e l'Interviewer non ricordava le domande precedenti.
>
> Oggi: le 3 risposte della profilazione sono validate contro liste ufficiali; la paura si supera solo quando **la metrica specifica** arriva a 7.5/10 (es. chiarezza per "restare senza parole"); una volta superata resta superata, ma se cambi paura riparte; l'Interviewer riceve la cronologia e non ripete; l'Evaluator dà 1-3 alle risposte povere; il backend ha CORS, errori HTTP chiari e un endpoint per il CV in PDF.
>
> Il test enorme verifica 88 casi offline in pochi secondi, senza consumare quota. Con `--live` fa anche 3 chiamate vere a Gemini Lite: una domanda, una valutazione severa (4/1/1 su una risposta povera) e un report (80/100). I test offline servono per la logica e i casi limite; quelli live per dimostrare che l'LLM è davvero collegato.
>
> Il lavoro è sul branch `feature/genai-core`; l'ultimo push è `3a15197` e non abbiamo ancora pushato, così main resta stabile.»

---

## 7. Domande probabili e risposte

**Perché 7.5 e non 8?**
7.5/10 è una soglia di padronanza: non basta la sufficienza, ma non è nemmeno impossibile. È una costante in `profilo.py`, si cambia in un punto.

**Perché la metrica specifica e non l'overall?**
Perché l'overall può essere alto grazie ad altre metriche. Se la paura è "restare senza parole", la competenza da guardare è la chiarezza. Lo dimostra il test: chiarezza 7.5 con STAR ed esempi a 1 → paura superata, overall basso.

**Cos'è lo "sticky"?**
Una volta superata per quella paura, resta superata anche se in una sessione successiva il voto scende. Se cambia la paura, riparte da zero: la nuova paura non è ancora stata affrontata.

**Perché serve `paura_attuale`?**
Per sapere a quale paura si riferisce il flag. Senza, dopo un cambio paura la sticky farebbe risultare già superata anche la nuova.

**Perché i test offline?**
Per verificare la logica e forzare casi difficili (503, timeout, JSON rotto, PDF corrotto) in modo veloce e deterministico, senza quota. I test live verificano il modello vero.

**Cosa manca ancora?**
L'endpoint `/turn` (Collega 2), Supabase/auth (Collega 1), TTS/visemi (Collega 2), frontend (team AR/VR). Finché `/turn` non c'è, `/end` accetta le valutazioni dal client: è temporaneo.

**Perché un branch e non main?**
Per non rompere main e poter fare merge/PR dopo la revisione di Collega 2.

**Cosa succede se Gemini è giù?**
Il wrapper fa 2 retry su 503/429/timeout; se falliscono, l'API risponde 503 con un messaggio chiaro. I test offline restano verdi.

---

## 8. Comandi utili

```powershell
# test
python test_enorme.py
python test_enorme.py --live

# cosa è cambiato
git log --oneline origin/main..HEAD
git diff --stat origin/main..HEAD

# stato
git status
git branch --show-current

# pubblicare (quando decidi)
git push -u origin feature/genai-core
```

---

## 9. Stato git

- **Ultimo push:** `origin/main` = `3a15197`.
- **Branch:** `feature/genai-core`.
- **Commit:** `b27e44c` (backend), `0c0d192` (test/changelog), `26226f1` (live/docs), più il commit di questa guida.
- **Push:** non ancora fatto; `main` non è stato toccato.
- **File vs ultimo push:** 26 (10 nuovi, 16 modificati).
- `.env` e `venv/` non sono tracciati.
