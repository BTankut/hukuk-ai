from __future__ import annotations

import asyncio

from guardrails.pipeline import GuardrailsResult
from rag.orchestrator import RAGOrchestrator, RetrievedChunk


class DummyLLMClient:
    async def generate_rag_draft(self, query: str, context: str) -> str:
        assert query
        assert "TBK" in context
        return "Haksız fiil talepleri için süre [Kaynak: TBK md.72] olarak düzenlenir."


class DummyGuardrails:
    def __init__(self) -> None:
        self.called = 0

    async def run(self, *, user_query: str, draft_answer: str, retrieved_chunks: list[dict]):
        self.called += 1
        assert user_query
        assert draft_answer
        assert retrieved_chunks
        return GuardrailsResult(answer=draft_answer, blocked=False, reasons=[])


class DummyMutatingGuardrails:
    def __init__(self, rewritten_answer: str) -> None:
        self.rewritten_answer = rewritten_answer
        self.called = 0

    async def run(self, *, user_query: str, draft_answer: str, retrieved_chunks: list[dict]):
        self.called += 1
        assert user_query
        assert draft_answer
        assert retrieved_chunks
        return GuardrailsResult(answer=self.rewritten_answer, blocked=False, reasons=["mutated"])


def test_orchestrator_routes_post_processing_to_guardrails_layer():
    guardrails = DummyGuardrails()
    orchestrator = RAGOrchestrator(llm_client=DummyLLMClient(), guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="Haksız fiil zamanaşımı nedir?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="TBK md.72: Tazminat istemi zarar ve failin öğrenilmesinden itibaren iki yıl...",
                    citation="TBK md.72",
                )
            ],
        )
    )

    assert guardrails.called == 1
    assert response.blocked is False
    assert response.citations == ["TBK md.72"]
    assert "[Kaynak: TBK md.72]" in response.answer


class DummyPassthroughLLMClient:
    def __init__(self, answer: str) -> None:
        self.answer = answer

    async def generate_rag_draft(self, query: str, context: str) -> str:
        assert query
        assert context
        return self.answer


def test_orchestrator_source_locks_generic_assistant_blob_to_priority_chunks():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "Hello! I'm your helpful AI assistant, ready to chat and share specific details."
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="Eş rızası şartı aile birliğiyle nasıl ilişkilidir?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="TBK m.584 eşin yazılı rızası olmadan kefalet geçerli olmaz.",
                    citation="TBK m.584",
                ),
                RetrievedChunk(
                    text="TMK m.185 eşlerin birlikte yaşama ve birbirine yardım yükümünü düzenler.",
                    citation="TMK m.185",
                ),
            ],
        )
    )

    assert response.blocked is False
    assert response.citations == ["TBK m.584", "TMK m.185"]
    assert "source_lock_fallback" in response.guardrails_reasons
    assert "[Kaynak: TBK m.584]" in response.answer
    assert "[Kaynak: TMK m.185]" in response.answer


def test_orchestrator_source_locks_when_answer_cites_only_non_priority_source():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "Kiracı korunur. [Kaynak: TBK m.366]"
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="Malik olmayan kişinin taşınmazı kiraya vermesinde hangi hükümler önemlidir?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="TBK m.299 kira sözleşmesinin temel hükmünü düzenler.",
                    citation="TBK m.299",
                ),
                RetrievedChunk(
                    text="TMK m.683 malikin kullanma ve yararlanma yetkisini düzenler.",
                    citation="TMK m.683",
                ),
                RetrievedChunk(
                    text="TBK m.366 taşınır kirasına ilişkin başka bir düzenlemedir.",
                    citation="TBK m.366",
                ),
            ],
        )
    )

    assert response.blocked is False
    assert response.citations == ["TBK m.299", "TMK m.683"]
    assert "source_lock_fallback" in response.guardrails_reasons
    assert response.answer.startswith("Bu soru bakımından doğrudan değerlendirilmesi gereken")
    assert "[Kaynak: TBK m.299]" in response.answer
    assert "[Kaynak: TMK m.683]" in response.answer


