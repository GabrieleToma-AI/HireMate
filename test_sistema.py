import asyncio
import sys

from corsi import get_dettagli_corso
from agenti.evaluator import valuta_risposta
from agenti.llm import chiama_llm_json

sys.stdout.reconfigure(encoding="utf-8")

PROFILO = {
    "ansia_principale": "Non sembrare abbastanza preparato tecnicamente",
    "stile_gestione_problemi": "Faccio ricerche infinite finché non trovo la soluzione",
    "timore_critico": "Non ho saputo spiegare bene le mie competenze",
}


async def run_corsi():
    print("\n🧪 TEST 1: Database Corsi")
    corso = "SOC Analyst"
    dettagli = get_dettagli_corso(corso)
    assert isinstance(dettagli, dict), "I dettagli devono essere un dizionario"
    assert "materie" in dettagli, "Manca la chiave 'materie'"
    assert len(dettagli["materie"]) > 0, "La lista delle materie è vuota"
    print(f"   ✅ Trovato corso: {corso}")
    print(f"   ✅ Materie: {', '.join(dettagli['materie'][:3])}...")

    try:
        get_dettagli_corso("Corso Inventato")
    except ValueError:
        print("   ✅ Gestione errore corso inesistente: OK")
    else:
        raise AssertionError("Doveva lanciare ValueError per corso inesistente")


async def run_llm():
    print("\n🧪 TEST 2: Chiamata LLM (FreeLLMAPI -> Gemini Fallback)")
    prompt_system = "Rispondi solo con un JSON contenente la chiave 'messaggio' e valore 'ciao'."
    prompt_user = "Esegui."

    risultato = await chiama_llm_json(prompt_system, prompt_user, temperature=0.1)

    assert isinstance(risultato, dict), "La risposta deve essere un dizionario"
    assert "messaggio" in risultato, "Manca la chiave 'messaggio' nel JSON"
    print(f"   ✅ Risposta LLM ricevuta: {risultato}")


async def run_evaluator():
    print("\n🧪 TEST 3: Evaluator Agent")
    risultato = await valuta_risposta(
        corso="Full Stack Developer",
        profilo_soft_skill=PROFILO,
        domanda="Raccontami di un progetto in team.",
        trascrizione=(
            "eh abbiamo fatto un sito web, io ho fatto il frontend e lui il backend, "
            "è andata bene"
        ),
    )

    for chiave in ("chiarezza", "struttura_star", "esempi_concreti", "suggerimento", "better_answer"):
        assert chiave in risultato, f"Manca '{chiave}'"

    assert isinstance(risultato["chiarezza"], int), "Il voto deve essere un intero"
    assert 1 <= risultato["chiarezza"] <= 10, "Il voto deve essere tra 1 e 10"

    print("   ✅ Struttura JSON corretta.")
    print(
        f"   ✅ Voti: Chiarezza={risultato['chiarezza']}, "
        f"STAR={risultato['struttura_star']}, Esempi={risultato['esempi_concreti']}"
    )
    print(f"   ✅ Suggerimento generato: '{risultato['suggerimento'][:50]}...'")


async def main():
    print("🚀 AVVIO SUITE DI TEST HIREMATE")
    print("=" * 40)

    for test in (run_corsi, run_llm, run_evaluator):
        try:
            await test()
        except Exception as e:
            print(f"   ❌ FALLITO: {e}")
            return 1

    print("\n" + "=" * 40)
    print("🏁 SUITE DI TEST COMPLETATA")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
