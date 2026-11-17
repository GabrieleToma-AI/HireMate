import asyncio
import json
from corsi import get_dettagli_corso
from agenti.evaluator import valuta_risposta
from agenti.llm import chiama_llm_json

async def test_corsi():
    print("\n🧪 TEST 1: Database Corsi")
    try:
        corso = "SOC Analyst"
        dettagli = get_dettagli_corso(corso)
        assert isinstance(dettagli, dict), "I dettagli devono essere un dizionario"
        assert "materie" in dettagli, "Manca la chiave 'materie'"
        assert len(dettagli["materie"]) > 0, "La lista delle materie è vuota"
        print(f"   ✅ Trovato corso: {corso}")
        print(f"   ✅ Materie: {', '.join(dettagli['materie'][:3])}...")
        
        # Test errore
        try:
            get_dettagli_corso("Corso Inventato")
            print("   ❌ ERRORE: Doveva lanciare ValueError per corso inesistente")
        except ValueError:
            print("   ✅ Gestione errore corso inesistente: OK")
            
    except Exception as e:
        print(f"   ❌ FALLITO: {e}")

async def test_llm():
    print("\n🧪 TEST 2: Chiamata LLM (FreeLLMAPI -> Gemini Fallback)")
    try:
        prompt_system = "Rispondi solo con un JSON contenente la chiave 'messaggio' e valore 'ciao'."
        prompt_user = "Esegui."
        
        risultato = await chiama_llm_json(prompt_system, prompt_user, temperature=0.1)
        
        assert isinstance(risultato, dict), "La risposta deve essere un dizionario"
        assert "messaggio" in risultato, "Manca la chiave 'messaggio' nel JSON"
        print(f"   ✅ Risposta LLM ricevuta: {risultato}")
    except Exception as e:
        print(f"   ❌ FALLITO: {e}")

async def test_evaluator():
    print("\n🧪 TEST 3: Evaluator Agent")
    try:
        risultato = await valuta_risposta(
            corso="Full Stack Developer",
            soft_skill="Lavoro di squadra",
            domanda="Raccontami di un progetto in team.",
            trascrizione="eh abbiamo fatto un sito web, io ho fatto il frontend e lui il backend, è andata bene"
        )
        
        # Verifica struttura JSON
        assert "chiarezza" in risultato, "Manca 'chiarezza'"
        assert "struttura_star" in risultato, "Manca 'struttura_star'"
        assert "esempi_concreti" in risultato, "Manca 'esempi_concreti'"
        assert "suggerimento" in risultato, "Manca 'suggerimento'"
        assert "better_answer" in risultato, "Manca 'better_answer'"
        
        # Verifica tipi di dati
        assert isinstance(risultato["chiarezza"], int), "Il voto deve essere un intero"
        
        print("   ✅ Struttura JSON corretta.")
        print(f"   ✅ Voti: Chiarezza={risultato['chiarezza']}, STAR={risultato['struttura_star']}, Esempi={risultato['esempi_concreti']}")
        print(f"   ✅ Suggerimento generato: '{risultato['suggerimento'][:50]}...'")
    except Exception as e:
        print(f"   ❌ FALLITO: {e}")

async def main():
    print("🚀 AVVIO SUITE DI TEST HIREMATE")
    print("=" * 40)
    await test_corsi()
    await test_llm()
    await test_evaluator()
    print("\n" + "=" * 40)
    print("🏁 SUITE DI TEST COMPLETATA")

if __name__ == "__main__":
    asyncio.run(main())