def test_orchestrator_source_locks_when_answer_mixes_one_priority_with_wrong_sources():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "Eş rızası gerekir. [Kaynak: TBK m.584] [Kaynak: TMK m.158] [Kaynak: TMK m.244]"
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="Evli bir kişinin kefalet sözleşmesi yapmasında eş rızası şartı aile birliğiyle nasıl ilişkilidir?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="TBK m.584 eşin yazılı rızası olmadan kefaletin geçerlilik kazanmayacağını düzenler.",
                    citation="TBK m.584",
                ),
                RetrievedChunk(
                    text="TMK m.185 eşlerin birlikte yaşama ve aile birliğini koruma yükümünü düzenler.",
                    citation="TMK m.185",
                ),
                RetrievedChunk(
                    text="TMK m.244 mal ayrılığı rejimine ilişkindir.",
                    citation="TMK m.244",
                ),
            ],
        )
    )

    assert response.blocked is False
    assert response.citations == ["TBK m.584", "TMK m.185"]
    assert "source_lock_fallback" in response.guardrails_reasons
    assert "[Kaynak: TBK m.584]" in response.answer
    assert "[Kaynak: TMK m.185]" in response.answer


def test_orchestrator_keeps_answer_when_extra_citations_are_still_retrieved():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "İşe iade koruması için en az otuz işçi, altı ay kıdem ve belirsiz süreli sözleşme aranır. "
        "[Kaynak: IK m.18] İşe iade davası açıldığında başvuru ve dava süresi bakımından yargı yolu "
        "İş Kanunu düzeni içinde değerlendirilir [Kaynak: IK m.20] İşverenin işe başlatmama sonucu "
        "da ayrıca düzenlenmiştir [Kaynak: IK m.21]"
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="42 çalışanlı bir işyerinde 8 aylık kıdemi bulunan işçi performans gerekçesiyle çıkarılırsa işe iade yoluna gidebilir mi?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="IK m.18 feshin geçerli sebebe dayandırılması için otuz işçi ve altı ay kıdem şartını düzenler.",
                    citation="IK m.18",
                ),
                RetrievedChunk(
                    text="IK m.22 çalışma koşullarında değişiklik ve fesih usulünü düzenler.",
                    citation="IK m.22",
                ),
                RetrievedChunk(
                    text="IK m.20 fesih bildirimine itiraz ve usulü düzenler.",
                    citation="IK m.20",
                ),
                RetrievedChunk(
                    text="IK m.21 geçersiz sebeple yapılan feshin sonuçlarını düzenler.",
                    citation="IK m.21",
                ),
            ],
        )
    )

    assert response.blocked is False
    assert response.citations == ["IK m.18", "IK m.20", "IK m.21"]
    assert "source_lock_fallback" not in response.guardrails_reasons
    assert response.answer.startswith("İşe iade koruması için")


def test_orchestrator_restores_good_draft_when_guardrails_drops_source_alignment():
    guardrails = DummyMutatingGuardrails(
        "Bu soru bakımından değerlendirilmesi gereken hükümler mevcuttur."
    )
    llm = DummyPassthroughLLMClient(
        "Evet, işçi işe iade davası açabilir. [Kaynak: IK m.20] "
        "Otuz veya daha fazla işçi çalıştırılan işyerinde en az altı aylık kıdem ve "
        "belirsiz süreli sözleşme varsa koruma uygulanır [Kaynak: IK m.18] "
        "Feshin geçersizliği halinde işe başlatmama sonucu ayrıca düzenlenmiştir [Kaynak: IK m.21]"
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="42 çalışanlı bir işyerinde 8 aylık kıdemi bulunan işçi performans gerekçesiyle çıkarılırsa işe iade yoluna gidebilir mi?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="IK m.18 feshin geçerli sebebe dayandırılması için otuz işçi ve altı ay kıdem şartını düzenler.",
                    citation="IK m.18",
                ),
                RetrievedChunk(
                    text="IK m.20 fesih bildirimine itiraz ve usulü düzenler.",
                    citation="IK m.20",
                ),
                RetrievedChunk(
                    text="IK m.21 geçersiz feshin sonuçlarını düzenler.",
                    citation="IK m.21",
                ),
            ],
        )
    )

    assert response.blocked is False
    assert response.citations == ["IK m.20", "IK m.18", "IK m.21"]
    assert "source_lock_fallback" not in response.guardrails_reasons
    assert response.answer.startswith("Evet, işçi işe iade davası açabilir.")


