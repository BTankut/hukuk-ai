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


class LLMClient:
    """DGX üzerinde çalışan OpenAI-compatible vLLM client wrapper'ı."""

    _STRINGIFIED_RESPONSE_RE = re.compile(r"response=(\[[\s\S]*?\])\s+llm_output=")

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
        )
        return self._client

    async def chat(self, messages: Sequence[ChatMessage], temperature: float = 0.1) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.settings.dgx_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        return self._extract_text(response.choices[0].message.content or "")

    @classmethod
    def _extract_text(cls, result: Any) -> str:
        if isinstance(result, str):
            match = cls._STRINGIFIED_RESPONSE_RE.search(result)
            if match:
                try:
                    payload = ast.literal_eval(match.group(1))
                except Exception:
                    payload = None
                if isinstance(payload, list):
                    first = payload[0] if payload else None
                    if isinstance(first, dict):
                        content = first.get("content")
                        if isinstance(content, str) and content.strip():
                            return content
            return result
        content = getattr(result, "content", None)
        if isinstance(content, str) and content.strip():
            return content
        return str(result)

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

    async def generate_rag_draft(self, query: str, context: str) -> str:
        if not context or not context.strip():
            messages = self._build_no_context_messages(query)
        else:
            messages = self._build_rag_messages(query, context)
        return await self.chat(messages=messages, temperature=0.1)
