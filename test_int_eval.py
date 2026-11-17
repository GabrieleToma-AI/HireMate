import asyncio
from agenti.interviewer import genera_domanda
from agenti.evaluator import valuta_risposta

async def main():
    print("🚀 AVVIO TEST DI INTEGRAZIONE (Interviewer -> Utente -> Evaluator)\n")
    print("=" * 50)

    # 1. DATI DELL'UTENTE (Simuliamo il risultato della registrazione)
    corso = "Cyber Security Specialist"
    paura_colloquio = "Restare senza parole"
    reazione_problema = "Mi blocco e mi faccio prendere dal panico"
    paura_fallimento = "Ero troppo in ansia e non riuscivo a concentrarmi"
    
    cv_finto = {
        "competenze": ["Python", "Analisi Log", "Wireshark"],
        "progetti": ["Configurazione di una rete aziendale simulata (Cisco Packet Tracer)"]
    }

    print("👤 PROFILO STUDENTE:")
    print(f"- Corso: {corso}")
    print(f"- Paura: {paura_colloquio}")
    print(f"- Reazione ai problemi: {reazione_problema}\n")

    # 2. L'INTERVIEWER GENERA LA DOMANDA
    print("🤖 L'Interviewer sta pensando alla domanda...")
    try:
        domanda = await genera_domanda(
            corso=corso,
            paura_colloquio=paura_colloquio,
            reazione_problema=reazione_problema,
            paura_fallimento=paura_fallimento,
            cv_json=cv_finto
        )
        print(f"\n❓ DOMANDA GENERATA:\n\"{domanda}\"\n")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Errore nell'Interviewer: {e}")
        return

    # 3. SIMULIAMO LA RISPOSTA DELL'UTENTE (Trascrizione vocale confusa)
    trascrizione_utente = "eh si in pratica ho fatto questo progetto a scuola con packet tracer e ho configurato la rete, però all'inizio non sapevo come fare e mi sono un po' bloccato ma poi ho chiesto al prof e ho risolto"
    print("🎤 RISPOSTA DELLO STUDENTE (trascrizione vocale):")
    print(f"\"{trascrizione_utente}\"\n")
    print("-" * 50)

    # 4. L'EVALUATOR VALUTA LA RISPOSTA
    print("⚖️ L'Evaluator sta analizzando la risposta...")
    try:
        valutazione = await valuta_risposta(
            corso=corso,
            paura_colloquio=paura_colloquio,
            reazione_problema=reazione_problema,
            paura_fallimento=paura_fallimento,
            domanda=domanda,
            trascrizione=trascrizione_utente,
            cv_json=cv_finto
        )

        print("\n📊 VALUTAZIONE OTTENUTA:")
        print(f"✅ Chiarezza: {valutazione.get('chiarezza')}/10")
        print(f"✅ Struttura STAR: {valutazione.get('struttura_star')}/10")
        print(f"✅ Esempi Concreti: {valutazione.get('esempi_concreti')}/10")
        print(f"\n💡 SUGGERIMENTO PER L'UTENTE:\n{valutazione.get('suggerimento')}")
        print(f"\n✨ BETTER ANSWER (Risposta Ideale):\n{valutazione.get('better_answer')}")

    except Exception as e:
        print(f"❌ Errore nell'Evaluator: {e}")

if __name__ == "__main__":
    asyncio.run(main())