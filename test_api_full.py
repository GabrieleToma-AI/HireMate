import asyncio
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api/session"


async def test_full_api():
    async with httpx.AsyncClient() as client:
        print("🚀 AVVIO TEST DI INTEGRAZIONE - VARIANTE GENAI SPECIALIST\n")
        print("=" * 60)

        # --- DATI DI TEST (GenAI Specialist) ---
        profilo = {
            "ansia_principale": "Non saper parlare di me stesso",
            "stile_gestione_problemi": "Faccio ricerche infinite finché non trovo la soluzione",
            "timore_critico": "Non mi sono preparato abbastanza sull'azienda",
        }
        cv_finto = {
            "competenze": ["LangChain", "OpenAI API", "Python", "Vector Database"],
            "progetti": ["Sviluppo di un chatbot per l'assistenza clienti basato su RAG"],
        }

        # ==========================================
        # TEST 1: ENDPOINT /start
        # ==========================================
        print("🧪 TEST 1: Chiamata a /start (Corso GenAI Specialist)")
        payload_start = {
            "corso": "GenAI Specialist",
            "profilo_soft_skill": profilo,
            "cv_json": cv_finto,
        }

        try:
            response_start = await client.post(
                f"{BASE_URL}/start", json=payload_start, timeout=30.0
            )
            if response_start.status_code == 200:
                data_start = response_start.json()
                print("✅ Risposta 200 OK")
                print(f"   Domanda Generata: \"{data_start['questionText']}\"\n")
            else:
                print(f"❌ Errore {response_start.status_code}: {response_start.text}\n")
                return
        except httpx.ConnectError:
            print("❌ Server non attivo.")
            return

        # ==========================================
        # TEST 2: ENDPOINT /end (Prima sessione)
        # ==========================================
        print("🧪 TEST 2: Chiamata a /end (Feedback finale - PRIMA SESSIONE)")
        # Voti mediocri: la paura NON deve essere superata
        valutazioni_finte = [
            {"chiarezza": 1, "struttura_star": 1.4, "esempi_concreti": 5.1},
            {"chiarezza": 1.5, "struttura_star": 3.5, "esempi_concreti": 4.4},
        ]

        payload_end_1 = {
            "corso": "GenAI Specialist",
            "profilo_soft_skill": profilo,
            "valutazioni": valutazioni_finte,
            "report_precedente": None,
        }

        report_1 = None
        try:
            response_end_1 = await client.post(
                f"{BASE_URL}/end", json=payload_end_1, timeout=30.0
            )
            if response_end_1.status_code == 200:
                report_1 = response_end_1.json()["report"]
                print("✅ Risposta 200 OK")
                print(f"   Overall Previous: {report_1['overall_previous']}")
                print(f"   Overall Current:  {report_1['overall_current']}")
                print(f"   Stats (Current):  {report_1['stats_current']}")
                print(f"   Paura superata:   {report_1['paura_superata']}")
                print(f"   Metrica paura:    {report_1['metrica_paura']}")
                print(f"   Badges:           {report_1['badges']}")
                print(f"   Improvements:     {report_1['improvements']}")
                print(f"   Final Tip:        {report_1['final_tip']}\n")
                if report_1["paura_superata"]:
                    print("   ⚠️ Con voti bassi la paura non dovrebbe essere superata\n")
            else:
                print(f"❌ Errore {response_end_1.status_code}: {response_end_1.text}\n")
                return
        except Exception as e:
            print(f"❌ Errore di rete: {e}")
            return

        # ==========================================
        # TEST 3: ENDPOINT /end (Seconda sessione)
        # ==========================================
        print("🧪 TEST 3: Chiamata a /end (Feedback finale - SECONDA SESSIONE)")
        # Voti eccellenti: la paura DEVE essere superata
        valutazioni_migliorate = [
            {"chiarezza": 9, "struttura_star": 8, "esempi_concreti": 8},
            {"chiarezza": 8, "struttura_star": 9, "esempi_concreti": 7},
        ]

        payload_end_2 = {
            "corso": "GenAI Specialist",
            "profilo_soft_skill": profilo,
            "valutazioni": valutazioni_migliorate,
            "report_precedente": report_1,
        }

        try:
            response_end_2 = await client.post(
                f"{BASE_URL}/end", json=payload_end_2, timeout=30.0
            )
            if response_end_2.status_code == 200:
                report_2 = response_end_2.json()["report"]
                print("✅ Risposta 200 OK")
                print(f"   Overall Previous: {report_2['overall_previous']} (deve corrispondere al Current del test 2)")
                print(f"   Overall Current:  {report_2['overall_current']}")
                print(f"   Stats (Previous): {report_2['stats_previous']}")
                print(f"   Stats (Current):  {report_2['stats_current']}")
                print(f"   Paura superata:   {report_2['paura_superata']}")
                print(f"   Metrica paura:    {report_2['metrica_paura']}")
                print(f"   Prossime paure:   {report_2['prossime_paure']}")
                print(f"   Badges:           {report_2['badges']}")
                print(f"   Final Tip:        {report_2['final_tip']}\n")

                if not report_2["paura_superata"]:
                    print("   ⚠️ Con voti alti la paura dovrebbe essere superata\n")
                elif len(report_2["prossime_paure"]) != 3:
                    print("   ⚠️ Attese esattamente 3 paure alternative\n")
            else:
                print(f"❌ Errore {response_end_2.status_code}: {response_end_2.text}\n")
        except Exception as e:
            print(f"❌ Errore di rete: {e}")


if __name__ == "__main__":
    asyncio.run(test_full_api())