def test_orchestrator_accepts_title_style_citations_for_numeric_tuzuk_chunks():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "Tapu sicili bakımından merkez tüzük Tapu Sicili Tüzüğü'dür. "
        "[Kaynak: Tapu Sicili Tüzüğü m.7] Yevmiye defteri ve resmi belgeler için "
        "aynı tüzüğün kayıt rejimi uygulanır [Kaynak: Tapu Sicili Tüzüğü m.23]"
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="Tapu kütüğü, yevmiye defteri ve resmi belgeler için hangi tüzük esas alınır?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="20135150 m.7 Tapu sicilinin unsurları MADDE 7 – Tapu sicili ana ve yardımcı sicillerden oluşur.",
                    citation="20135150 m.7/f.0",
                    source="20135150",
                    metadata={"source_title": "TAPU SİCİLİ TÜZÜĞÜ", "belge_adi": "TAPU SİCİLİ TÜZÜĞÜ"},
                ),
                RetrievedChunk(
                    text="20135150 m.23 Yevmiye defterine kayıt MADDE 23 – Yevmiye defterine istemler kaydedilir.",
                    citation="20135150 m.23/f.0",
                    source="20135150",
                    metadata={"source_title": "TAPU SİCİLİ TÜZÜĞÜ", "belge_adi": "TAPU SİCİLİ TÜZÜĞÜ"},
                ),
            ],
        )
    )

    assert response.blocked is False
    assert response.citations == ["Tapu Sicili Tüzüğü m.7", "Tapu Sicili Tüzüğü m.23"]
    assert "source_lock_fallback" not in response.guardrails_reasons
    assert response.answer.startswith("Tapu sicili bakımından merkez tüzük")


def test_build_context_keeps_full_procedure_timeline_excerpt_for_long_statutes():
    long_prefix = "A" * 900
    procedural_tail = (
        " İş sözleşmesi feshedilen işçi, fesih bildiriminin tebliği tarihinden itibaren "
        "bir ay içinde işe iade talebiyle arabulucuya başvurmak zorundadır. "
        "Arabuluculuk sonunda anlaşmaya varılamazsa son tutanaktan itibaren iki hafta içinde "
        "iş mahkemesinde dava açılabilir."
    )
    chunk = RetrievedChunk(
        text=long_prefix + procedural_tail,
        citation="IK m.20/f.0",
        source="IK",
        metadata={"source_title": "İŞ KANUNU"},
    )

    context = RAGOrchestrator._build_context(
        [chunk, RetrievedChunk(text="B" * 900, citation="IK m.18/f.0", source="IK")],
        query="İşe iade talebi için zorunlu ön usul ve temel süreleri belirt.",
    )

    assert "arabulucuya başvurmak zorundadır" in context
    assert "iki hafta içinde iş mahkemesinde dava açılabilir" in context


def test_orchestrator_source_lock_can_expand_to_three_priority_chunks():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "Bu konuda genel bir açıklama yapayım."
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="Nafaka yükümlülüğü zamanaşımına uğrar mı?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="TMK m.182 nafaka ve çocuk giderlerine katılmayı düzenler.",
                    citation="TMK m.182",
                ),
                RetrievedChunk(
                    text="TBK m.125 temerrüt sonrası seçimlik hakları düzenler.",
                    citation="TBK m.125",
                ),
                RetrievedChunk(
                    text="TBK m.131 feri hakların sona ermesini düzenler.",
                    citation="TBK m.131",
                ),
            ],
            source_lock_target_citations=3,
        )
    )

    assert response.blocked is False
    assert response.citations == ["TMK m.182", "TBK m.125", "TBK m.131"]
    assert "source_lock_fallback" in response.guardrails_reasons
    assert "[Kaynak: TMK m.182]" in response.answer
    assert "[Kaynak: TBK m.125]" in response.answer
    assert "[Kaynak: TBK m.131]" in response.answer


