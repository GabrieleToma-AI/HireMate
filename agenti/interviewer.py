import json
from agenti.llm import chiama_llm_json, LLMError
from corsi import get_dettagli_corso

async def genera_domanda(
    corso: str, 
    paura_colloquio: str,
    reazione_problema: str,
    paura_fallimento: str,
    cv_json: dict | None = None
) -> str:
    """
    Genera una domanda HR basata sul corso, sul profilo psicologico e sul CV.
    """
    try:
        dettagli_corso = get_dettagli_corso(corso)
    except ValueError as e:
        raise LLMError(f"Impossibile generare la domanda: {e}")
        
    materie = ", ".join(dettagli_corso["materie"])
    focus_hr = dettagli_corso["focus_hr"]

    contesto_cv = ""
    if cv_json:
        contesto_cv = f"\nIl candidato ha allegato un CV con queste esperienze: {json.dumps(cv_json, ensure_ascii=False)}. Usa queste informazioni per personalizzare la domanda."

    system_prompt = f"""
<role>
Sei un HR Manager esperto che conduce un colloquio per un ruolo IT Junior.
</role>

<context>
Stai intervistando uno studente del corso ITS: {corso}.
Le materie tecniche che ha studiato sono: {materie}.
Il focus soft skills di questo corso è: {focus_hr}.
Profilo psicologico dello studente:
- Paura principale del colloquio: {paura_colloquio}
- Reazione di fronte a un problema: {reazione_problema}
- Paura principale di fallire: {paura_fallimento}
{contesto_cv}
</context>

<instructions>
1. Genera UNA sola domanda alla volta, in italiano.
2. NON fare domande tecniche. Fai domande SOFT (comportamentali).
3. Calibra la domanda in base alle paure dello studente:
   - Se ha paura di "restare senza parole" o "non sapersi spiegare", chiedi un esempio concreto per aiutarlo a strutturare il pensiero.
   - Se ha paura di "essere troppo in ansia", usa un tono rassicurante e domande chiare.
   - Se ha paura di "non avere esperienza tecnica", chiedi di raccontare un progetto scolastico o personale.
   - Se "si blocca di fronte ai problemi", chiedi come ha superato un momento di blocco.
4. Lega la domanda alle materie studiate o al CV.
</instructions>

<output_format>
Rispondi solo con un oggetto JSON valido contenente la chiave "domanda".
{{
  "domanda": "Testo della domanda qui"
}}
</output_format>
"""

    user_prompt = "Genera la prima domanda del colloquio."

    risultato = await chiama_llm_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.7
    )
    
    return risultato.get("domanda", "Mi scuso, non sono riuscito a generare una domanda.")