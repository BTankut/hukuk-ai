from __future__ import annotations

import asyncio
from types import SimpleNamespace

from config import Settings
from llm.client import ChatMessage, LLMClient


class CapturingLLMClient(LLMClient):
    def __init__(self) -> None:
        super().__init__(Settings())
        self.calls: list[tuple[list[ChatMessage], float, int | None]] = []

    async def chat(self, messages, temperature: float = 0.1, max_tokens: int | None = None) -> str:  # type: ignore[override]
        self.calls.append((list(messages), temperature, max_tokens))
        return "ok"


def test_generate_rag_draft_uses_wave2_prompt_rules_with_context() -> None:
    client = CapturingLLMClient()

    asyncio.run(
        client.generate_rag_draft(
            query="TMK m.706 ile TBK m.237 birlikte nasıl değerlendirilir?",
            context="[Kaynak: TMK m.706]\nResmi şekil gerekir.\n\n[Kaynak: TBK m.237]\nSatış sözleşmesi...",
        )
    )

    messages, temperature, max_tokens = client.calls[-1]
    assert temperature == 0.0
    assert max_tokens is None
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "Belge ailesini ve prefixlerini asla karıştırma" in messages[0].content
    assert "Cross-law sorularda" in messages[0].content
    assert "Önce kısa sonucu ver" in messages[0].content
    assert "Soruda açık madde numarası geçiyorsa" in messages[1].content
    assert "[Kaynak: TMK m.706]" in messages[1].content
    assert "TMK m.706 ile TBK m.237" in messages[1].content


def test_generate_rag_draft_uses_refusal_prompt_without_context() -> None:
    client = CapturingLLMClient()

    asyncio.run(client.generate_rag_draft(query="Kıdem tazminatı nasıl hesaplanır?", context=""))

    messages, _temperature, max_tokens = client.calls[-1]
    assert max_tokens is None
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "bilgi üretme" in messages[0].content
    assert "Kaynak olmadan yanıt verme" in messages[1].content
    assert "Kıdem tazminatı nasıl hesaplanır?" in messages[1].content


def test_extract_text_parses_stringified_response_wrapper() -> None:
    wrapped = (
        "response=[{'role': 'assistant', 'content': \"TBK m.584 ve TMK m.185 birlikte "
        "değerlendirilir. [Kaynak: TBK m.584] [Kaynak: TMK m.185]\"}] "
        "llm_output=None output_data=None"
    )

    assert (
        LLMClient._extract_text(wrapped)
        == "TBK m.584 ve TMK m.185 birlikte değerlendirilir. [Kaynak: TBK m.584] [Kaynak: TMK m.185]"
    )


def test_extract_text_keeps_plain_string_response() -> None:
    plain = "TBK m.49 haksız fiili düzenler. [Kaynak: TBK m.49]"

    assert LLMClient._extract_text(plain) == plain


def test_extract_text_parses_wrapper_with_metadata_tail() -> None:
    wrapped = (
        "response=[{'role': 'assistant', 'content': 'TBK m.49 metnine göre kusurlu ve hukuka aykırı "
        "fiille başkasına zarar veren, bu zararı gidermekle yükümlüdür. [Kaynak: TBK m.49]'}] "
        "llm_output=None output_data=None log=None state=None tool_calls=None reasoning_content=None "
        "llm_metadata={'response_metadata': {'token_usage': {'completion_tokens': 102}}}"
    )

    assert (
        LLMClient._extract_text(wrapped)
        == "TBK m.49 metnine göre kusurlu ve hukuka aykırı fiille başkasına zarar veren, bu zararı "
        "gidermekle yükümlüdür. [Kaynak: TBK m.49]"
    )


def test_extract_text_parses_object_content_wrapper() -> None:
    wrapped = (
        "response=[{'role': 'assistant', 'content': 'TBK m.49 metnine göre kusurlu ve hukuka aykırı "
        "fiille başkasına zarar veren, bu zararı gidermekle yükümlüdür. [Kaynak: TBK m.49]'}] "
        "llm_output=None output_data=None log=None state=None"
    )

    assert (
        LLMClient._extract_text(SimpleNamespace(content=wrapped))
        == "TBK m.49 metnine göre kusurlu ve hukuka aykırı fiille başkasına zarar veren, bu zararı "
        "gidermekle yükümlüdür. [Kaynak: TBK m.49]"
    )


