# 🚀 HIREMATE - RECAP PROGETTO & ROADMAP

> **Nota:** documento storico. Lo stato aggiornato è in `recap_18_11_2.md`; alcune scelte qui sono superate (es. modello Gemini e nomi dei campi paura).

## 🎯 Stato dell'Arte (Cosa è stato completato dal Team GenAI)
Il backend GenAI è **completamente funzionante e testato**. L'architettura è solida, asincrona e resiliente.

### 🧠 Agenti Implementati
1. **Interviewer Agent**: Genera domande comportamentali basate su:
   - Corso ITS (14 corsi mappati in `corsi.py`).
   - Dati del CV (se presenti).
   - Profilo psicologico dello studente (ansia, gestione problemi, timore critico).
   - *Nota*: Il tono è professionale (non "troppo buono"), varia le formulazioni e non usa frasi fatte.
2. **Evaluator Agent**: Valuta la risposta su 3 metriche oggettive (Chiarezza, Struttura STAR, Esempi Concreti) restituendo un JSON con voti (1-10), suggerimenti e una *better_answer*.
3. **Reporter Agent**: 
   - Calcola l'**Overall Score** in Python puro con media pesata (Chiarezza 40%, STAR 30%, Esempi 30%).
   - Restituisce `overall_previous` e `stats_previous` (per l'animazione "+1" del frontend).
   - Genera Badge, Aree di Miglioramento e un Final Tip personalizzato sulle paure dell'utente.
   - **Nuova Feature**: Calcola `fear_overcome` (se l'utente ha superato la sua paura) e prepara le opzioni per la "prossima paura".

### 🔌 Endpoint API Implementati (FastAPI)
- `POST /api/session/start`: Riceve il profilo utente e genera la prima domanda.
- `POST /api/session/end`: Riceve l'array di valutazioni, calcola il report e restituisce i dati per l'animazione gamificata.

### 🛡️ Architettura di Rete (LLM Fallback)
- Implementato un sistema a cascata in `agenti/llm.py`: 
  1. Tenta **FreeLLMAPI** (`auto:fastest`).
  2. Fallback su **Gemini 3.5 Flash-Lite** (`gemini-3.5-flash-lite`), modello unico.
- Gestione errori nativa (Timeout, 429 Quota Exceeded, 503 Server Down) e logging dettagliato.

---

## 🚧 Prossimi Passi (Lavoro per gli altri AI Engineers)

### 👨‍💻 Collega 1 (Data, Database & CV)
*Obiettivo: Gestire i dati e l'estrazione del CV.*

1. **Supabase Setup**: 
   - Creare le tabelle `users`, `sessions`, `turns`, e `fears_history`.
   - Configurare l'SDK Python di Supabase (`supabase-py`).
2. **CV Parser Agent** (`agenti/cv_parser.py`):
   - Usare `pypdf` per estrarre il testo dal PDF.
   - Usare il wrapper `agenti/llm.py` per trasformare il testo in JSON strutturato.
3. **Profilazione Dinamica**:
   - Implementare l'endpoint `PATCH /api/users/update-fear` per permettere all'utente di cambiare la propria paura dopo averla superata (i dati gli verranno forniti dal Reporter Agent).

### 👨‍💻 Collega 2 (API Routing & Audio)
*Obiettivo: Gestire il flusso del colloquio e la voce.*

1. **Endpoint `/api/session/turn`**: 
   - Implementare la logica per ricevere la trascrizione dell'utente.
   - Chiamare l'Evaluator, salvare il turno, aggiornare la cronologia e chiamare l'Interviewer per la prossima domanda.
2. **Azure Text-to-Speech** (`agenti/tts.py`):
   - Configurare l'SDK di Azure.
   - Generare l'audio `.mp3` per le domande dell'Interviewer.
   - Generare l'array di **visemi** per il lip-sync.
   - Restituire `audioUrl` e `visemes` nel JSON dell'endpoint `/turn`.

### 🎨 Team AR/VR & Game (Frontend)
*Obiettivo: Rendere HireMate un'esperienza visiva e interattiva.*

1. **UI Game-Style**: 
   - Creare l'onboarding in stile Typeform/Tinder con Framer Motion.
   - Implementare il Push-to-Talk con Web Speech API (barra spaziatrice).
2. **Player 3D**: 
   - Configurare Three.js / React Three Fiber.
   - Sincronizzare l'avatar con `audioUrl` e `visemes` forniti dal backend.
3. **Report Animato**: 
   - Sviluppare l'animazione delle barre (Overall Score, Chiarezza, STAR, Esempi) usando `previous` e `current`.
   - Sviluppare la modale di "Promozione Paura" quando `fear_overcome` è `true`.

---
**Team GenAI è pronto per il SAL. Iniziamo l'integrazione!** 🚀