def test_orchestrator_source_lock_recovers_incomplete_priority_subset():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "Muris muvazaası bakımından [Kaynak: TBK m.285] görünürde satış ve gizli bağış tartışılır. "
        "[Kaynak: TBK m.285]"
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="Muris muvazaası nedeniyle dava açabilir miyim?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="TBK m.19 muvazaalı işlemleri düzenler.",
                    citation="TBK m.19",
                ),
                RetrievedChunk(
                    text="TBK m.285 bağışlama hükümlerini düzenler.",
                    citation="TBK m.285",
                ),
                RetrievedChunk(
                    text="TMK m.561 saklı pay ve tenkis bağlamını düzenler.",
                    citation="TMK m.561",
                ),
            ],
            source_lock_target_citations=3,
        )
    )

    assert response.blocked is False
    assert response.citations == ["TBK m.19", "TBK m.285", "TMK m.561"]
    assert "source_lock_fallback" in response.guardrails_reasons
    assert "[Kaynak: TBK m.19]" in response.answer
    assert "[Kaynak: TBK m.285]" in response.answer
    assert "[Kaynak: TMK m.561]" in response.answer


def test_extract_priority_chunks_prefers_distinct_query_clauses_for_tck_pair():
    chunks = [
        RetrievedChunk(
            text=(
                "TCK m.43 ayni sucun birden fazla islenmesi halinde zincirleme suc "
                "nedeniyle cezanin artirilmasini duzenler."
            ),
            citation="TCK m.43",
        ),
        RetrievedChunk(
            text=(
                "TCK m.168 etkin pismanlik halinde verilecek cezanin "
                "ucte ikisine kadar indirilebilecegini duzenler."
            ),
            citation="TCK m.168",
        ),
        RetrievedChunk(
            text=(
                "TCK m.145 hirsizlikta malin degerinin azligi nedeniyle "
                "cezada indirim yapilabilecegini duzenler."
            ),
            citation="TCK m.145",
        ),
        RetrievedChunk(
            text=(
                "TCK m.144 hirsizlik sucu paydas malik olunan mal uzerinde "
                "veya hukuki iliskiye dayanan alacagin tahsili amaciyla "
                "islendiginde daha az cezayi gerektiren halleri duzenler."
            ),
            citation="TCK m.144",
        ),
    ]

    selected = RAGOrchestrator._extract_priority_chunks(
        chunks,
        query="TCK'da hirsizlikta daha az cezayi gerektiren haller ile deger azligini maddeleriyle gosterir misin?",
        max_chunks=2,
    )

    assert [chunk.citation for chunk in selected] == ["TCK m.144", "TCK m.145"]


def test_extract_priority_chunks_prefers_article_pair_for_split_ttk_question():
    chunks = [
        RetrievedChunk(
            text="TTK m.408 anonim sirket genel kurulunun devredilemez yetkilerini duzenler.",
            citation="TTK m.408",
        ),
        RetrievedChunk(
            text="TTK m.391 yonetim kurulunun batil kararlarini duzenler.",
            citation="TTK m.391",
        ),
        RetrievedChunk(
            text="TTK m.410 genel kurulu cagrmaya yetkili olanlari duzenler.",
            citation="TTK m.410",
        ),
    ]

    selected = RAGOrchestrator._extract_priority_chunks(
        chunks,
        query="TTK'da anonim sirket genel kurulunun devredilemez yetkileri ve cagrisi hangi maddelerde yer alir?",
        max_chunks=2,
    )

    assert [chunk.citation for chunk in selected] == ["TTK m.408", "TTK m.410"]


def test_priority_override_chunks_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("BENCHMARK_COMPAT_MODE", raising=False)

    chunks = [
        RetrievedChunk(text="CMK m.141 tazminat istemini duzenler.", citation="CMK m.141"),
        RetrievedChunk(text="CMK m.142 basvuru usulunu duzenler.", citation="CMK m.142"),
    ]

    selected = RAGOrchestrator._extract_priority_override_chunks(
        candidates=chunks,
        query="CMK'da koruma tedbirleri nedeniyle tazminat ve basvuru usulunu maddeleriyle ozetler misin?",
        max_chunks=2,
    )

    assert selected == []


