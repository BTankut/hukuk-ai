from __future__ import annotations

import asyncio
from types import SimpleNamespace

from config import Settings
from guardrails.pipeline import GuardrailsPipeline


def test_guardrails_pipeline_does_not_block_valid_legal_answer_in_safe_default():
    settings = Settings(
        guardrails_enabled=False,
        guardrails_strict_mode=False,
        presidio_enabled=False,
    )
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
    settings = Settings(
        guardrails_enabled=False,
        guardrails_strict_mode=False,
        presidio_enabled=False,
    )
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
    settings = Settings(
        guardrails_enabled=False,
        guardrails_strict_mode=False,
        presidio_enabled=False,
    )
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


def test_guardrails_pipeline_fail_opens_on_english_false_positive_refusal(monkeypatch):
    settings = Settings(
        guardrails_enabled=True,
        guardrails_strict_mode=False,
        presidio_enabled=False,
    )
    pipeline = GuardrailsPipeline(settings=settings)

    async def _fake_guardrails(*_args, **_kwargs):
        return (
            "response=[{'role': 'assistant', 'content': \"I'm sorry, I can't respond to that.\"}] "
            "llm_output=None output_data=None"
        )

    monkeypatch.setattr(pipeline, "_generate_with_rails_guarded", _fake_guardrails)

    result = asyncio.run(
        pipeline.run(
            user_query="TBK 49 nedir?",
            draft_answer="TBK m.49 haksiz fiil sorumlulugunun genel kuralini duzenler. [Kaynak: TBK m.49]",
            retrieved_chunks=[{"text": "...", "citation": "TBK m.49"}],
        )
    )

    assert result.blocked is False
    assert result.answer.endswith("[Kaynak: TBK m.49]")
    assert "guardrails_fail_open_refusal_fallback" in result.reasons


def test_guardrails_extract_text_parses_wrapper_with_metadata_tail():
    wrapped = (
        "response=[{'role': 'assistant', 'content': 'TBK m.49 uyarınca kusurlu ve hukuka aykırı "
        "fiille başkasına zarar veren, bu zararı gidermekle yükümlüdür. [Kaynak: TBK m.49]'}] "
        "llm_output=None output_data=None log=None state=None tool_calls=None reasoning_content=None "
        "llm_metadata={'response_metadata': {'token_usage': {'completion_tokens': 42}}}"
    )

    assert GuardrailsPipeline._extract_text(wrapped) == (
        "TBK m.49 uyarınca kusurlu ve hukuka aykırı fiille başkasına zarar veren, "
        "bu zararı gidermekle yükümlüdür. [Kaynak: TBK m.49]"
    )


def test_guardrails_extract_text_parses_object_content_wrapper():
    wrapped = (
        "response=[{'role': 'assistant', 'content': 'TBK m.49 uyarınca kusurlu ve hukuka aykırı "
        "fiille başkasına zarar veren, bu zararı gidermekle yükümlüdür. [Kaynak: TBK m.49]'}] "
        "llm_output=None output_data=None log=None state=None"
    )

    assert GuardrailsPipeline._extract_text(SimpleNamespace(content=wrapped)) == (
        "TBK m.49 uyarınca kusurlu ve hukuka aykırı fiille başkasına zarar veren, "
        "bu zararı gidermekle yükümlüdür. [Kaynak: TBK m.49]"
    )


def test_guardrails_extract_text_parses_dict_response_wrapper():
    wrapped = (
        "response=[{'role': 'assistant', 'content': 'TBK m.49 uyarınca kusurlu ve hukuka aykırı "
        "fiille başkasına zarar veren, bu zararı gidermekle yükümlüdür. [Kaynak: TBK m.49]'}] "
        "llm_output=None output_data=None log=None state=None"
    )

    assert GuardrailsPipeline._extract_text({"response": wrapped}) == (
        "TBK m.49 uyarınca kusurlu ve hukuka aykırı fiille başkasına zarar veren, "
        "bu zararı gidermekle yükümlüdür. [Kaynak: TBK m.49]"
    )
