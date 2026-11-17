import asyncio
from agenti.interviewer import genera_domanda

async def main():
    print("--- TEST INTERVIEWER ---")
    try:
        # Test 1: Senza CV
        domanda1 = await genera_domanda(
            corso="SOC Analyst", 
            soft_skill="Gestione dello stress"
        )
        print(f"\nDomanda (SOC Analyst):\n{domanda1}")

        # Test 2: Con CV finto
        cv_finto = {"competenze": ["Python", "Docker"], "progetti": ["Sito web scolastico"]}
        domanda2 = await genera_domanda(
            corso="Full Stack Developer", 
            soft_skill="Lavoro di squadra",
            cv_json=cv_finto
        )
        print(f"\nDomanda (Full Stack con CV):\n{domanda2}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    asyncio.run(main())