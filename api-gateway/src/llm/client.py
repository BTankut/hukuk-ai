from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any, Sequence

from config import Settings


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(slots=True)
class LLMResult:
    text: str
    usage: TokenUsage | None = None
    trace: dict[str, Any] | None = None


class LLMClient:
    """DGX üzerinde çalışan OpenAI-compatible vLLM client wrapper'ı."""

    _STRINGIFIED_RESPONSE_RE = re.compile(r"response=(\[[\s\S]*?\])\s+llm_output=")
    _STRINGIFIED_RESPONSE_MARKERS = (
        " llm_output=",
        " output_data=",
        " log=",
        " state=",
    )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            from openai import AsyncOpenAI
        except Exception as exc:  # pragma: no cover - dependency missing at runtime
            raise RuntimeError(
                "openai paketi bulunamadı. `pip install -e .` sonrası tekrar deneyin."
            ) from exc

        self._client = AsyncOpenAI(
            base_url=self.settings.dgx_base_url,
            api_key=self.settings.dgx_api_key,
            timeout=self.settings.dgx_request_timeout_seconds,
            max_retries=self.settings.dgx_retry_count,
        )
        return self._client

    def _resolve_max_tokens(self, max_tokens: int | None) -> int:
        return max_tokens if isinstance(max_tokens, int) and max_tokens > 0 else self.settings.dgx_max_tokens_default

    def _build_generation_contract(
        self,
        *,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        return {
            "temperature": temperature,
            "top_p": self.settings.dgx_top_p,
            "top_k": self.settings.dgx_top_k,
            "max_tokens": max_tokens,
            "stop": None,
            "seed": self.settings.dgx_seed,
            "retry_count": self.settings.dgx_retry_count,
            "timeout_seconds": self.settings.dgx_request_timeout_seconds,
            "streaming": False,
            "enable_thinking": False,
        }

    def _build_request_payload(
        self,
        *,
        messages: Sequence[ChatMessage],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.settings.dgx_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
        }
        if self.settings.dgx_top_p is not None:
            payload["top_p"] = self.settings.dgx_top_p
        if self.settings.dgx_seed is not None:
            payload["seed"] = self.settings.dgx_seed
        if self.settings.dgx_top_k is not None:
            payload["extra_body"]["top_k"] = self.settings.dgx_top_k
        return payload

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int | None = None,
    ) -> LLMResult:
        client = self._get_client()
        resolved_max_tokens = self._resolve_max_tokens(max_tokens)
        generation_contract = self._build_generation_contract(
            temperature=temperature,
            max_tokens=resolved_max_tokens,
        )
        request_payload = self._build_request_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=resolved_max_tokens,
        )
        response = await client.chat.completions.create(**request_payload)
        return LLMResult(
            text=self._extract_text(response.choices[0].message.content or ""),
            usage=self._extract_usage(response),
            trace={
                "model_request_payload": request_payload,
                "generation_contract": generation_contract,
                "raw_answer_object": self._extract_raw_answer_object(response),
            },
        )

    @classmethod
    def _extract_text(cls, result: Any) -> str:
        if isinstance(result, str):
            payload = cls._extract_stringified_response_payload(result)
            if isinstance(payload, list):
                first = payload[0] if payload else None
                if isinstance(first, dict):
                    content = first.get("content")
                    if isinstance(content, str) and content.strip():
                        return content
            return result
        content = getattr(result, "content", None)
        if isinstance(content, str) and content.strip():
            return cls._extract_text(content)
        return str(result)

    @classmethod
    def _extract_stringified_response_payload(cls, result: str) -> list[dict[str, Any]] | None:
        match = cls._STRINGIFIED_RESPONSE_RE.search(result)
        if match:
            return cls._safe_literal_list(match.group(1))

        if not result.startswith("response="):
            return None

        start = len("response=")
        end_positions = [
            result.find(marker, start)
            for marker in cls._STRINGIFIED_RESPONSE_MARKERS
            if result.find(marker, start) != -1
        ]
        if not end_positions:
            return None

        return cls._safe_literal_list(result[start : min(end_positions)].strip())

    @staticmethod
    def _safe_literal_list(payload_text: str) -> list[dict[str, Any]] | None:
        try:
            payload = ast.literal_eval(payload_text)
        except Exception:
            return None
        return payload if isinstance(payload, list) else None

    @staticmethod
    def _extract_usage(response: Any) -> TokenUsage | None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None

        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")

        if not all(isinstance(value, int) and value >= 0 for value in (prompt_tokens, completion_tokens, total_tokens)):
            return None

        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    @classmethod
    def _extract_raw_answer_object(cls, response: Any) -> dict[str, Any]:
        choices = getattr(response, "choices", None) or []
        if not choices:
            return {}

        choice = choices[0]
        message = getattr(choice, "message", None)
        raw_content = getattr(message, "content", "") if message is not None else ""
        extracted_text = cls._extract_text(raw_content if raw_content is not None else "")
        return {
            "role": getattr(message, "role", "assistant") if message is not None else "assistant",
            "content": raw_content if isinstance(raw_content, str) else str(raw_content),
            "extracted_text": extracted_text,
            "finish_reason": getattr(choice, "finish_reason", None),
        }

    @staticmethod
    def _build_no_context_messages(query: str) -> list[ChatMessage]:
        return [
            ChatMessage(
                role="system",
                content=(
                    "Sen bir Türk hukuku asistanısın. Sana doğrulanmış kaynak verilmemişse "
                    "bilgi üretme. Kısa kal, tahmin yürütme ve kaynak bulunmadığını açıkça belirt."
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    "Aşağıdaki soru için ilgili mevzuat kaynağı bulunamadı. "
                    "Kaynak olmadan yanıt verme; kullanıcıya mevcut kaynaklarda açık dayanak "
                    "bulunmadığını kibarca açıkla ve uzman bir avukata danışmasını öner.\n\n"
                    f"SORU:\n{query}"
                ),
            ),
        ]

    @staticmethod
    def _build_rag_messages(query: str, context: str) -> list[ChatMessage]:
        system_prompt = (
            "Sen bir Türk hukuku asistanısın. YALNIZCA verilen KAYNAKLAR bölümünü kullan. "
            "Kaynakta bulunmayan bilgi, sonuç veya madde üretme.\n\n"
            "Yanıtı üretmeden önce zihinsel olarak şu sırayı izle, fakat bu adımları kullanıcıya yazma:\n"
            "1. Sorunun gerçekten hangi kanun ailesine dayandığını belirle (TBK, TMK, TCK, HMK, TTK, İİK).\n"
            "2. Soru belirli bir maddeye atıf yapıyorsa ve o madde kaynaklarda varsa önce onu değerlendir.\n"
            "3. Her iddiayı yalnız gerçekten dayandığın kaynak maddelerle eşleştir.\n\n"
            "Zorunlu kurallar:\n"
            "- Her hukuki iddiada en yakın ilgili '[Kaynak: X]' etiketini kullan.\n"
            "- Kanun prefixlerini asla karıştırma; TBK/TMK/TCK/HMK/TTK/İİK aynen korunmalı.\n"
            "- Komşu veya benzer maddeyi yalnız yakın olduğu için cite etme; sadece gerçekten dayandığın maddeyi yaz.\n"
            "- Cross-law sorularda cevap gerçekten iki kanuna dayanıyorsa her iki kanundan da açık kaynak göster; dayanmıyorsa gereksiz ikinci kanun ekleme.\n"
            "- Önce kısa sonucu ver, sonra en fazla üç kısa dayanak maddesiyle devam et.\n"
            "- Kaynak yetersizse açıkça bunu söyle ve tahmin yürütme."
        )
        user_prompt = (
            "Aşağıdaki kaynak metinlerini kullanarak soruyu yanıtla. "
            "Önce tek cümlelik sonucu ver. Ardından yalnız gerçekten dayandığın maddeleri "
            "'[Kaynak: X]' biçiminde göster. Soruda açık madde numarası geçiyorsa ve kaynaklarda "
            "varsa o maddeyi atlama.\n\n"
            f"KAYNAKLAR:\n{context}\n\n"
            f"SORU:\n{query}"
        )
        return [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

    async def generate_rag_draft(
        self,
        query: str,
        context: str,
        *,
        max_tokens: int | None = None,
    ) -> LLMResult | str:
        if not context or not context.strip():
            messages = self._build_no_context_messages(query)
        else:
            messages = self._build_rag_messages(query, context)
        result = await self.chat(messages=messages, temperature=0.1, max_tokens=max_tokens)
        if isinstance(result, str):
            return result
        trace = dict(result.trace or {})
        trace["assembly_payload"] = {
            "query": query,
            "context": context,
        }
        result.trace = trace
        return result
