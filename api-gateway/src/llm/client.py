from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from config import Settings


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


class LLMClient:
    """DGX üzerinde çalışan OpenAI-compatible vLLM client wrapper'ı."""

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
        return response.choices[0].message.content or ""

    async def generate_rag_draft(self, query: str, context: str) -> str:
        if not context or not context.strip():
            # Bağlam yoksa güvenli refusal üret
            messages = [
                ChatMessage(
                    role="system",
                    content=(
                        "Sen bir Türk hukuku asistanısın. Yalnızca sana verilen kaynak "
                        "metinlerine dayanarak yanıt ver. Kaynak verilmemişse bunu açıkça "
                        "belirt ve bilgi üretme."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        "Aşağıdaki soru için ilgili mevzuat kaynağı bulunamadı. "
                        "Kaynak olmadan yanıt verme; kullanıcıya mevzuat bulunmadığını "
                        "kibarca açıkla ve uzman bir avukata danışmasını öner.\n\n"
                        f"SORU:\n{query}"
                    ),
                ),
            ]
        else:
            messages = [
                ChatMessage(
                    role="system",
                    content=(
                        "Sen bir Türk hukuku asistanısın. YALNIZCA verilen KAYNAKLAR "
                        "bölümündeki metni kullan. Kaynak metinlerde geçen '[Kaynak: X]' "
                        "etiketlerini yanıtında alıntı olarak kullan. "
                        "Kaynak metinlerde bulunmayan bilgi üretme. "
                        "Özellikle Türk Medeni Kanunu (TMK), İş Kanunu (Kıdem tazminatı vb.) veya "
                        "diğer kapsam dışı konularda (ör. şirketler hukuku) soru gelirse ve kaynaklarda "
                        "net olarak yoksa KESİNLİKLE kendi bilgini kullanarak yanıt verme. "
                        "Açıkça 'Bu konu şu anki TBK kapsamım dışındadır veya kaynaklarda bulunmamaktadır.' diyerek reddet."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        "Aşağıdaki kaynak metinleri kullanarak soruyu yanıtla. "
                        "Yanıtta her iddia için ilgili kaynak etiketini '[Kaynak: X]' "
                        "biçiminde ekle.\n\n"
                        f"KAYNAKLAR:\n{context}\n\n"
                        f"SORU:\n{query}"
                    ),
                ),
            ]
        return await self.chat(messages=messages, temperature=0.1)
