import asyncio
import sys
from unittest.mock import AsyncMock, patch

from agenti.reporter import genera_report_finale

sys.stdout.reconfigure(encoding="utf-8")

PROFILO = {
    "ansia_principale": "Restare senza parole",
    "stile_gestione_problemi": "Mi blocco e mi faccio prendere dal panico",
    "timore_critico": "Non ho abbastanza esperienza tecnica per il ruolo",
}

RISPOSTA_LLM = {"badges": [], "improvements": [], "final_tip": "ok"}


def valutazioni(chiarezza: float, star: float = 8, esempi: float = 8) -> list[dict]:
    return [{
        "chiarezza": chiarezza,
        "struttura_star": star,
        "esempi_concreti": esempi,
    }]


async def genera(
    chiarezza: float,
    star: float = 8,
    esempi: float = 8,
    precedente: dict | None = None,
    profilo: dict | None = None,
) -> dict:
    with patch(
        "agenti.reporter.chiama_llm_json",
        new=AsyncMock(return_value=RISPOSTA_LLM),
    ):
        return await genera_report_finale(
            corso="SOC Analyst",
            profilo_soft_skill=profilo or PROFILO,
            valutazioni=valutazioni(chiarezza, star, esempi),
            report_precedente=precedente,
        )


async def main():
    # La paura "Restare senza parole" si misura sulla chiarezza.
    report = await genera(7.4)
    assert report["paura_superata"] is False, report
    print("✅ chiarezza 7.4 -> paura non superata")

    # 7.5 basta anche se le altre metriche sono basse (non è l'overall)
    report = await genera(7.5, star=1, esempi=1)
    assert report["paura_superata"] is True, report
    assert report["metrica_paura"] == "chiarezza", report
    assert report["prossime_paure"] == [
        "Non sembrare abbastanza preparato tecnicamente",
        "Fare una figuraccia con il recruiter",
        "Non saper parlare di me stesso",
    ], report
    print("✅ chiarezza 7.5 -> paura superata (anche con overall basso)")

    # Paura tecnica: si misura sugli esempi concreti, non sulla chiarezza
    profilo_tecnico = dict(PROFILO)
    profilo_tecnico["ansia_principale"] = "Non sembrare abbastanza preparato tecnicamente"
    report = await genera(5, star=5, esempi=7.5, profilo=profilo_tecnico)
    assert report["paura_superata"] is True, report
    assert report["metrica_paura"] == "esempi_concreti", report
    print("✅ paura tecnica: esempi 7.5 -> superata, chiarezza 5 non conta")

    report = await genera(10, star=10, esempi=7.4, profilo=profilo_tecnico)
    assert report["paura_superata"] is False, report
    print("✅ paura tecnica: esempi 7.4 -> non superata (chiarezza 10 non basta)")

    # Paura "figuraccia": si misura sulla struttura STAR
    profilo_figuraccia = dict(PROFILO)
    profilo_figuraccia["ansia_principale"] = "Fare una figuraccia con il recruiter"
    report = await genera(5, star=7.5, esempi=5, profilo=profilo_figuraccia)
    assert report["paura_superata"] is True, report
    assert report["metrica_paura"] == "struttura_star", report
    print("✅ paura figuraccia: STAR 7.5 -> superata")

    # Sticky: era superata per la stessa paura -> resta superata
    precedente = {"paura_superata": True, "paura_attuale": "Restare senza parole"}
    report = await genera(5, precedente=precedente)
    assert report["paura_superata"] is True, report
    print("✅ sticky: resta superata con la stessa paura")

    # Reset: la paura e' cambiata -> il flag non vale piu'
    precedente = {"paura_superata": True, "paura_attuale": "Fare una figuraccia con il recruiter"}
    report = await genera(5, precedente=precedente)
    assert report["paura_superata"] is False, report
    print("✅ reset: paura cambiata -> non superata")

    print("\n🏁 TEST REPORTER COMPLETATI")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AssertionError as e:
        print(f"❌ FALLITO: {e}")
        sys.exit(1)
