"""Test enorme di HireMate.

Copre tutte le novità del backend GenAI senza consumare quota:
- profilo, mappa paura -> metrica, soglia 7.5
- interviewer con cronologia
- evaluator severo e clamp dei voti
- reporter (sticky, reset, prossime paure, overall)
- LLM (JSON, retry, timeout, fallback)
- API /start, /end, /cv/parse, CORS, errori HTTP
- modelli TurnRequest/TurnResponse
- configurazione, requirements, documenti

Esecuzione:
    python test_enorme.py          # 88 test offline (mock LLM)
    python test_enorme.py --live   # + 3 chiamate reali a Gemini Lite

Senza --live nessuna chiamata reale a Gemini/FreeLLMAPI: tutti gli LLM sono mockati.
"""

import asyncio
import io
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError
from pypdf import PdfReader, PdfWriter

import profilo
from agenti import llm as llm_module
from agenti.cv_parser import estrai_cv_json, estrai_testo_pdf
from agenti.evaluator import valuta_risposta
from agenti.interviewer import genera_domanda
from agenti.llm import (
    LLMError,
    _chiama_deepseek,
    _chiama_freellmapi,
    _chiama_gemini,
    _errore_temporaneo,
    _estrai_json,
    chiama_llm_json,
)
from agenti.reporter import genera_report_finale
from corsi import CORSI_ITS, CorsoNonValidoError, get_dettagli_corso
from main import app
from routers.sessions import (
    DOMANDE_PER_COLLOQUIO,
    ProfiloSoftSkill,
    TurnRequest,
    TurnResponse,
    Turno,
    Valutazione,
    ValutazioneCompleta,
)

sys.stdout.reconfigure(encoding="utf-8")
logging.disable(logging.CRITICAL)

LIVE = "--live" in sys.argv

BASE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Dati ufficiali
# ---------------------------------------------------------------------------
PAURE = [
    "Restare senza parole",
    "Non sembrare abbastanza preparato tecnicamente",
    "Fare una figuraccia con il recruiter",
    "Non saper parlare di me stesso",
]
STILI = [
    "Mi blocco e mi faccio prendere dal panico",
    "Chiedo subito aiuto a un collega o a un tutor",
    "Faccio ricerche infinite finché non trovo la soluzione",
    "Mi prendo una pausa e ci riprovo con calma",
]
TIMORI = [
    "Non ho saputo spiegare bene le mie competenze",
    "Ero troppo in ansia e non riuscivo a concentrarmi",
    "Non ho abbastanza esperienza tecnica per il ruolo",
    "Non mi sono preparato abbastanza sull'azienda",
]
METRICHE = ["chiarezza", "struttura_star", "esempi_concreti"]
METRICA_ATTESA = {
    "Restare senza parole": "chiarezza",
    "Non sembrare abbastanza preparato tecnicamente": "esempi_concreti",
    "Fare una figuraccia con il recruiter": "struttura_star",
    "Non saper parlare di me stesso": "chiarezza",
}
PROFILO = {
    "ansia_principale": "Restare senza parole",
    "stile_gestione_problemi": "Mi blocco e mi faccio prendere dal panico",
    "timore_critico": "Non ho abbastanza esperienza tecnica per il ruolo",
}
RISPOSTA_REPORT = {"badges": ["b"], "improvements": ["i"], "final_tip": "t"}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def profilo_con(paura: str = PAURE[0]) -> dict:
    profilo_test = dict(PROFILO)
    profilo_test["ansia_principale"] = paura
    return profilo_test


def valutazioni(chiarezza=8, star=8, esempi=8) -> list[dict]:
    return [{
        "chiarezza": chiarezza,
        "struttura_star": star,
        "esempi_concreti": esempi,
    }]


async def report_con(
    chiarezza=8,
    star=8,
    esempi=8,
    paura=PAURE[0],
    precedente=None,
    llm=None,
) -> dict:
    with patch(
        "agenti.reporter.chiama_llm_json",
        new=AsyncMock(return_value=llm if llm is not None else RISPOSTA_REPORT),
    ):
        return await genera_report_finale(
            corso="SOC Analyst",
            profilo_soft_skill=profilo_con(paura),
            valutazioni=valutazioni(chiarezza, star, esempi),
            report_precedente=precedente,
        )


async def intervista_con(cronologia=None, cv_json=None, llm=None):
    mock = AsyncMock(return_value=llm if llm is not None else {"domanda": "Domanda di test"})
    with patch("agenti.interviewer.chiama_llm_json", new=mock):
        risultato = await genera_domanda(
            corso="SOC Analyst",
            profilo_soft_skill=PROFILO,
            cv_json=cv_json,
            cronologia=cronologia,
        )
    return risultato, mock


def fake_response(testo: str) -> SimpleNamespace:
    return SimpleNamespace(text=testo)


def fake_gemini(side_effect):
    generate = AsyncMock(side_effect=side_effect)
    client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate))
    )
    return client, generate