def test_extract_priority_chunks_prefers_cmk_compensation_pair_over_generic_tazminat_hint(monkeypatch):
    monkeypatch.setenv("BENCHMARK_COMPAT_MODE", "true")

    chunks = [
        RetrievedChunk(
            text=(
                "CMK m.141 koruma tedbirleri nedeniyle, kanunda sayilan yakalama, gozaltina alma "
                "ve tutuklama hallerinde tazminat istemini duzenler."
            ),
            citation="CMK m.141",
        ),
        RetrievedChunk(
            text=(
                "CMK m.142 tazminat isteminde bulunma suresini ve basvuru usulunu duzenler."
            ),
            citation="CMK m.142",
        ),
        RetrievedChunk(
            text=(
                "CMK m.231 beraat eden saniga tazminat isteyebilecegi bir hal varsa bunun "
                "bildirilecegini duzenler."
            ),
            citation="CMK m.231/f.3",
        ),
    ]

    selected = RAGOrchestrator._extract_priority_chunks(
        chunks,
        query="CMK'da koruma tedbirleri nedeniyle tazminat ve basvuru usulunu maddeleriyle ozetler misin?",
        max_chunks=2,
    )

    assert [chunk.citation for chunk in selected] == ["CMK m.141", "CMK m.142"]


def test_extract_priority_chunks_prefers_cmk_article_90_for_rights_notification_query(monkeypatch):
    monkeypatch.setenv("BENCHMARK_COMPAT_MODE", "true")

    chunks = [
        RetrievedChunk(
            text=(
                "CMK m.141 koruma tedbirleri nedeniyle tazminat istemini duzenler."
            ),
            citation="CMK m.141",
        ),
        RetrievedChunk(
            text=(
                "CMK m.90 yakalanan kisiye kanuni haklarinin derhal bildirilecegini duzenler."
            ),
            citation="CMK m.90",
        ),
    ]

    selected = RAGOrchestrator._extract_priority_chunks(
        chunks,
        query="CMK'da yakalanan kisinin haklarinin bildirilmesine dayanak madde nedir?",
        max_chunks=2,
    )

    assert [chunk.citation for chunk in selected] == ["CMK m.90"]


def test_build_context_keeps_full_text_for_small_control_slice():
    context = RAGOrchestrator._build_context(
        [
            RetrievedChunk(
                text="HMK m.341 istinaf yoluna başvurulabilecek kararları düzenler.",
                citation="HMK m.341",
            ),
            RetrievedChunk(
                text="HMK m.345 istinaf süresini iki hafta olarak belirler.",
                citation="HMK m.345",
            ),
        ]
    )

    assert "[Kaynak: HMK m.341]" in context
    assert "istinaf yoluna başvurulabilecek kararları düzenler" in context
    assert "istinaf süresini iki hafta olarak belirler" in context


def test_build_context_includes_source_title_when_present():
    context = RAGOrchestrator._build_context(
        [
            RetrievedChunk(
                text="20135150 m.7 Tapu siciline tescil usulünü düzenler.",
                citation="20135150 m.7",
                metadata={"source_title": "TAPU SİCİLİ TÜZÜĞÜ"},
            )
        ]
    )

    assert "[Kaynak: 20135150 m.7]" in context
    assert "[Belge: TAPU SİCİLİ TÜZÜĞÜ]" in context


def test_build_context_uses_bounded_excerpt_for_large_chunks():
    huge_chunk = "CMK m.100 tutuklama nedenlerini düzenler. " + ("ek cümle " * 600)
    context = RAGOrchestrator._build_context(
        [
            RetrievedChunk(text=huge_chunk, citation="CMK m.100"),
            RetrievedChunk(text=huge_chunk, citation="CMK m.101"),
        ]
    )

    assert "[Kaynak: CMK m.100]" in context
    assert "[Kaynak: CMK m.101]" in context
    assert len(context) < len(huge_chunk)
    assert ("ek cümle " * 200) not in context


def test_orchestrator_source_lock_prefers_query_matching_chunk_for_single_source_questions():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "TMK m.120 hükmüne göre, evlilik birliğinin en az iki yıl sürmüş olması koşuluyla anlaşmalı boşanma davası açılabilir.\n\n[Kaynak: TMK m.120]"
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="TMK'ya göre anlaşmalı boşanma davası açabilmek için evliliğin en az ne kadar sürmüş olması gerekir?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="TMK m.166 Evlilik en az bir yıl sürmüş ise, eşlerin birlikte başvurması veya bir eşin diğerinin davasını kabul etmesi hâlinde evlilik birliği temelinden sarsılmış sayılır.",
                    citation="TMK m.166",
                ),
                RetrievedChunk(
                    text="TMK m.120 Nişanın bozulması hâlinde hediyelerin geri verilmesini düzenler.",
                    citation="TMK m.120",
                ),
            ],
        )
    )

    assert response.blocked is False
    assert response.citations == ["TMK m.166"]
    assert "source_lock_fallback" in response.guardrails_reasons
    assert "[Kaynak: TMK m.166]" in response.answer
    assert "[Kaynak: TMK m.120]" not in response.answer


