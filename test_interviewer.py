import asyncio
import sys

from agenti.interviewer import genera_domanda

sys.stdout.reconfigure(encoding="utf-8")

PROFILO = {
    "ansia_principale": "Restare senza parole",
    "stile_gestione_problemi": "Mi blocco e mi faccio prendere dal panico",
    "timore_critico": "Non ho abbastanza esperienza tecnica per il ruolo",
}


async def main():
    print("--- TEST INTERVIEWER ---")

    # Test 1: Senza CV
    domanda1 = await genera_domanda(corso="SOC Analyst", profilo_soft_skill=PROFILO)
    print(f"\nDomanda (SOC Analyst):\n{domanda1}")

    # Test 2: Con CV finto
    cv_finto = {"competenze": ["Python", "Docker"], "progetti": ["Sito web scolastico"]}
    domanda2 = await genera_domanda(
        corso="Full Stack Developer",
        profilo_soft_skill=PROFILO,
        cv_json=cv_finto,
    )
    print(f"\nDomanda (Full Stack con CV):\n{domanda2}")

    print("\n🏁 TEST INTERVIEWER COMPLETATO")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Errore: {e}")
        sys.exit(1)
