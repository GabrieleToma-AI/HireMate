import json
from agenti.llm import chiama_llm_json, LLMError

async def genera_report_finale(
    corso: str, 
    profilo_soft_skill: dict, 
    valutazioni: list[dict],
    report_precedente: dict | None = None  # <-- NUOVO PARAMETRO
) -> dict:
    
    if not valutazioni:
        raise LLMError("Nessuna valutazione disponibile per il report.")

    # 1. Calcolo delle medie della sessione ATTUALE
    media_chiarezza = sum(v.get("chiarezza", 0) for v in valutazioni) / len(valutazioni)
    media_star = sum(v.get("struttura_star", 0) for v in valutazioni) / len(valutazioni)
    media_esempi = sum(v.get("esempi_concreti", 0) for v in valutazioni) / len(valutazioni)

    # Media pesata: Chiarezza 40%, Struttura 30%, Esempi 30%
    overall_attuale = round((media_chiarezza * 0.4 + media_star * 0.3 + media_esempi * 0.3) * 10, 1)

    # 2. Gestione dei punteggi precedenti (se esistono)
        # 2. Gestione dei punteggi precedenti (se esistono)
    # Usiamo le chiavi corrette che il report genera in output
    if report_precedente and "stats_current" in report_precedente:
        stats_precedenti = report_precedente["stats_current"]
        overall_precedente = report_precedente.get("overall_current", 0.0)
    else:
        # Prima sessione in assoluto: si parte da zero
        stats_precedenti = {"chiarezza": 0.0, "struttura_star": 0.0, "esempi_concreti": 0.0}
        overall_precedente = 0.0

    ansia = profilo_soft_skill.get("ansia_principale", "")
    timore = profilo_soft_skill.get("timore_critico", "")

    # 3. Prompt per l'LLM
    system_prompt = f"""
<role>
Sei un Career Coach esperto in ambito IT. Il tuo compito è analizzare i risultati di un colloquio simulato per uno studente ITS e generare un report di feedback professionale, costruttivo e orientato al miglioramento.
</role>

<context>
Lo studente frequenta il corso ITS: {corso}.
Paura principale dello studente: {ansia}.
Timore critico: {timore}.

Ecco le medie dei voti ottenuti in QUESTA sessione:
- Chiarezza: {media_chiarezza:.1f}/10
- Struttura STAR: {media_star:.1f}/10
- Esempi Concreti: {media_esempi:.1f}/10
</context>

<instructions>
Genera un report di feedback professionale. Sii un coach severo ma giusto.
1. Estrai 2 "badges" (punti di forza): etichette positive basate sulle metriche in cui ha performato meglio.
2. Estrai 2 "improvements" (aree di miglioramento): azioni concrete per le metriche più basse.
3. Scrivi un "final_tip": un consiglio finale (massimo 2 frasi) che tenga conto delle sue paure (ansia e timore critico).
</instructions>

<output_format>
Rispondi solo con un JSON valido:
{{
  "badges": ["string", "string"],
  "improvements": ["string", "string"],
  "final_tip": "string"
}}
</output_format>
"""

    risultato_llm = await chiama_llm_json(
        system_prompt=system_prompt, 
        user_prompt="Genera il report testuale.", 
        temperature=0.4
    )

    # 4. Restituiamo i dati per l'animazione frontend
    return {
        "overall_previous": overall_precedente,
        "overall_current": overall_attuale,
        "stats_previous": stats_precedenti,
        "stats_current": {
            "chiarezza": round(media_chiarezza, 1),
            "struttura_star": round(media_star, 1),
            "esempi_concreti": round(media_esempi, 1)
        },
        "badges": risultato_llm.get("badges", []),
        "improvements": risultato_llm.get("improvements", []),
        "final_tip": risultato_llm.get("final_tip", "")
    }