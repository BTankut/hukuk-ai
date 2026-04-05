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


def test_extract_priority_chunks_prefers_cmk_compensation_pair_over_generic_tazminat_hint():
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


def test_extract_priority_chunks_prefers_cmk_article_90_for_rights_notification_query():
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
