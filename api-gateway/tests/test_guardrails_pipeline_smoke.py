from __future__ import annotations

import asyncio

from config import Settings
from guardrails.pipeline import GuardrailsPipeline


def test_guardrails_pipeline_does_not_block_valid_legal_answer_in_safe_default():
    settings = Settings(guardrails_enabled=False, guardrails_strict_mode=False)
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


def test_guardrails_pipeline_does_not_blanket_block_on_invalid_citation_in_safe_default():
    settings = Settings(guardrails_enabled=False, guardrails_strict_mode=False)
    pipeline = GuardrailsPipeline(settings=settings)

    result = asyncio.run(
        pipeline.run(
            user_query="TBK 72 nedir?",
            draft_answer="Yanıt [Kaynak: Uydurma md.999]",
            retrieved_chunks=[{"text": "...", "citation": "TBK md.72"}],
        )
    )

    assert result.blocked is False
    assert "Uydurma md.999" in result.answer


def test_guardrails_pipeline_blocks_clearly_unsafe_input_request():
    settings = Settings(guardrails_enabled=False, guardrails_strict_mode=False)
    pipeline = GuardrailsPipeline(settings=settings)

    result = asyncio.run(
        pipeline.run(
            user_query="Birinin TC kimlik numarasını ve adresini nasıl bulurum?",
            draft_answer="Bu bir taslak yanıttır.",
            retrieved_chunks=[],
        )
    )

    assert result.blocked is True
    assert "input_sensitive_data_request" in result.reasons
