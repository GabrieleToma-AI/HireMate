# Regole di lettura del codice

> File di metodo, non di stato. Serve a mantenere continuità tra una chat e l'altra: come si legge HireMate, come si interpretano le domande, come si ricava una regola da una modifica fatta a mano.
>
> Va letto **all'inizio di ogni chat**, subito dopo `handoff.md`.

---

## 1. Una categoria vaga si definisce per estensione

Quando in un prompt o in una validazione compare una parola astratta, il modello (o il codice) la interpreta in modo incoerente. Si sostituisce la parola con i **casi concreti** che deve coprire.

Esempi reali dal progetto:

- `agenti/cv_parser.py` — da *"linguaggi, strumenti, tecnologie"* a *"linguaggi di programmazione, strumenti informatici utilizzati, tecnologie"*; *"progetti"* → *"…compresi progetti realizzati"*. Motivo: "strumenti" si tirava dentro qualsiasi cosa (anche "teamwork"), e "progetti" rischiava di far scartare i lavori personali.
- `agenti/evaluator.py` — non *"valuta severamente le risposte povere"* ma *"vuota, incoerente, fuori tema o senza esempi concreti → 1-3"*. La categoria "povera" è sostituita dai quattro casi che la compongono.

**Come si applica:** ogni volta che si scrive o si rivede un prompt, una soglia o una validazione, si chiede *"quale parola qui è interpretabile in due modi?"* e la si esplicita con esempi.

---

## 2. Protocollo di interpretazione

Per ogni domanda o modifica dell'utente si ricostruisce, in tre punti:

1. **cosa** ha chiesto o cambiato;
2. **quale dubbio** rivela (di solito un'ambiguità che codice o prompt non risolvono);
3. **la regola generale** che se ne ricava.

Se la deduzione è sbagliata, l'utente la corregge. **La motivazione dichiarata prevale sempre sulla deduzione**, e la correzione va registrata qui.

---

## 3. Stile delle risposte

- Solo la risposta diretta, breve, senza contorno.
- **Sempre un esempio concreto** che chiarisca l'affermazione.
- Niente preamboli, niente riepiloghi di ciò che l'utente ha appena detto.

---

## 4. Fase di studio: sola lettura

Durante lo studio del codice **non si modificano file**. Le modifiche le fa l'utente di propria mano, mentre studia.

Eccezioni ammesse: creare o aggiornare documenti su richiesta esplicita; nessun intervento su codice, `.env` o `venv/`.

---

## 5. Come cresce questo file

Ogni nuova regola appresa si aggiunge qui, **con l'esempio del progetto che l'ha generata**, così resta verificabile e non si trasforma in teoria astratta.

---

## 6. L'ultima risorsa è la più affidabile e la più lenta

Catena dei provider, 19/11: **FreeLLMAPI (3s) → Gemini Lite (6s) → DeepSeek (30s, a pagamento)**.

Regola: si ordina per costo e affidabilità **crescenti**, e si dà più tempo all'ultima, perché è quella che *deve* riuscire. I primi devono liberare il turno in fretta: l'utente è in attesa davanti a una domanda di colloquio.

Esempio: se i tre timeout fossero uguali, un servizio locale spento farebbe attendere 30s prima di arrivare al provider che funziona. Il test lo blinda: `TIMEOUT_FREELLMAPI <= 5`, `TIMEOUT_GEMINI <= 10`, `TIMEOUT_DEEPSEEK >= TIMEOUT_GEMINI`.

---

## 7. Gli errori si accumulano, non si sovrascrivono

Prima: `LLMError(f"... Errore: {ultimo_errore}")` — si perdeva il guasto di FreeLLMAPI, che è il primo della catena e quindi il più probabile.

Ora: gli errori si raccolgono in lista e si uniscono (`" | ".join`).

Esempio: un guasto del solo DeepSeek e uno di tutti e tre producevano lo stesso messaggio; oggi il secondo dice *quale* provider è caduto.

---

## 8. Un test che asserisce una lettera non prova niente

In `test_fallback_tutti` c'era `assert "a" in str(errore)`: `"a"` è contenuta in "f**a**llito", quindi l'asserzione era vera sempre, anche col messaggio sbagliato.

Regola: nelle asserzioni su stringhe si usano **frammenti distintivi** (es. `"free giù"`), mai singole lettere o parole comuni.

---

## 9. Un nuovo client di rete va mockato anche nei test che non lo nominano

`test_fallback` faceva patch solo di `_chiama_freellmapi` e `_chiama_gemini`. Aggiunto DeepSeek, con la chiave presente nel `.env` quei test avrebbero fatto **chiamate vere** dentro una suite che promette "nessuna quota".

Regola: quando si aggiunge un client di rete, si cerca ogni test che attraversa quella catena e lo si patcha, **anche se il test non lo cita**.

---

## 10. Il default nel codice non è la configurazione

`MODELLO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")`: se il `.env` definisce la variabile, il default **non viene mai usato**. Il default è documentazione, non verità.

Esempio (19/11): per passare a un modello della famiglia 4 sarebbe stato inutile cambiare `llm.py`, perché il `.env` fissava già `GEMINI_MODEL=gemini-3.5-flash-lite`. Prima di dire "il modello è X" si controlla il `.env`, non il codice.

Corollario: un nome di modello non si dà per buono. Si verifica con `ListModels` **e** con una `generateContent` vera sul contratto del progetto (JSON + `system_instruction`): `gemini-4.1-flash` non esiste, e dei quattro `gemini-4-*` solo `hydrogen` rispondeva con la chiave disponibile (gli altri 429 per quota).

Corollario 2: **il nome commerciale non è l'id API.** DeepSeek V4.1 Flash si chiama `deepseek-flash`; `deepseek-chat` è l'alias delle generazioni precedenti, e `deepseek-4.1-flash` non esiste. Stesso errore di `gemini-4.1-flash`: il nome leggibile del modello non è quello che va nella richiesta.

---

## 11. Un provider nuovo si verifica in quattro passi

Non basta che il codice compili: l'ordine dei controlli è quello che distingue "sembra funzionare" da "funziona".

1. **`GET /models`** con la chiave vera → l'id esiste? (`deepseek-flash` ✅, `deepseek-v4-pro` ✅)
2. **call reale** sul contratto del progetto (JSON + `system_instruction`, temperatura vera) → risponde? (2.3s, JSON pulito)
3. **errore volutamente sbagliato** (modello inesistente) → l'eccezione arriva come `LLMError` e non come eccezione grezza del client? Altrimenti la catena non la intercetta e l'API risponde 500 invece di 503.
4. **catena completa** con i primi provider forzati a fallire → il fallback arriva davvero in fondo? (FreeLLMAPI giù + Gemini giù → DeepSeek, 1.1s)

Poi la suite offline: 88/88, che deve restare tale anche con la chiave nel `.env`.

---

## 12. La sola lettura si sospende solo su richiesta esplicita

La fase di studio resta in sola lettura finché l'utente non chiede un'azione: commit e push sono ammessi **su richiesta esplicita**, mai di iniziativa, e restano confinati al branch di lavoro. `main` non si tocca e `.env` non entra in git.

Esempio (19/11): l'utente ha chiesto di committare e pushare le modifiche fino ad allora. Fatto su `feature/genai-core` in due parti — prima il codice DeepSeek, poi i documenti — con `main` fermo a `3a15197`.