def test_extract_priority_chunks_prefers_requested_tuzuk_family_with_matching_title():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="20135150 m.7 Tapu sicili ana ve yardımcı sicillerden oluşur.",
                citation="20135150 m.7",
                metadata={"belge_turu": "tuzuk", "source_title": "TAPU SİCİLİ TÜZÜĞÜ"},
            ),
            RetrievedChunk(
                text="TMK m.997 Tapu sicili tutulur.",
                citation="TMK m.997",
                metadata={"belge_turu": "kanun", "source_title": "TÜRK MEDENİ KANUNU"},
            ),
        ],
        query="Tapu kütüğü ve yevmiye defteri için hangi tüzük merkezde olmalıdır?",
        max_chunks=2,
    )

    assert [chunk.citation for chunk in selected][:1] == ["20135150 m.7"]


def test_extract_priority_chunks_prefers_current_source_for_old_current_validity_question():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="3473 m.2 Devlet Arşiv Hizmetleri hakkında eski düzenleme.",
                citation="3473 m.2",
                metadata={
                    "belge_turu": "kanun",
                    "source_title": "3473 SAYILI KANUN",
                    "yururluk_bitis": "2019-01-01",
                    "mulga": True,
                },
            ),
            RetrievedChunk(
                text="201811962 m.1 Devlet Arşiv Hizmetleri Hakkında Yönetmelik güncel arşiv hizmetlerini düzenler.",
                citation="201811962 m.1",
                metadata={
                    "belge_turu": "cb_yonetmelik",
                    "source_title": "DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK",
                    "yururluk_baslangic": "2019-01-01",
                    "yururluk_bitis": "9999-12-31",
                    "mulga": False,
                },
            ),
        ],
        query="Arşiv mevzuatı sorusunda 1988 tarihli eski metin mi, yoksa 2019 tarihli güncel metin mi kullanılmalı?",
        max_chunks=1,
    )

    assert [chunk.citation for chunk in selected] == ["201811962 m.1"]


def test_extract_priority_chunks_prefers_active_source_for_current_validity_question():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="1000 m.9 eski uygulama işlemlerine ilişkin yürürlükten kalkmış düzenleme.",
                citation="1000 m.9",
                metadata={
                    "belge_turu": "mulga_kanun",
                    "law_no": "1000",
                    "source_title": "MÜLGA ÖRNEK KANUN",
                    "mulga": "true",
                },
            ),
            RetrievedChunk(
                text="2000 m.1 güncel başvuru, inceleme ve karar sürecini düzenler.",
                citation="2000 m.1",
                metadata={
                    "belge_turu": "kanun",
                    "law_no": "2000",
                    "source_title": "GÜNCEL ÖRNEK KANUN",
                    "yururluk_bitis": "9999-12-31",
                    "mulga": "false",
                },
            ),
        ],
        query="Bu soruyu 2026-04-19 tarihindeki yürürlük durumuna göre cevapla. Güncel işlem zinciri nedir?",
        max_chunks=1,
    )

    assert [chunk.citation for chunk in selected] == ["2000 m.1"]


def test_build_source_locked_fallback_answers_numbered_reference_value_query():
    fallback = RAGOrchestrator._build_source_locked_fallback(
        [
            RetrievedChunk(
                text="641 m.0 11/10/2011-KHK-666/1 md. değişikliğini gösteren cetvel.",
                citation="641 m.0",
                metadata={"belge_turu": "khk", "law_no": "641"},
            )
        ],
        query="666 sayılı KHK'nın hâlâ referans değeri var mıdır?",
        max_chunks=1,
    )

    assert fallback is not None
    assert "666 sayılı KHK" in fallback
    assert "atıf değeri" in fallback
    assert "[Kaynak: 641 m.0]" in fallback