def test_build_request_payload_and_generation_contract_are_deterministic() -> None:
    settings = Settings(
        dgx_model="Qwen/test",
        dgx_top_p=0.9,
        dgx_top_k=40,
        dgx_seed=3407,
        dgx_request_timeout_seconds=123.0,
        dgx_retry_count=0,
    )
    client = LLMClient(settings)
    messages = [ChatMessage(role="user", content="TBK m.49 nedir?")]

    request_payload = client._build_request_payload(messages=messages, temperature=0.1, max_tokens=256)
    generation_contract = client._build_generation_contract(temperature=0.1, max_tokens=256)

    assert request_payload["model"] == "Qwen/test"
    assert request_payload["messages"] == [{"role": "user", "content": "TBK m.49 nedir?"}]
    assert request_payload["temperature"] == 0.1
    assert request_payload["max_tokens"] == 256
    assert request_payload["top_p"] == 0.9
    assert request_payload["seed"] == 3407
    assert request_payload["extra_body"]["top_k"] == 40
    assert request_payload["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False
    assert generation_contract == {
        "temperature": 0.1,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 256,
        "stop": None,
        "seed": 3407,
        "retry_count": 0,
        "timeout_seconds": 123.0,
        "streaming": False,
        "enable_thinking": False,
    }


def test_build_request_payload_and_generation_contract_enable_thinking_when_configured() -> None:
    settings = Settings(
        dgx_model="Qwen/test",
        dgx_top_p=0.9,
        dgx_top_k=40,
        dgx_seed=3407,
        dgx_request_timeout_seconds=123.0,
        dgx_retry_count=0,
        dgx_enable_thinking=True,
    )
    client = LLMClient(settings)
    messages = [ChatMessage(role="user", content="TBK m.49 nedir?")]

    request_payload = client._build_request_payload(messages=messages, temperature=0.1, max_tokens=256)
    generation_contract = client._build_generation_contract(temperature=0.1, max_tokens=256)

    assert request_payload["extra_body"]["chat_template_kwargs"]["enable_thinking"] is True
    assert generation_contract["enable_thinking"] is True


def test_build_rag_messages_generalizes_beyond_core_law_families() -> None:
    messages = LLMClient._build_rag_messages(
        query="Tapu sicili için hangi tüzük merkezde olmalıdır?",
        context="[Kaynak: 20135150 m.7]\n[Belge: TAPU SİCİLİ TÜZÜĞÜ]\n...",
    )

    system_prompt = messages[0].content
    assert "mevzuat ailesine" in system_prompt
    assert "tüzük" in system_prompt
    assert "[Belge: ...]" in system_prompt


def test_build_rag_messages_adds_procedure_guardrails_for_timeline_questions() -> None:
    messages = LLMClient._build_rag_messages(
        query="İşe iade talebi için zorunlu ön usul ve temel süreler nelerdir?",
        context="[Kaynak: IK m.20]\n[Belge: İŞ KANUNU]\n...",
    )

    system_prompt = messages[0].content
    assert "Ön şart/ön usul ile dava aşamasını birbirine karıştırma." in system_prompt
    assert "Kaynakta arabulucuya başvuru zorunlu deniyorsa" in system_prompt
    assert "Süreleri yalnız kaynakta açıkça geçtiği şekliyle ver" in system_prompt


def test_extract_raw_answer_object_keeps_unprojected_content() -> None:
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    role="assistant",
                    content="response=[{'role': 'assistant', 'content': 'TBK m.49 [Kaynak: TBK m.49]'}] llm_output=None",
                ),
                finish_reason="stop",
            )
        ]
    )

    assert LLMClient._extract_raw_answer_object(response) == {
        "role": "assistant",
        "content": "response=[{'role': 'assistant', 'content': 'TBK m.49 [Kaynak: TBK m.49]'}] llm_output=None",
        "extracted_text": "TBK m.49 [Kaynak: TBK m.49]",
        "finish_reason": "stop",
    }
