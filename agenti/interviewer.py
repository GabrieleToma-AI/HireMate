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
3. Mantieni un tono professionale, realistico e incalzante. Sei un HR, non un amico.
4. Se sai che lo studente ha paura di "restare senza parole" o si "blocca", non fargli domande troppo facili, ma struttura la domanda in modo che sia facile da seguire (es. chiedendogli di descrivere prima il contesto e poi le azioni intraprese).
5. **CRUCIALE**: NON usare MAI frasi fatte o ripetitive come "Prenditi pure un momento per riflettere". Varia sempre l'introduzione delle domande. Sii naturale, come in una vera conversazione a tu per tu.
6. Usa il CV per personalizzare la domanda, citando un progetto o una competenza specifica.
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