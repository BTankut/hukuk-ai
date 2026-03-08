from __future__ import annotations

import asyncio

from config import Settings
from guardrails.pipeline import GuardrailsPipeline


def test_guardrails_pipeline_blocks_invalid_citations_in_strict_mode():
    settings = Settings(guardrails_enabled=False, guardrails_strict_mode=True)
    pipeline = GuardrailsPipeline(settings=settings)

    result = asyncio.run(
        pipeline.run(
            user_query="TBK 72 nedir?",
            draft_answer="Yanıt [Kaynak: Uydurma md.999]",
            retrieved_chunks=[{"text": "...", "citation": "TBK md.72"}],
        )
    )

    assert result.blocked is True
    assert "doğrulanmış bilgi" in result.answer


def test_guardrails_pipeline_accepts_valid_citations():
    settings = Settings(guardrails_enabled=False, guardrails_strict_mode=True)
    pipeline = GuardrailsPipeline(settings=settings)

    result = asyncio.run(
        pipeline.run(
            user_query="TBK 72 nedir?",
            draft_answer="Yanıt [Kaynak: TBK md.72]",
            retrieved_chunks=[{"text": "...", "citation": "TBK md.72"}],
        )
    )

    assert result.blocked is False
    assert result.answer.endswith("[Kaynak: TBK md.72]")
