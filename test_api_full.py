"""Test live dell'API: richiede il server attivo su http://127.0.0.1:8000.

Oggi il percorso disponibile e' `/start` una volta e `/end` due volte: prima con
voti bassi (la paura non deve essere superata) e poi con voti alti (deve esserlo).
Consuma quota LLM: NON fa parte della CI.
"""

import asyncio
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000/api/session"
HEALTH = "http://127.0.0.1:8000/api/health"
TIMEOUT = 60.0

CORSO = "GenAI Specialist"
PROFILO = {
    "ansia_principale": "Non saper parlare di me stesso",
    "stile_gestione_problemi": "Faccio ricerche infinite finché non trovo la soluzione",
    "timore_critico": "Non mi sono preparato abbastanza sull'azienda",
}
CV = {
    "competenze": ["LangChain", "OpenAI API", "Python", "Vector Database"],
    "progetti": ["Sviluppo di un chatbot per l'assistenza clienti basato su RAG"],
}

esiti = {"passati": 0, "falliti": 0}


def verifica(condizione: bool, messaggio: str) -> None:
    if not condizione:
        raise AssertionError(messaggio)


async def esegui(nome: str, funzione) -> bool:
    try:
        await funzione()
    except Exception as errore:  # noqa: BLE001 - il test riporta qualsiasi guasto
        esiti["falliti"] += 1
        print(f"  ❌ {nome} -> {type(errore).__name__}: {errore}")
        return False
    esiti["passati"] += 1
    print(f"  ✅ {nome}")
    return True


async def main() -> int:
    print("🌐 TEST LIVE DELL'API (consuma quota LLM)\n")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            salute = await client.get(HEALTH)
        except httpx.ConnectError:
            print("❌ Server non attivo su http://127.0.0.1:8000")
            print("   Avvia `python main.py` e rilancia questo file.")
            return 1

        stato: dict = {}

        async def health():
            verifica(salute.status_code == 200, f"/api/health: {salute.status_code}")

        async def start():
            risposta = await client.post(
                f"{BASE}/start",
                json={"corso": CORSO, "profilo_soft_skill": PROFILO, "cv_json": CV},
            )
            verifica(
                risposta.status_code == 200,
                f"/start: {risposta.status_code} {risposta.text}",
            )
            dati = risposta.json()
            verifica(bool(dati.get("sessionId")), "sessionId mancante o vuoto")
            verifica(
                str(dati.get("turnId", "")).startswith("turn-"),
                f"turnId inatteso: {dati.get('turnId')}",
            )
            verifica(len(dati.get("questionText", "")) > 20, "questionText troppo corto")
            verifica(
                dati.get("gesture") == "explain",
                f"gesture inattesa: {dati.get('gesture')}",
            )
            verifica(dati.get("audioUrl") is None, "senza TTS audioUrl deve essere null")
            verifica(dati.get("visemes") == [], "senza TTS visemes deve essere []")
            stato["start"] = dati
            print(f"     domanda: {dati['questionText'][:110]}...")

        async def end_prima():
            risposta = await client.post(
                f"{BASE}/end",
                json={
                    "sessionId": stato["start"]["sessionId"],
                    "corso": CORSO,
                    "profilo_soft_skill": PROFILO,
                    "valutazioni": [
                        {"chiarezza": 1, "struttura_star": 1.4, "esempi_concreti": 5.1},
                        {"chiarezza": 1.5, "struttura_star": 3.5, "esempi_concreti": 4.4},
                    ],
                    "report_precedente": None,
                },
            )
            verifica(
                risposta.status_code == 200,
                f"/end: {risposta.status_code} {risposta.text}",
            )
            report = risposta.json()["report"]
            verifica(
                report["paura_superata"] is False,
                "con voti bassi la paura non deve essere superata",
            )
            verifica(
                report["overall_previous"] == 0.0,
                f"prima sessione: overall_previous {report['overall_previous']}",
            )
            verifica(
                report["metrica_paura"] == "chiarezza",
                f"metrica_paura: {report['metrica_paura']}",
            )
            verifica(
                report["prossime_paure"] == [],
                "le paure alternative arrivano solo dopo la promozione",
            )
            stato["report1"] = report
            print(
                f"     overall: {report['overall_current']}/100, "
                f"paura superata: {report['paura_superata']}"
            )

        async def end_seconda():
            report_1 = stato["report1"]
            risposta = await client.post(
                f"{BASE}/end",
                json={
                    "sessionId": stato["start"]["sessionId"],
                    "corso": CORSO,
                    "profilo_soft_skill": PROFILO,
                    "valutazioni": [
                        {"chiarezza": 9, "struttura_star": 8, "esempi_concreti": 8},
                        {"chiarezza": 8, "struttura_star": 9, "esempi_concreti": 7},
                    ],
                    "report_precedente": report_1,
                },
            )
            verifica(
                risposta.status_code == 200,
                f"/end: {risposta.status_code} {risposta.text}",
            )
            report = risposta.json()["report"]
            verifica(
                report["paura_superata"] is True,
                "con chiarezza 8.5 la paura deve essere superata",
            )
            verifica(
                report["metrica_paura"] == "chiarezza",
                f"metrica_paura: {report['metrica_paura']}",
            )
            verifica(
                len(report["prossime_paure"]) == 3,
                f"prossime_paure: {len(report['prossime_paure'])}",
            )
            verifica(
                report["overall_previous"] == report_1["overall_current"],
                "overall_previous deve corrispondere al current della sessione prima",
            )
            print(
                f"     overall: {report['overall_current']}/100, "
                f"prossime paure: {len(report['prossime_paure'])}"
            )

        await esegui("GET /api/health", health)
        if await esegui("POST /api/session/start", start):
            if await esegui("POST /api/session/end (prima sessione, voti bassi)", end_prima):
                await esegui(
                    "POST /api/session/end (seconda sessione, voti alti)", end_seconda
                )

    totale = esiti["passati"] + esiti["falliti"]
    print("\n" + "=" * 70)
    print(
        f"TOTALE: {totale}   PASSATI: {esiti['passati']}   "
        f"FALLITI: {esiti['falliti']}"
    )
    print("=" * 70)
    if esiti["falliti"]:
        print("\n❌ ALCUNI TEST SONO FALLITI")
        return 1
    print("\n🎉 TUTTI I TEST SONO PASSATI")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