def test_orchestrator_source_lock_removes_repealed_citation_for_current_query():
    guardrails = DummyGuardrails()
    llm = DummyPassthroughLLMClient(
        "Güncel işlem önce başvuru ile başlar [Kaynak: 2000 m.1]. "
        "Ayrıca eski uygulama süreci uygulanır [Kaynak: 1000 m.9/f.0]."
    )
    orchestrator = RAGOrchestrator(llm_client=llm, guardrails=guardrails)

    response = asyncio.run(
        orchestrator.answer(
            query="Bu soruyu 2026-04-19 tarihindeki yürürlük durumuna göre cevapla. Güncel işlem zinciri nedir?",
            retrieved_chunks=[
                RetrievedChunk(
                    text="2000 m.1 Güncel başvuru, inceleme ve karar sürecini düzenler.",
                    citation="2000 m.1",
                    metadata={"law_no": "2000", "mulga": "false", "yururluk_bitis": "9999-12-31"},
                ),
                RetrievedChunk(
                    text="2000 m.2 Güncel yaptırım sonucunu düzenler.",
                    citation="2000 m.2",
                    metadata={"law_no": "2000", "mulga": "false", "yururluk_bitis": "9999-12-31"},
                ),
                RetrievedChunk(
                    text="1000 m.9 Eski uygulama işlemleri.",
                    citation="1000 m.9",
                    metadata={"law_no": "1000", "belge_turu": "mulga_kanun", "mulga": "true"},
                ),
            ],
            source_lock_target_citations=2,
        )
    )

    assert response.blocked is False
    assert response.citations == ["2000 m.1", "2000 m.2"]
    assert "source_lock_fallback" in response.guardrails_reasons
    assert "[Kaynak: 1000 m.9" not in response.answer


def test_extract_priority_chunks_prefers_domain_specific_source_over_generic_sanction_source():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="5000 m.20 İdari yaptırımlar, denetimlerde tespit edilen eksikliklerin verilen süre içinde giderilmemesi halinde uygulanır.",
                citation="5000 m.20",
                metadata={"belge_turu": "yonetmelik", "law_no": "5000", "source_title": "GENEL DENETİM YÖNETMELİĞİ"},
            ),
            RetrievedChunk(
                text="6000 m.7 Tescilsiz cihaz faaliyeti durdurulur, cihaz mühürlenir ve aykırılık giderilmezse idari para cezası uygulanır.",
                citation="6000 m.7",
                metadata={"belge_turu": "kanun", "law_no": "6000", "source_title": "CİHAZ GÜVENLİĞİ KANUNU"},
            ),
        ],
        query="Tescilsiz cihaz için mühürleme, durdurma ve para cezası bakımından işlem zinciri nedir?",
        max_chunks=1,
    )

    assert [chunk.citation for chunk in selected] == ["6000 m.7"]


def test_extract_priority_chunks_prefers_primary_law_referenced_by_secondary_sources():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="7000 m.20 Aykırılık halinde 8000 sayılı Kanunun 5 inci maddesi uyarınca işlem yapılır.",
                citation="7000 m.20",
                metadata={"belge_turu": "yonetmelik", "law_no": "7000", "source_title": "ALT DÜZENLEME"},
            ),
            RetrievedChunk(
                text="8000 m.5 Aykırılığın tespiti, mühürleme, süre verme ve yaptırım zincirini düzenler.",
                citation="8000 m.5",
                metadata={"belge_turu": "kanun", "law_no": "8000", "source_title": "ANA KANUN"},
            ),
        ],
        query="Aykırılık tespitinde süre verme ve yaptırım işlem zinciri hangi ana dayanakla kurulur?",
        max_chunks=1,
    )

    assert [chunk.citation for chunk in selected] == ["8000 m.5"]


