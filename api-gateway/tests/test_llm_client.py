from __future__ import annotations

import asyncio
from types import SimpleNamespace

from config import Settings
from llm.client import ChatMessage, LLMClient


class CapturingLLMClient(LLMClient):
    def __init__(self) -> None:
        super().__init__(Settings())
        self.calls: list[tuple[list[ChatMessage], float]] = []

    async def chat(self, messages, temperature: float = 0.1) -> str:  # type: ignore[override]
        self.calls.append((list(messages), temperature))
        return "ok"


def test_generate_rag_draft_uses_wave2_prompt_rules_with_context() -> None:
    client = CapturingLLMClient()

    asyncio.run(
        client.generate_rag_draft(
            query="TMK m.706 ile TBK m.237 birlikte nasıl değerlendirilir?",
            context="[Kaynak: TMK m.706]\nResmi şekil gerekir.\n\n[Kaynak: TBK m.237]\nSatış sözleşmesi...",
        )
    )

    messages, temperature = client.calls[-1]
    assert temperature == 0.1
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "Kanun prefixlerini asla karıştırma" in messages[0].content
    assert "Cross-law sorularda" in messages[0].content
    assert "Önce kısa sonucu ver" in messages[0].content
    assert "Soruda açık madde numarası geçiyorsa" in messages[1].content
    assert "[Kaynak: TMK m.706]" in messages[1].content
    assert "TMK m.706 ile TBK m.237" in messages[1].content


def test_generate_rag_draft_uses_refusal_prompt_without_context() -> None:
    client = CapturingLLMClient()

    asyncio.run(client.generate_rag_draft(query="Kıdem tazminatı nasıl hesaplanır?", context=""))

    messages, _temperature = client.calls[-1]
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
