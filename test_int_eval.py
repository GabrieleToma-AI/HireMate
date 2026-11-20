import asyncio
import sys

from agenti.interviewer import genera_domanda
from agenti.evaluator import valuta_risposta

sys.stdout.reconfigure(encoding="utf-8")

PROFILO = {
    "ansia_principale": "Restare senza parole",
    "stile_gestione_problemi": "Mi blocco e mi faccio prendere dal panico",
    "timore_critico": "Ero troppo in ansia e non riuscivo a concentrarmi",
}


async def main():
    print("🚀 AVVIO TEST DI INTEGRAZIONE (Interviewer -> Utente -> Evaluator)\n")
    print("=" * 50)

    corso = "Cyber Security Specialist"
    cv_finto = {
        "competenze": ["Python", "Analisi Log", "Wireshark"],
        "progetti": ["Configurazione di una rete aziendale simulata (Cisco Packet Tracer)"],
    }

    print("👤 PROFILO STUDENTE:")
    print(f"- Corso: {corso}")
    print(f"- Paura: {PROFILO['ansia_principale']}")
    print(f"- Reazione ai problemi: {PROFILO['stile_gestione_problemi']}\n")

    # 1. L'INTERVIEWER GENERA LA DOMANDA
    print("🤖 L'Interviewer sta pensando alla domanda...")
    domanda = await genera_domanda(
        corso=corso,
        profilo_soft_skill=PROFILO,
        cv_json=cv_finto,
    )
    print(f"\n❓ DOMANDA GENERATA:\n\"{domanda}\"\n")
    print("-" * 50)

    # 2. SIMULIAMO LA RISPOSTA DELL'UTENTE (trascrizione vocale confusa)
    trascrizione_utente = (
        "eh si in pratica ho fatto questo progetto a scuola con packet tracer e ho "
        "configurato la rete, però all'inizio non sapevo come fare e mi sono un po' "
        "bloccato ma poi ho chiesto al prof e ho risolto"
    )
    print("🎤 RISPOSTA DELLO STUDENTE (trascrizione vocale):")
    print(f"\"{trascrizione_utente}\"\n")
    print("-" * 50)

    # 3. L'EVALUATOR VALUTA LA RISPOSTA
    print("⚖️ L'Evaluator sta analizzando la risposta...")
    valutazione = await valuta_risposta(
        corso=corso,
        profilo_soft_skill=PROFILO,
        domanda=domanda,
        trascrizione=trascrizione_utente,
        cv_json=cv_finto,
    )

    print("\n📊 VALUTAZIONE OTTENUTA:")
    print(f"✅ Chiarezza: {valutazione.get('chiarezza')}/10")
    print(f"✅ Struttura STAR: {valutazione.get('struttura_star')}/10")
    print(f"✅ Esempi Concreti: {valutazione.get('esempi_concreti')}/10")
    print(f"\n💡 SUGGERIMENTO PER L'UTENTE:\n{valutazione.get('suggerimento')}")
    print(f"\n✨ BETTER ANSWER (Risposta Ideale):\n{valutazione.get('better_answer')}")

    # Un test senza assert non è un test: se l'Evaluator esce dal contratto, deve fallire.
    for chiave in ("chiarezza", "struttura_star", "esempi_concreti"):
        valore = valutazione[chiave]
        assert isinstance(valore, int), f"{chiave} non è un intero: {valore!r}"
        assert 1 <= valore <= 10, f"{chiave} fuori range: {valore}"
    assert valutazione["suggerimento"].strip(), "suggerimento vuoto"
    assert valutazione["better_answer"].strip(), "better_answer vuota"

    print("\n✅ CONTRATTO DELLA VALUTAZIONE RISPETTATO")
    print("🏁 TEST COMPLETATO")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Errore: {e}")
        sys.exit(1)