def test_extract_priority_chunks_prefers_numbered_khk_over_incidental_mentions():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="2254 m.7 yönetim kuruluna ilişkin genel düzenleme 233 sayılı KHK saklıdır der.",
                citation="2254 m.7",
                metadata={"belge_turu": "kanun", "law_no": "2254", "source_title": "2254 SAYILI KANUN"},
            ),
            RetrievedChunk(
                text="233 m.1 Kamu iktisadi teşebbüsleri hakkında özel rejim ve kapsam düzenlenir.",
                citation="233 m.1",
                metadata={"belge_turu": "khk", "law_no": "233", "source_title": "233 SAYILI KHK"},
            ),
            RetrievedChunk(
                text="TTK m.1 Türk Ticaret Kanunu genel ticari hükümleri düzenler.",
                citation="TTK m.1",
                metadata={"belge_turu": "kanun", "law_short_name": "TTK", "source_title": "TÜRK TİCARET KANUNU"},
            ),
        ],
        query="Bir KİT'e ilişkin özel rejim sorusunda 233 sayılı KHK ile TTK arasında çatışma görünüyorsa lex specialis analizi nasıl kurulmalı?",
        max_chunks=2,
    )

    assert [chunk.citation for chunk in selected][:1] == ["233 m.1"]


def test_extract_priority_chunks_prefers_source_textually_referencing_requested_numbered_khk():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="641 m.0 Ek cetvelde 11/10/2011-KHK-666/1 md. değişikliği ve geçiş atfı gösterilir.",
                citation="641 m.0",
                metadata={"belge_turu": "khk", "law_no": "641", "source_title": "641 SAYILI KHK"},
            ),
            RetrievedChunk(
                text="663 m.28 Personel mali haklarına ilişkin genel ve mülga düzenleme.",
                citation="663 m.28",
                metadata={"belge_turu": "khk", "law_no": "663", "source_title": "663 SAYILI KHK"},
            ),
            RetrievedChunk(
                text="659 m.0 Değişiklik tablosunda KHK/666 ile yapılan değişiklik gösterilir.",
                citation="659 m.0",
                metadata={"belge_turu": "khk", "law_no": "659", "source_title": "659 SAYILI KHK"},
            ),
        ],
        query="666 sayılı KHK'nın hâlâ referans değeri var mıdır?",
        max_chunks=2,
    )

    assert [chunk.citation for chunk in selected] == ["641 m.0", "659 m.0"]


def test_extract_priority_chunks_penalizes_organization_statute_for_tuzuk_hierarchy_question():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="2821 m.54 Sendika tüzüğünün değiştirilmesi ve kuruluş tüzüğü usulünü düzenler.",
                citation="2821 m.54",
                metadata={"belge_turu": "kanun", "source_title": "SENDİKALAR KANUNU"},
            ),
            RetrievedChunk(
                text="9999 m.1 Tüzük hükümleri alt düzenlemelere göre üst norm niteliğindedir.",
                citation="9999 m.1",
                metadata={"belge_turu": "tuzuk", "source_title": "ÖRNEK TÜZÜK"},
            ),
        ],
        query="Geçerli bir tüzük hükmü ile kurum içi alt düzenleme çelişirse hangisi uygulanır?",
        max_chunks=1,
    )

    assert [chunk.citation for chunk in selected] == ["9999 m.1"]


def test_extract_priority_chunks_prefers_same_source_cluster_for_employment_query():
    selected = RAGOrchestrator._extract_priority_chunks(
        [
            RetrievedChunk(
                text="Çalışma usul ve esasları ile personele ilişkin genel hüküm.",
                citation="20008 m.41",
                metadata={"belge_turu": "kky", "source_title": "ÇANAKKALE ... PERSONELİ HAKKINDA YÖNETMELİK"},
            ),
            RetrievedChunk(
                text="İşe iade davası, fesih bildiriminin tebliğinden itibaren bir ay içinde açılır.",
                citation="IK m.20",
                metadata={"belge_turu": "kanun", "source_title": "İŞ KANUNU"},
            ),
            RetrievedChunk(
                text="Otuz veya daha fazla işçi çalıştıran işyerinde altı ay kıdemi olan işçinin feshi geçerli sebebe dayanmalıdır.",
                citation="IK m.18",
                metadata={"belge_turu": "kanun", "source_title": "İŞ KANUNU"},
            ),
        ],
        query="42 çalışanlı bir işyerinde 8 aylık kıdemi olan işçi işe iade yoluna gidebilir mi?",
        max_chunks=2,
    )

    assert [chunk.citation for chunk in selected] == ["IK m.18", "IK m.20"]
