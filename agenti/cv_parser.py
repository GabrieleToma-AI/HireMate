import io

from pypdf import PdfReader

from agenti.llm import chiama_llm_json

SYSTEM_PROMPT = """
<role>
Sei un parser di CV. Estrai dal testo solo le competenze e i progetti.
</role>

<instructions>
1. Non inventare nulla: se un'informazione non c'è, lascia la lista vuota.
2. "competenze" sono linguaggi, strumenti, tecnologie e soft skill citati.
3. "progetti" sono esperienze scolastiche, personali o lavorative descritte.
4. Rispondi in italiano.
</instructions>

<output_format>
Rispondi solo con un JSON valido:
{
  "competenze": ["string"],
  "progetti": ["string"]
}
</output_format>
"""


def estrai_testo_pdf(contenuto: bytes) -> str:
    """Estrae il testo da un PDF caricato in memoria."""
    lettore = PdfReader(io.BytesIO(contenuto))
    pagine = [(pagina.extract_text() or "") for pagina in lettore.pages]
    return "\n".join(pagine).strip()


async def estrai_cv_json(contenuto: bytes) -> dict:
    """Trasforma il PDF in JSON strutturato usando il wrapper LLM."""
    testo = estrai_testo_pdf(contenuto)
    if not testo:
        raise ValueError("Il PDF non contiene testo estraibile.")

    return await chiama_llm_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=testo,
        temperature=0.2,
    )