def crea_pdf_con_testo(testo: str) -> bytes:
    """Costruisce un PDF minimo valido con una riga di testo."""
    stream = f"BT /F1 12 Tf 72 720 Td ({testo}) Tj ET".encode("latin-1")
    oggetti = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(oggetti, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(oggetti) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(oggetti) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(out)


def crea_pdf_vuoto() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def assert_raises(tipo, funzione, frammento=None):
    try:
        funzione()
    except tipo as errore:
        if frammento is not None:
            assert frammento in str(errore), f"Atteso '{frammento}' in '{errore}'"
        return errore
    raise AssertionError(f"Atteso {tipo.__name__}, non è stato sollevato nulla")


async def assert_raises_async(tipo, awaitable, frammento=None):
    try:
        await awaitable
    except tipo as errore:
        if frammento is not None:
            assert frammento in str(errore), f"Atteso '{frammento}' in '{errore}'"
        return errore
    raise AssertionError(f"Atteso {tipo.__name__}, non è stato sollevato nulla")


class Runner:
    def __init__(self):
        self.passati = 0
        self.falliti = 0
        self.errori = []
        self.sezione_corrente = ""

    def sezione(self, titolo: str):
        self.sezione_corrente = titolo
        print("\n" + "=" * 80)
        print(f"  {titolo}")
        print("=" * 80)

    async def caso(self, nome: str, funzione):
        try:
            risultato = funzione()
            if asyncio.iscoroutine(risultato):
                await risultato
            self.passati += 1
            print(f"  ✅ {nome}")
        except Exception as errore:
            self.falliti += 1
            self.errori.append((self.sezione_corrente, nome, errore, traceback.format_exc()))
            print(f"  ❌ {nome} -> {type(errore).__name__}: {errore}")

    def riepilogo(self) -> int:
        totale = self.passati + self.falliti
        print("\n" + "=" * 80)
        print(f"  TOTALE: {totale}   PASSATI: {self.passati}   FALLITI: {self.falliti}")
        print("=" * 80)
        if self.errori:
            print("\nDETTAGLIO FALLIMENTI")
            for sezione, nome, _, tb in self.errori:
                print(f"\n[{sezione}] {nome}\n{tb}")
            return 1
        print("\n🎉 TUTTI I TEST SONO PASSATI")
        return 0


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------
async def main() -> int:
    run = Runner()
    client = TestClient(app)

    # =====================================================================
    run.sezione("1. PROFILO, LISTE E METRICHE")
    # =====================================================================
    def test_liste_ufficiali():
        assert profilo.PAURE_DISPONIBILI == PAURE
        assert profilo.STILI_GESTIONE_PROBLEMI == STILI
        assert profilo.TIMORI_CRITICI == TIMORI
        assert len(PAURE) == len(STILI) == len(TIMORI) == 4
        assert len(set(PAURE)) == len(set(STILI)) == len(set(TIMORI)) == 4

    async def test_mappa_metrica():
        assert set(profilo.METRICA_PER_PAURA) == set(PAURE)
        for paura, metrica in METRICA_ATTESA.items():
            assert profilo.METRICA_PER_PAURA[paura] == metrica
            assert metrica in METRICHE

    def test_soglia():
        assert profilo.SOGLIA_METRICA_PAURA == 7.5
        assert isinstance(profilo.SOGLIA_METRICA_PAURA, float)

    def test_profilo_dataclass():
        valore = ProfiloSoftSkill(**PROFILO)
        assert valore.ansia_principale == PAURE[0]
        assert valore.stile_gestione_problemi == STILI[0]
        assert valore.timore_critico == TIMORI[2]

    await run.caso("Le 4 paure ufficiali sono esatte", test_liste_ufficiali)
    await run.caso("La mappa paura -> metrica è completa", test_mappa_metrica)
    await run.caso("La soglia è 7.5", test_soglia)
    await run.caso("ProfiloSoftSkill accetta il profilo ufficiale", test_profilo_dataclass)

    for campo, valore_errato in [
        ("ansia_principale", "Paura inventata"),
        ("stile_gestione_problemi", "Stile inventato"),
        ("timore_critico", "Timore inventato"),
    ]:
        def test_campo(campo=campo, valore_errato=valore_errato):
            dati = dict(PROFILO)
            dati[campo] = valore_errato
            assert_raises(ValidationError, lambda: ProfiloSoftSkill(**dati))
        await run.caso(f"ProfiloSoftSkill rifiuta {campo} inventato", test_campo)

    # =====================================================================
    run.sezione("2. CORSI")
    # =====================================================================
    def test_corsi_numero():
        assert len(CORSI_ITS) == 14

    def test_corsi_completi():
        for nome, dettagli in CORSI_ITS.items():
            assert isinstance(nome, str) and nome
            assert isinstance(dettagli["materie"], list) and dettagli["materie"]
            assert isinstance(dettagli["focus_hr"], str) and dettagli["focus_hr"]
            assert isinstance(dettagli["area"], str) and dettagli["area"]

    def test_corso_valido():
        dettagli = get_dettagli_corso("SOC Analyst")
        assert "SIEM" in " ".join(dettagli["materie"])

    def test_corso_invalido():
        errore = assert_raises(
            CorsoNonValidoError,
            lambda: get_dettagli_corso("Corso Inventato"),
            "Corso non valido",
        )
        assert isinstance(errore, ValueError)

    await run.caso("Ci sono 14 corsi", test_corsi_numero)
    await run.caso("Tutti i corsi sono completi", test_corsi_completi)
    await run.caso("get_dettagli_corso trova SOC Analyst", test_corso_valido)
    await run.caso("Corso invalido -> CorsoNonValidoError(ValueError)", test_corso_invalido)

    # =====================================================================
    run.sezione("3. LLM: JSON, RETRY, TIMEOUT, FALLBACK")
    # =====================================================================
    def test_estrai_json():
        assert _estrai_json('{"a": 1}') == {"a": 1}
        assert _estrai_json('```json\n{"a": 1}\n```') == {"a": 1}
        assert _estrai_json('```\n{"a": 1}\n```') == {"a": 1}
        assert _estrai_json('testo prima {"a": 1} testo dopo') == {"a": 1}
        assert _estrai_json('  {"a": 1}  ') == {"a": 1}

    def test_estrai_json_vuoto():
        assert_raises(json.JSONDecodeError, lambda: _estrai_json(""))
        assert_raises(json.JSONDecodeError, lambda: _estrai_json(None))

    def test_errore_temporaneo():
        for messaggio in ("503 UNAVAILABLE", "429 quota", "RESOURCE_EXHAUSTED", "Rate Limit", "timeout"):
            assert _errore_temporaneo(Exception(messaggio)) is True
        assert _errore_temporaneo(asyncio.TimeoutError()) is True
        assert _errore_temporaneo(Exception("400 invalid")) is False
        assert _errore_temporaneo(Exception("chiave errata")) is False

    async def test_gemini_retry():
        client_fake, generate = fake_gemini([
            Exception("503 UNAVAILABLE"),
            Exception("503 UNAVAILABLE"),
            fake_response('{"ok": true}'),
        ])
        with patch("agenti.llm.gemini_client", client_fake), patch("agenti.llm.ATTESA_RETRY", 0):
            risultato = await _chiama_gemini("sys", "user", 0.1)
        assert risultato == {"ok": True}
        assert generate.await_count == 3

    async def test_gemini_no_retry():
        client_fake, generate = fake_gemini([Exception("400 INVALID_ARGUMENT")])
        with patch("agenti.llm.gemini_client", client_fake), patch("agenti.llm.ATTESA_RETRY", 0):
            await assert_raises_async(LLMError, _chiama_gemini("sys", "user", 0.1))
        assert generate.await_count == 1

    async def test_gemini_tutti_falliscono():
        client_fake, generate = fake_gemini([Exception("429 quota")] * 3)
        with patch("agenti.llm.gemini_client", client_fake), patch("agenti.llm.ATTESA_RETRY", 0):
            await assert_raises_async(LLMError, _chiama_gemini("sys", "user", 0.1))
        assert generate.await_count == 3

    async def test_gemini_timeout():
        async def lento(*args, **kwargs):
            await asyncio.sleep(0.05)
            return fake_response("{}")

        client_fake, generate = fake_gemini(lento)
        with (
            patch("agenti.llm.gemini_client", client_fake),
            patch("agenti.llm.ATTESA_RETRY", 0),
            patch("agenti.llm.TIMEOUT_GEMINI", 0.01),
        ):
            await assert_raises_async(LLMError, _chiama_gemini("sys", "user", 0.1))
        assert generate.await_count == 3

    async def test_gemini_code_fence():
        client_fake, _ = fake_gemini([fake_response('```json\n{"ok": true}\n```')])
        with patch("agenti.llm.gemini_client", client_fake), patch("agenti.llm.ATTESA_RETRY", 0):
            assert await _chiama_gemini("sys", "user", 0.1) == {"ok": True}

    async def test_freellmapi():
        crea = AsyncMock(return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
        ))
        client_fake = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=crea))
        )
        with patch("agenti.llm.freellmapi_client", client_fake):
            assert await _chiama_freellmapi("sys", "user", 0.1) == {"ok": True}
        crea.assert_awaited_once()

        # DeepSeek è OpenAI-compatibile: stesso client finto, stesso contratto.
        crea_deepseek = AsyncMock(return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
        ))
        client_deepseek = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=crea_deepseek))
        )
        with patch("agenti.llm.deepseek_client", client_deepseek):
            assert await _chiama_deepseek("sys", "user", 0.1) == {"ok": True}
        crea_deepseek.assert_awaited_once()

    async def test_freellmapi_none():
        with patch("agenti.llm.freellmapi_client", None):
            await assert_raises_async(LLMError, _chiama_freellmapi("s", "u", 0.1))

    async def test_gemini_none():
        with patch("agenti.llm.gemini_client", None):
            await assert_raises_async(LLMError, _chiama_gemini("s", "u", 0.1))
        with patch("agenti.llm.deepseek_client", None):
            await assert_raises_async(LLMError, _chiama_deepseek("s", "u", 0.1))

    async def test_fallback():
        ordine = []

        async def freellmapi_giu(*args, **kwargs):
            ordine.append("freellmapi")
            raise LLMError("FreeLLMAPI giù")

        async def gemini_giu(*args, **kwargs):
            ordine.append("gemini")
            raise LLMError("Gemini giù")

        async def deepseek_ok(*args, **kwargs):
            ordine.append("deepseek")
            return {"ok": 1}

        with (
            patch("agenti.llm._chiama_freellmapi", new=freellmapi_giu),
            patch("agenti.llm._chiama_gemini", new=gemini_giu),
            patch("agenti.llm._chiama_deepseek", new=deepseek_ok),
        ):
            assert await chiama_llm_json("s", "u") == {"ok": 1}
        assert ordine == ["freellmapi", "gemini", "deepseek"]

        # Se Gemini risponde, DeepSeek non deve essere toccato (è la risorsa a pagamento).
        ordine.clear()

        async def gemini_ok(*args, **kwargs):
            ordine.append("gemini")
            return {"ok": 2}

        async def deepseek_mai(*args, **kwargs):
            raise AssertionError("DeepSeek non deve essere chiamato")

        with (
            patch("agenti.llm._chiama_freellmapi", new=freellmapi_giu),
            patch("agenti.llm._chiama_gemini", new=gemini_ok),
            patch("agenti.llm._chiama_deepseek", new=deepseek_mai),
        ):
            assert await chiama_llm_json("s", "u") == {"ok": 2}
        assert ordine == ["freellmapi", "gemini"]

    async def test_fallback_tutti():
        with (
            patch("agenti.llm._chiama_freellmapi", new=AsyncMock(side_effect=LLMError("free giù"))),
            patch("agenti.llm._chiama_gemini", new=AsyncMock(side_effect=LLMError("gemini giù"))),
            patch("agenti.llm._chiama_deepseek", new=AsyncMock(side_effect=LLMError("deepseek giù"))),
        ):
            errore = await assert_raises_async(
                LLMError, chiama_llm_json("s", "u"), "Tutti i provider"
            )
            # Tutti e tre gli errori devono comparire: prima si vedeva solo l'ultimo.
            testo = str(errore)
            assert "free giù" in testo, testo
            assert "gemini giù" in testo, testo
            assert "deepseek giù" in testo, testo

    def test_modello():
        assert "gemini-3.5-flash-lite" in llm_module.MODELLO_GEMINI
        assert llm_module.TENTATIVI_GEMINI == 3
        assert llm_module.MODELLO_DEEPSEEK == "deepseek-flash"
        # I primi due provider devono restare rapidi: l'utente è in attesa.
        assert llm_module.TIMEOUT_FREELLMAPI <= 5
        assert llm_module.TIMEOUT_GEMINI <= 10
        assert llm_module.TIMEOUT_DEEPSEEK >= llm_module.TIMEOUT_GEMINI

    await run.caso("_estrai_json gestisce JSON, code fence e testo extra", test_estrai_json)
    await run.caso("_estrai_json rifiuta risposte vuote", test_estrai_json_vuoto)
    await run.caso("_errore_temporaneo riconosce 503/429/timeout", test_errore_temporaneo)
    await run.caso("Gemini: 2 retry poi successo", test_gemini_retry)
    await run.caso("Gemini: nessun retry su errore 400", test_gemini_no_retry)
    await run.caso("Gemini: 3 errori -> LLMError", test_gemini_tutti_falliscono)
    await run.caso("Gemini: timeout -> retry e LLMError", test_gemini_timeout)
    await run.caso("Gemini: risposta con code fence", test_gemini_code_fence)
    await run.caso("FreeLLMAPI/DeepSeek: risposta JSON", test_freellmapi)
    await run.caso("FreeLLMAPI non configurato -> LLMError", test_freellmapi_none)
    await run.caso("Gemini/DeepSeek non configurati -> LLMError", test_gemini_none)
    await run.caso("chiama_llm_json: ordine FreeLLMAPI -> Gemini -> DeepSeek", test_fallback)
    await run.caso("chiama_llm_json: tutti i provider falliscono", test_fallback_tutti)
    await run.caso("Modello unico gemini-3.5-flash-lite", test_modello)

    # =====================================================================
    run.sezione("4. INTERVIEWER E CRONOLOGIA")
    # =====================================================================
    async def test_interviewer_prima():
        risultato, mock = await intervista_con()
        assert risultato == "Domanda di test"
        kwargs = mock.await_args.kwargs
        assert kwargs["temperature"] == 0.8
        assert "prima" in kwargs["user_prompt"]
        sistema = kwargs["system_prompt"]
        assert "SOC Analyst" in sistema
        assert "SIEM" in sistema
        assert PROFILO["ansia_principale"] in sistema
        assert PROFILO["stile_gestione_problemi"] in sistema
        assert PROFILO["timore_critico"] in sistema
        assert "NON ripetere" in sistema
        assert "Prenditi pure un momento" in sistema

    async def test_interviewer_cv():
        _, mock = await intervista_con(cv_json={"competenze": ["Python"], "progetti": ["Rete aziendale"]})
        sistema = mock.await_args.kwargs["system_prompt"]
        assert "Python" in sistema
        assert "Rete aziendale" in sistema

    async def test_interviewer_cronologia_dict():
        cronologia = [{"domanda": "D1", "trascrizione": "R1"}]
        _, mock = await intervista_con(cronologia=cronologia)
        kwargs = mock.await_args.kwargs
        assert "prossima" in kwargs["user_prompt"]
        assert "prima" not in kwargs["user_prompt"]
        sistema = kwargs["system_prompt"]
        assert "<Cronologia>" in sistema
        assert "D1" in sistema and "R1" in sistema

    async def test_interviewer_cronologia_modelli():
        cronologia = [Turno(domanda="D2", trascrizione="R2")]
        _, mock = await intervista_con(cronologia=cronologia)
        sistema = mock.await_args.kwargs["system_prompt"]
        assert "D2" in sistema and "R2" in sistema

    async def test_interviewer_default():
        risultato, _ = await intervista_con(llm={})
        assert "Mi scuso" in risultato

    async def test_interviewer_corso_invalido():
        await assert_raises_async(
            CorsoNonValidoError,
            genera_domanda(corso="Corso Inventato", profilo_soft_skill=PROFILO),
        )

    await run.caso("Interviewer: prima domanda, 0.8, profilo nel prompt", test_interviewer_prima)
    await run.caso("Interviewer: CV nel prompt", test_interviewer_cv)
    await run.caso("Interviewer: cronologia (dict) e nessuna ripetizione", test_interviewer_cronologia_dict)
    await run.caso("Interviewer: cronologia (modelli Turno)", test_interviewer_cronologia_modelli)
    await run.caso("Interviewer: risposta vuota -> messaggio di scusa", test_interviewer_default)
    await run.caso("Interviewer: corso invalido", test_interviewer_corso_invalido)

    # =====================================================================
    run.sezione("5. EVALUATOR")
    # =====================================================================
    async def test_evaluator_clamp():
        mock = AsyncMock(return_value={
            "chiarezza": 0,
            "struttura_star": 11,
            "esempi_concreti": 7.9,
            "suggerimento": "s",
            "better_answer": "b",
        })
        with patch("agenti.evaluator.chiama_llm_json", new=mock):
            risultato = await valuta_risposta(
                corso="SOC Analyst",
                profilo_soft_skill=PROFILO,
                domanda="Domanda",
                trascrizione="Trascrizione",
                cv_json={"competenze": ["Python"]},
            )
        assert risultato["chiarezza"] == 1
        assert risultato["struttura_star"] == 10
        assert risultato["esempi_concreti"] == 7
        assert risultato["suggerimento"] == "s"
        assert risultato["better_answer"] == "b"
        assert mock.await_args.kwargs["temperature"] == 0.2

    async def test_evaluator_default():
        with patch("agenti.evaluator.chiama_llm_json", new=AsyncMock(return_value={})):
            risultato = await valuta_risposta(
                corso="SOC Analyst",
                profilo_soft_skill=PROFILO,
                domanda="D",
                trascrizione="T",
            )
        assert risultato["chiarezza"] == 1
        assert risultato["struttura_star"] == 1
        assert risultato["esempi_concreti"] == 1
        assert risultato["suggerimento"] == ""
        assert risultato["better_answer"] == ""

    async def test_evaluator_prompt():
        mock = AsyncMock(return_value={"chiarezza": 5, "struttura_star": 5, "esempi_concreti": 5})
        with patch("agenti.evaluator.chiama_llm_json", new=mock):
            await valuta_risposta(
                corso="SOC Analyst",
                profilo_soft_skill=PROFILO,
                domanda="D-test",
                trascrizione="T-test",
                cv_json={"competenze": ["Python"]},
            )
        sistema = mock.await_args.kwargs["system_prompt"]
        assert "1-3" in sistema
        assert "severo" in sistema
        assert "fuori tema" in sistema
        assert "SOC Analyst" in sistema
        assert PROFILO["ansia_principale"] in sistema
        assert PROFILO["timore_critico"] in sistema
        assert "<domanda>D-test</domanda>" in sistema
        assert "<trascrizione>T-test</trascrizione>" in sistema
        assert "Python" in sistema

    async def test_evaluator_stringa():
        with patch("agenti.evaluator.chiama_llm_json", new=AsyncMock(return_value={
            "chiarezza": "8", "struttura_star": "7", "esempi_concreti": "9",
        })):
            risultato = await valuta_risposta(
                corso="SOC Analyst",
                profilo_soft_skill=PROFILO,
                domanda="D",
                trascrizione="T",
            )
        assert (risultato["chiarezza"], risultato["struttura_star"], risultato["esempi_concreti"]) == (8, 7, 9)

    await run.caso("Evaluator: clamp 1-10 e campi extra", test_evaluator_clamp)
    await run.caso("Evaluator: campi mancanti -> default", test_evaluator_default)
    await run.caso("Evaluator: prompt severo e input completi", test_evaluator_prompt)
    await run.caso("Evaluator: voti come stringhe", test_evaluator_stringa)

    # =====================================================================
    run.sezione("6. REPORTER E REGOLA PAURA")
    # =====================================================================
    async def test_reporter_overall():
        report = await report_con(8, 8, 8)
        assert report["overall_current"] == 80.0
        assert report["stats_current"] == {
            "chiarezza": 8.0,
            "struttura_star": 8.0,
            "esempi_concreti": 8.0,
        }
        assert report["overall_previous"] == 0.0
        assert report["stats_previous"] == {
            "chiarezza": 0.0,
            "struttura_star": 0.0,
            "esempi_concreti": 0.0,
        }

    async def test_reporter_previous():
        precedente = {
            "overall_current": 50.0,
            "stats_current": {"chiarezza": 5.0, "struttura_star": 5.0, "esempi_concreti": 5.0},
        }
        report = await report_con(8, 8, 8, precedente=precedente)
        assert report["overall_previous"] == 50.0
        assert report["stats_previous"] == precedente["stats_current"]

    async def test_reporter_sticky():
        precedente = {"paura_superata": True, "paura_attuale": PAURE[0]}
        report = await report_con(1, 1, 1, precedente=precedente)
        assert report["paura_superata"] is True
        assert len(report["prossime_paure"]) == 3

    async def test_reporter_reset():
        precedente = {"paura_superata": True, "paura_attuale": PAURE[1]}
        report = await report_con(1, 1, 1, precedente=precedente)
        assert report["paura_superata"] is False
        assert report["prossime_paure"] == []

    async def test_reporter_sticky_senza_paura_attuale():
        precedente = {"paura_superata": True}
        report = await report_con(1, 1, 1, precedente=precedente)
        assert report["paura_superata"] is False

    async def test_reporter_opzioni():
        for paura in PAURE:
            report = await report_con(7.5, 7.5, 7.5, paura=paura)
            assert report["paura_attuale"] == paura
            assert report["metrica_paura"] == METRICA_ATTESA[paura]
            assert report["paura_superata"] is True
            assert report["prossime_paure"] == [p for p in PAURE if p != paura]
            assert paura not in report["prossime_paure"]
            assert len(report["prossime_paure"]) == 3

    async def test_reporter_metrica_specifica():
        report = await report_con(7.5, 1, 1, paura=PAURE[0])
        assert report["paura_superata"] is True
        assert report["overall_current"] < 40
        assert report["metrica_paura"] == "chiarezza"

        report = await report_con(1, 1, 7.5, paura=PAURE[1])
        assert report["paura_superata"] is True
        assert report["overall_current"] < 40
        assert report["metrica_paura"] == "esempi_concreti"

        report = await report_con(1, 7.5, 1, paura=PAURE[2])
        assert report["paura_superata"] is True
        assert report["overall_current"] < 40
        assert report["metrica_paura"] == "struttura_star"

    async def test_reporter_soglia():
        for paura, metrica in METRICA_ATTESA.items():
            valori = {"chiarezza": 1, "struttura_star": 1, "esempi_concreti": 1}
            valori[metrica] = 7.4
            report = await report_con(
                chiarezza=valori["chiarezza"],
                star=valori["struttura_star"],
                esempi=valori["esempi_concreti"],
                paura=paura,
            )
            assert report["paura_superata"] is False, paura
            valori[metrica] = 7.5
            report = await report_con(
                chiarezza=valori["chiarezza"],
                star=valori["struttura_star"],
                esempi=valori["esempi_concreti"],
                paura=paura,
            )
            assert report["paura_superata"] is True, paura

    async def test_reporter_vuoto():
        with patch("agenti.reporter.chiama_llm_json", new=AsyncMock(return_value=RISPOSTA_REPORT)):
            await assert_raises_async(
                LLMError,
                genera_report_finale(
                    corso="SOC Analyst",
                    profilo_soft_skill=PROFILO,
                    valutazioni=[],
                ),
                "Nessuna valutazione",
            )

    async def test_reporter_badges_default():
        report = await report_con(8, 8, 8, llm={})
        assert report["badges"] == []
        assert report["improvements"] == []
        assert report["final_tip"] == ""

    await run.caso("Reporter: overall e stats prima sessione", test_reporter_overall)
    await run.caso("Reporter: stats/overall precedenti", test_reporter_previous)
    await run.caso("Reporter: sticky sulla stessa paura", test_reporter_sticky)
    await run.caso("Reporter: reset se la paura cambia", test_reporter_reset)
    await run.caso("Reporter: sticky richiede paura_attuale", test_reporter_sticky_senza_paura_attuale)
    await run.caso("Reporter: 3 opzioni corrette per ogni paura", test_reporter_opzioni)
    await run.caso("Reporter: la metrica specifica batte l'overall", test_reporter_metrica_specifica)
    await run.caso("Reporter: soglia 7.4/7.5 per ogni metrica", test_reporter_soglia)
    await run.caso("Reporter: valutazioni vuote -> LLMError", test_reporter_vuoto)
    await run.caso("Reporter: badges/improvements mancanti -> default", test_reporter_badges_default)

    # =====================================================================
    run.sezione("7. MODELLI E API")
    # =====================================================================
    def test_modello_valutazione():
        assert Valutazione(chiarezza=8, struttura_star=7, esempi_concreti=9)
        assert_raises(ValidationError, lambda: Valutazione(chiarezza=11, struttura_star=7, esempi_concreti=9))
        assert_raises(ValidationError, lambda: Valutazione(chiarezza=-1, struttura_star=7, esempi_concreti=9))

    def test_modello_valutazione_completa():
        valore = ValutazioneCompleta(
            chiarezza=8, struttura_star=7, esempi_concreti=9,
            suggerimento="s", better_answer="b",
        )
        assert valore.suggerimento == "s"
        assert valore.better_answer == "b"

    def test_modello_turno():
        turno = Turno(domanda="D1", trascrizione="R1")
        assert turno.domanda == "D1"

    def test_turn_request():
        richiesta = TurnRequest(
            corso="SOC Analyst",
            profilo_soft_skill=PROFILO,
            domanda="D2",
            trascrizione="R2",
        )
        assert richiesta.cronologia == []

        richiesta = TurnRequest(
            corso="SOC Analyst",
            profilo_soft_skill=PROFILO,
            domanda="D2",
            trascrizione="R2",
            cronologia=[{"domanda": "D1", "trascrizione": "R1"}],
        )
        assert richiesta.cronologia[0].domanda == "D1"
        assert richiesta.cronologia[0].trascrizione == "R1"

    def test_turn_request_corso_invalido():
        assert_raises(
            ValidationError,
            lambda: TurnRequest(
                corso="Corso Inventato",
                profilo_soft_skill=PROFILO,
                domanda="D",
                trascrizione="R",
            ),
        )

    def test_turn_response():
        risposta = TurnResponse(
            turnId="turn-1",
            valutazione=ValutazioneCompleta(chiarezza=8, struttura_star=7, esempi_concreti=9),
            prossimaDomanda="D2",
            colloquio_terminato=False,
        )
        assert risposta.turnId == "turn-1"
        assert risposta.prossimaDomanda == "D2"
        assert risposta.colloquio_terminato is False
        assert risposta.audioUrl is None
        assert risposta.visemes == []
        assert risposta.gesture == "explain"

    def test_domande_per_colloquio():
        assert DOMANDE_PER_COLLOQUIO == 6

    async def test_api_start():
        mock = AsyncMock(return_value="Domanda API")
        with patch("routers.sessions.genera_domanda", new=mock):
            prima = client.post("/api/session/start", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": PROFILO,
                "cv_json": {"competenze": ["Python"]},
            })
            seconda = client.post("/api/session/start", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": PROFILO,
            })
        assert prima.status_code == 200
        assert seconda.status_code == 200
        dati = prima.json()
        assert dati["questionText"] == "Domanda API"
        assert dati["turnId"].startswith("turn-")
        assert dati["turnId"] != seconda.json()["turnId"]
        assert dati["audioUrl"] is None
        assert dati["visemes"] == []
        assert dati["gesture"] == "explain"
        assert mock.await_args_list[0].kwargs["corso"] == "SOC Analyst"
        assert mock.await_args_list[0].kwargs["cv_json"] == {"competenze": ["Python"]}

    async def test_api_start_profilo_invalido():
        for campo, valore in [
            ("ansia_principale", "Paura inventata"),
            ("stile_gestione_problemi", "Stile inventato"),
            ("timore_critico", "Timore inventato"),
        ]:
            dati = dict(PROFILO)
            dati[campo] = valore
            risposta = client.post("/api/session/start", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": dati,
            })
            assert risposta.status_code == 422, (campo, risposta.status_code)

        incompleto = dict(PROFILO)
        incompleto.pop("ansia_principale")
        risposta = client.post("/api/session/start", json={
            "corso": "SOC Analyst",
            "profilo_soft_skill": incompleto,
        })
        assert risposta.status_code == 422

    async def test_api_start_corso_invalido():
        risposta = client.post("/api/session/start", json={
            "corso": "Corso Inventato",
            "profilo_soft_skill": PROFILO,
        })
        assert risposta.status_code == 422

    async def test_api_start_llm_error():
        with patch("routers.sessions.genera_domanda", new=AsyncMock(side_effect=LLMError("segreto"))):
            risposta = client.post("/api/session/start", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": PROFILO,
            })
        assert risposta.status_code == 503
        assert "segreto" not in risposta.text
        assert "Servizio LLM" in risposta.json()["detail"]

    async def test_api_start_generic_error():
        with patch("routers.sessions.genera_domanda", new=AsyncMock(side_effect=RuntimeError("segreto"))):
            risposta = client.post("/api/session/start", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": PROFILO,
            })
        assert risposta.status_code == 500
        assert "segreto" not in risposta.text
        assert risposta.json()["detail"] == "Errore interno del server."

    async def test_api_end():
        report_finto = {
            "overall_previous": 0.0,
            "overall_current": 80.0,
            "stats_previous": {},
            "stats_current": {"chiarezza": 8.0, "struttura_star": 8.0, "esempi_concreti": 8.0},
            "paura_attuale": PAURE[0],
            "metrica_paura": "chiarezza",
            "paura_superata": True,
            "prossime_paure": PAURE[1:],
            "badges": [],
            "improvements": [],
            "final_tip": "",
        }
        mock = AsyncMock(return_value=report_finto)
        with patch("routers.sessions.genera_report_finale", new=mock):
            risposta = client.post("/api/session/end", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": PROFILO,
                "valutazioni": [{"chiarezza": 8, "struttura_star": 8, "esempi_concreti": 8}],
                "report_precedente": None,
            })
        assert risposta.status_code == 200
        assert risposta.json()["report"]["paura_superata"] is True
        kwargs = mock.await_args.kwargs
        assert kwargs["valutazioni"][0]["chiarezza"] == 8
        assert kwargs["profilo_soft_skill"]["ansia_principale"] == PAURE[0]

    async def test_api_end_valutazioni_vuote():
        risposta = client.post("/api/session/end", json={
            "corso": "SOC Analyst",
            "profilo_soft_skill": PROFILO,
            "valutazioni": [],
        })
        assert risposta.status_code == 422

    async def test_api_end_voti_fuori_range():
        for voto in (11, -1):
            risposta = client.post("/api/session/end", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": PROFILO,
                "valutazioni": [{"chiarezza": voto, "struttura_star": 8, "esempi_concreti": 8}],
            })
            assert risposta.status_code == 422, voto

    async def test_api_end_voto_mancante():
        risposta = client.post("/api/session/end", json={
            "corso": "SOC Analyst",
            "profilo_soft_skill": PROFILO,
            "valutazioni": [{"chiarezza": 8, "struttura_star": 8}],
        })
        assert risposta.status_code == 422

    async def test_api_end_llm_error():
        with patch("routers.sessions.genera_report_finale", new=AsyncMock(side_effect=LLMError("segreto"))):
            risposta = client.post("/api/session/end", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": PROFILO,
                "valutazioni": [{"chiarezza": 8, "struttura_star": 8, "esempi_concreti": 8}],
            })
        assert risposta.status_code == 503
        assert "segreto" not in risposta.text

    async def test_api_end_generic_error():
        with patch("routers.sessions.genera_report_finale", new=AsyncMock(side_effect=RuntimeError("segreto"))):
            risposta = client.post("/api/session/end", json={
                "corso": "SOC Analyst",
                "profilo_soft_skill": PROFILO,
                "valutazioni": [{"chiarezza": 8, "struttura_star": 8, "esempi_concreti": 8}],
            })
        assert risposta.status_code == 500
        assert "segreto" not in risposta.text
        assert risposta.json()["detail"] == "Errore interno del server."

    async def test_api_health():
        radice = client.get("/")
        assert radice.status_code == 200
        assert radice.json()["status"] == "success"

        salute = client.get("/api/health")
        assert salute.status_code == 200
        assert "Gemini" in salute.json()["llm"]

    async def test_openapi():
        percorsi = client.get("/openapi.json").json()["paths"]
        assert "/api/session/start" in percorsi
        assert "/api/session/end" in percorsi
        assert "/api/cv/parse" in percorsi

    async def test_cors():
        origini = os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
        )
        origine_ok = [o.strip() for o in origini.split(",") if o.strip()][0]
        risposta = client.options(
            "/api/session/start",
            headers={
                "Origin": origine_ok,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert risposta.status_code == 200
        assert risposta.headers.get("access-control-allow-origin") == origine_ok

        risposta = client.options(
            "/api/session/start",
            headers={
                "Origin": "http://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert (
            risposta.status_code == 400
            or risposta.headers.get("access-control-allow-origin") is None
        )

    await run.caso("Valutazione valida e fuori range", test_modello_valutazione)
    await run.caso("ValutazioneCompleta con suggerimento/better", test_modello_valutazione_completa)
    await run.caso("Turno valido", test_modello_turno)
    await run.caso("TurnRequest: cronologia default e popolata", test_turn_request)
    await run.caso("TurnRequest: corso invalido", test_turn_request_corso_invalido)
    await run.caso("TurnResponse: campi e default", test_turn_response)
    await run.caso("DOMANDE_PER_COLLOQUIO = 6", test_domande_per_colloquio)
    await run.caso("API /start risponde e turnId è univoco", test_api_start)
    await run.caso("API /start rifiuta profilo invalido/incompleto", test_api_start_profilo_invalido)
    await run.caso("API /start rifiuta corso invalido", test_api_start_corso_invalido)
    await run.caso("API /start: LLMError -> 503 generico", test_api_start_llm_error)
    await run.caso("API /start: errore generico -> 500 generico", test_api_start_generic_error)
    await run.caso("API /end valido", test_api_end)
    await run.caso("API /end rifiuta valutazioni vuote", test_api_end_valutazioni_vuote)
    await run.caso("API /end rifiuta voti fuori range", test_api_end_voti_fuori_range)
    await run.caso("API /end rifiuta voto mancante", test_api_end_voto_mancante)
    await run.caso("API /end: LLMError -> 503", test_api_end_llm_error)
    await run.caso("API /end: errore generico -> 500", test_api_end_generic_error)
    await run.caso("API root e health", test_api_health)
    await run.caso("OpenAPI espone start/end/cv", test_openapi)
    await run.caso("CORS: origine ammessa e origine estranea", test_cors)

    # =====================================================================
    run.sezione("8. CV PARSER E ENDPOINT /api/cv/parse")
    # =====================================================================
    pdf_testo = crea_pdf_con_testo("Python Docker Kubernetes")
    pdf_vuoto = crea_pdf_vuoto()

    def test_pdf_estrazione():
        testo = estrai_testo_pdf(pdf_testo)
        assert "Python" in testo
        assert "Docker" in testo
        assert "Kubernetes" in testo

    def test_pdf_vuoto_estrazione():
        assert estrai_testo_pdf(pdf_vuoto) == ""

    async def test_cv_json():
        with patch("agenti.cv_parser.chiama_llm_json", new=AsyncMock(return_value={
            "competenze": ["Python"],
            "progetti": ["Rete"],
        })):
            risultato = await estrai_cv_json(pdf_testo)
        assert risultato == {"competenze": ["Python"], "progetti": ["Rete"]}

    async def test_cv_vuoto_errore():
        await assert_raises_async(ValueError, estrai_cv_json(pdf_vuoto), "non contiene testo")

    def test_cv_corrotto_errore():
        assert_raises(ValueError, lambda: estrai_testo_pdf(b"non e un pdf"), "non leggibile")

    async def test_cv_endpoint_ok():
        with patch("agenti.cv_parser.chiama_llm_json", new=AsyncMock(return_value={
            "competenze": ["Python"],
            "progetti": ["Rete"],
        })):
            risposta = client.post(
                "/api/cv/parse",
                files={"file": ("cv.pdf", pdf_testo, "application/pdf")},
            )
        assert risposta.status_code == 200
        assert risposta.json()["cv_json"]["competenze"] == ["Python"]

    async def test_cv_endpoint_tipo():
        risposta = client.post(
            "/api/cv/parse",
            files={"file": ("cv.txt", b"ciao", "text/plain")},
        )
        assert risposta.status_code == 415

    async def test_cv_endpoint_vuoto():
        risposta = client.post(
            "/api/cv/parse",
            files={"file": ("cv.pdf", b"", "application/pdf")},
        )
        assert risposta.status_code == 400

    async def test_cv_endpoint_grande():
        risposta = client.post(
            "/api/cv/parse",
            files={"file": ("cv.pdf", b"0" * (5 * 1024 * 1024 + 1), "application/pdf")},
        )
        assert risposta.status_code == 413

    async def test_cv_endpoint_senza_testo():
        risposta = client.post(
            "/api/cv/parse",
            files={"file": ("cv.pdf", pdf_vuoto, "application/pdf")},
        )
        assert risposta.status_code == 400

    async def test_cv_endpoint_corrotto():
        risposta = client.post(
            "/api/cv/parse",
            files={"file": ("cv.pdf", b"non e un pdf", "application/pdf")},
        )
        assert risposta.status_code == 400

    async def test_cv_endpoint_llm_error():
        with patch("routers.cv.estrai_cv_json", new=AsyncMock(side_effect=LLMError("segreto"))):
            risposta = client.post(
                "/api/cv/parse",
                files={"file": ("cv.pdf", pdf_testo, "application/pdf")},
            )
        assert risposta.status_code == 503
        assert "segreto" not in risposta.text

    async def test_cv_endpoint_generic_error():
        with patch("routers.cv.estrai_cv_json", new=AsyncMock(side_effect=RuntimeError("segreto"))):
            risposta = client.post(
                "/api/cv/parse",
                files={"file": ("cv.pdf", pdf_testo, "application/pdf")},
            )
        assert risposta.status_code == 500
        assert "segreto" not in risposta.text

    await run.caso("PDF: estrazione testo", test_pdf_estrazione)
    await run.caso("PDF: vuoto -> stringa vuota", test_pdf_vuoto_estrazione)
    await run.caso("CV: PDF -> JSON con LLM mock", test_cv_json)
    await run.caso("CV: PDF vuoto -> ValueError", test_cv_vuoto_errore)
    await run.caso("CV: PDF corrotto -> ValueError", test_cv_corrotto_errore)
    await run.caso("CV endpoint: PDF valido -> 200", test_cv_endpoint_ok)
    await run.caso("CV endpoint: tipo non PDF -> 415", test_cv_endpoint_tipo)
    await run.caso("CV endpoint: file vuoto -> 400", test_cv_endpoint_vuoto)
    await run.caso("CV endpoint: file > 5 MB -> 413", test_cv_endpoint_grande)
    await run.caso("CV endpoint: PDF senza testo -> 400", test_cv_endpoint_senza_testo)
    await run.caso("CV endpoint: PDF corrotto -> 400", test_cv_endpoint_corrotto)
    await run.caso("CV endpoint: LLMError -> 503", test_cv_endpoint_llm_error)
    await run.caso("CV endpoint: errore generico -> 500", test_cv_endpoint_generic_error)

    # =====================================================================
    run.sezione("9. CONFIGURAZIONE, REQUIREMENTS E DOCUMENTI")
    # =====================================================================
    def test_requirements():
        contenuto = (BASE / "requirements.txt").read_bytes()
        assert not contenuto.startswith(b"\xff\xfe")
        testo = contenuto.decode("utf-8")
        for atteso in (
            "google-genai==3.4.0",
            "pypdf==7.1.1",
            "python-multipart==0.0.34",
            "fastapi==",
            "uvicorn==",
            "openai==",
            "python-dotenv==",
        ):
            assert atteso in testo, atteso
        assert "google-generativeai" not in testo

    def test_env_example():
        testo = (BASE / ".env.example").read_text(encoding="utf-8")
        assert "GEMINI_MODEL=gemini-3.5-flash-lite" in testo
        assert "GEMINI_FALLBACK_MODEL" not in testo
        assert "3.8" not in testo
        assert "LLM_RETRY_DELAY_SECONDS=1.5" in testo
        assert "CORS_ALLOW_ORIGINS" in testo
        assert "localhost:3000" in testo

    def test_gitignore():
        testo = (BASE / ".gitignore").read_text(encoding="utf-8")
        for atteso in (".env", "venv/", "__pycache__/"):
            assert atteso in testo

    def test_readme():
        testo = (BASE / "README.md").read_text(encoding="utf-8")
        for atteso in ("metrica_paura", "TurnRequest", "/api/cv/parse", "bcrypt", "7.5"):
            assert atteso in testo, atteso

    def test_funzionamento():
        testo = (BASE / "processi_spiegati" / "funzionamento.md").read_text(encoding="utf-8")
        for atteso in ("METRICA_PER_PAURA", "cronologia", "cv_parser"):
            assert atteso in testo, atteso

    def test_recap():
        testo = (BASE / "processi_spiegati" / "recap_18_11_2.md").read_text(encoding="utf-8")
        for atteso in ("7.5", "TurnRequest", "pypdf"):
            assert atteso in testo, atteso

    def test_piano():
        testo = (BASE / "processi_spiegati" / "piano_lavoro_18_11.md").read_text(encoding="utf-8")
        for atteso in ("feature/genai-core", "7.5"):
            assert atteso in testo, atteso

    def test_input_registrazione():
        testo = (BASE / "input_registrazione.txt").read_text(encoding="utf-8")
        assert "Non ho abbastanza esperienza tecnica per il ruolo" in testo

    def test_nessun_38_nel_codice():
        for percorso in BASE.rglob("*.py"):
            if "venv" in percorso.parts or "__pycache__" in percorso.parts:
                continue
            if percorso.name == "test_enorme.py":
                continue
            assert "3.8" not in percorso.read_text(encoding="utf-8"), percorso

    await run.caso("requirements.txt UTF-8 e dipendenze corrette", test_requirements)
    await run.caso(".env.example: solo Lite, retry e CORS", test_env_example)
    await run.caso(".gitignore protegge .env e venv", test_gitignore)
    await run.caso("README aggiornato", test_readme)
    await run.caso("funzionamento.md aggiornato", test_funzionamento)
    await run.caso("recap_18_11_2.md aggiornato", test_recap)
    await run.caso("piano_lavoro_18_11.md aggiornato", test_piano)
    await run.caso("input_registrazione.txt allineato", test_input_registrazione)
    await run.caso("Nessun riferimento a Gemini 3.8 nel codice", test_nessun_38_nel_codice)

    # =====================================================================
    if LIVE:
        run.sezione("10. LIVE GEMINI (chiamate reali, consuma quota)")

        async def live_interviewer():
            domanda = await genera_domanda(
                corso="SOC Analyst", profilo_soft_skill=PROFILO
            )
            assert isinstance(domanda, str)
            assert len(domanda) > 20, domanda
            # Non tutte le domande finiscono con "?": l'HR può usare l'imperativo.
            spie = ("?", "descriva", "racconti", "come", "quale", "spieghi")
            assert any(pista in domanda.lower() for pista in spie), domanda
            print(f"     domanda reale: {domanda[:120]}...")

        async def live_evaluator():
            risultato = await valuta_risposta(
                corso="SOC Analyst",
                profilo_soft_skill=PROFILO,
                domanda="Raccontami un progetto a cui hai lavorato.",
                trascrizione="Non lo so, non ho mai fatto niente.",
            )
            for chiave in METRICHE:
                assert isinstance(risultato[chiave], int), chiave
                assert 1 <= risultato[chiave] <= 10, (chiave, risultato[chiave])
            assert isinstance(risultato["suggerimento"], str)
            assert isinstance(risultato["better_answer"], str)
            media = sum(risultato[c] for c in METRICHE) / 3
            print(
                "     voti reali: "
                f"{risultato['chiarezza']}/{risultato['struttura_star']}/{risultato['esempi_concreti']}"
                f" (media {media:.1f})"
            )
            # Una risposta palesemente povera non deve essere premiata.
            assert media <= 6, f"Risposta povera valutata troppo alta: {risultato}"

        async def live_reporter():
            report = await genera_report_finale(
                corso="SOC Analyst",
                profilo_soft_skill=profilo_con(PAURE[0]),
                valutazioni=valutazioni(8, 8, 8),
            )
            assert report["paura_superata"] is True, report
            assert report["metrica_paura"] == "chiarezza", report
            assert len(report["prossime_paure"]) == 3, report
            assert isinstance(report["final_tip"], str)
            print(f"     report reale: {report['overall_current']}/100, metrica chiarezza")

        await run.caso("LIVE: Interviewer genera una domanda vera", live_interviewer)
        await run.caso("LIVE: Evaluator non premia una risposta povera", live_evaluator)
        await run.caso("LIVE: Reporter calcola la paura e chiama l'LLM", live_reporter)

    # =====================================================================
    esito = run.riepilogo()
    client.close()
    return esito


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
