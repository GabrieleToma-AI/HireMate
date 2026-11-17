import json
from agenti.llm import chiama_llm_json, LLMError
from corsi import get_dettagli_corso

async def genera_domanda(
    corso: str, 
    profilo_soft_skill: dict, 
    cv_json: dict | None = None
) -> str:
    
    ansia = profilo_soft_skill.get("ansia_principale", "")
    gestione = profilo_soft_skill.get("stile_gestione_problemi", "")
    timore = profilo_soft_skill.get("timore_critico", "")
    
    try:
        dettagli_corso = get_dettagli_corso(corso)
    except ValueError as e:
        raise LLMError(f"Impossibile generare la domanda: {e}")
        
    materie = ", ".join(dettagli_corso["materie"])
    focus_hr = dettagli_corso["focus_hr"]

    contesto_cv = ""
    if cv_json:
        contesto_cv = f"\nIl candidato ha esperienze nel CV: {json.dumps(cv_json, ensure_ascii=False)}."

    system_prompt = f"""
<role>
Sei un HR Manager esperto che conduce un colloquio per un ruolo IT Junior. 
Il tuo stile è professionale, diretto e orientato ai risultati, ma sei anche un buon ascoltatore. Non sei un "orso", ma non sei nemmeno un "amico". Vuoi testare il candidato per capire se è pronto per il mondo del lavoro.
</role>

<context>
Lo studente frequenta il corso ITS: {corso}.
Materie studiate: {materie}.
Focus soft skills del corso: {focus_hr}.
Profilo psicologico dello studente (da usare per calibrare le domande, non per giudicare):
- Ansia principale: {ansia}
- Stile di gestione dei problemi: {gestione}
- Timore critico: {timore}
{contesto_cv}
</context>

<instructions>
1. Genera UNA sola domanda alla volta, in italiano.
2. Fai domande COMPORTAMENTALI (soft skills), non tecniche.
3. Mantieni un tono professionale e incalzante, ma dai allo studente il tempo di pensare.
4. Se sai che lo studente ha paura di "restare senza parole" o si "blocca", non fargli domande troppo facili, ma dagli un aggancio chiaro (es. "Prenditi un momento, poi raccontami un progetto in cui..."). Aiutalo a strutturare il pensiero.
5. Se ha paura di "non avere esperienza", chiedigli di descrivere nel dettaglio un progetto scolastico o un problema tecnico che ha risolto.
6. Usa il CV per personalizzare la domanda.
</instructions>

<output_format>
Rispondi solo con un JSON valido: {{ "domanda": "Testo" }}
</output_format>
"""

    risultato = await chiama_llm_json(
        system_prompt=system_prompt,
        user_prompt="Genera la prima domanda del colloquio.",
        temperature=0.7
    )
    return risultato.get("domanda", "Mi scuso, non sono riuscito a generare una domanda.")