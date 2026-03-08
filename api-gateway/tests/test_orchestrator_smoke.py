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
