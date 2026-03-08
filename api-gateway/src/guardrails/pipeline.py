from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import Settings
from guardrails.actions import PresidioMasker, validate_citations


@dataclass(slots=True)
class GuardrailsResult:
    answer: str
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)


class GuardrailsPipeline:
    """RAG post-processing doğrulama katmanı.

    Faz 1'de manuel hallucination/citation post-processing yerine bu sınıf kullanılır.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.masker = PresidioMasker(settings)
        self._rails: Any | None = None
        self._rails_lock = asyncio.Lock()

    async def _ensure_rails(self) -> Any | None:
        if not self.settings.guardrails_enabled:
            return None
        if self._rails is not None:
            return self._rails

        async with self._rails_lock:
            if self._rails is not None:
                return self._rails

            try:
                from nemoguardrails import LLMRails, RailsConfig
            except Exception:  # pragma: no cover - depends on optional dependency
                self._rails = None
                return None

            config_dir = self._resolve_config_dir()
            config = RailsConfig.from_path(str(config_dir))
            self._rails = LLMRails(config)
            self._register_custom_actions(self._rails)
            return self._rails

    def _resolve_config_dir(self) -> Path:
        configured = self.settings.guardrails_config_dir
        if configured.is_absolute():
            return configured
        # .../api-gateway/src/guardrails/pipeline.py -> parents[2] == api-gateway/
        return (Path(__file__).resolve().parents[2] / configured).resolve()

    def _register_custom_actions(self, rails: Any) -> None:
        register = getattr(rails, "register_action", None)
        if register is None:
            return

        async def presidio_mask_input(text: str) -> str:
            return self.masker.mask(text)

        async def presidio_mask_output(text: str) -> str:
            return self.masker.mask(text)

        async def verify_output_citations(answer: str, retrieved_chunks: list[dict[str, Any]]) -> bool:
            ok, _invalid = validate_citations(answer, retrieved_chunks)
            return ok

        register(action=presidio_mask_input, name="presidio_mask_input")
        register(action=presidio_mask_output, name="presidio_mask_output")
        register(action=verify_output_citations, name="verify_output_citations")

    async def _generate_with_rails(self, prompt: str, context: dict[str, Any]) -> str:
        rails = await self._ensure_rails()
        if rails is None:
            return context["draft_answer"]

        messages = [{"role": "user", "content": prompt}]

        # NeMo Guardrails sürümleri arasında parametre farkları olabildiği için
        # kontrollü fallback zinciri kullanıyoruz.
        calls = [
            ("generate_async", {"messages": messages, "options": {"context": context}}),
            ("generate_async", {"messages": messages, "context": context}),
            ("generate", {"messages": messages, "options": {"context": context}}),
            ("generate", {"messages": messages}),
        ]

        last_error: Exception | None = None
        for fn_name, kwargs in calls:
            fn = getattr(rails, fn_name, None)
            if fn is None:
                continue
            try:
                result = fn(**kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return self._extract_text(result)
            except TypeError as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error

        return context["draft_answer"]

    @staticmethod
    def _extract_text(result: Any) -> str:
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            if "content" in result:
                return str(result["content"])
            if "response" in result:
                return str(result["response"])
        # bazen Guardrails response objesi dönebilir
        content = getattr(result, "content", None)
        if content:
            return str(content)
        return str(result)

    async def run(
        self,
        *,
        user_query: str,
        draft_answer: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> GuardrailsResult:
        """Taslak yanıtı Guardrails politikalarıyla doğrula ve maskeler."""

        masked_query = self.masker.mask(user_query)

        context = {
            "user_query": masked_query,
            "draft_answer": draft_answer,
            "retrieved_chunks": retrieved_chunks,
            "hallucination_samples": self.settings.hallucination_samples,
        }

        guard_prompt = (
            "Kullanıcı sorusu, elde edilen kaynak parçaları ve taslak yanıt verildi. "
            "Sadece kaynaklarla doğrulanabilen iddiaları koru, kaynakta yoksa çıkar veya "
            "reddetme cümlesi ile belirt. Cevaptaki kaynak formatı [Kaynak: ...] olmalı. "
            "Gerekirse kısa bir refusal ver.\n\n"
            f"SORU:\n{masked_query}\n\n"
            f"TASLAK YANIT:\n{draft_answer}\n\n"
            f"KAYNAKLAR:\n{self._format_chunks(retrieved_chunks)}"
        )

        guarded = await self._generate_with_rails(guard_prompt, context)
        masked_output = self.masker.mask(guarded)

        citations_ok, invalid_citations = validate_citations(masked_output, retrieved_chunks)
        reasons: list[str] = []
        blocked = False

        if not citations_ok:
            reasons.append("invalid_or_missing_citation")
            if self.settings.guardrails_strict_mode:
                blocked = True

        if blocked:
            return GuardrailsResult(
                answer=(
                    "Bu konuda elimdeki kaynaklarda yeterli doğrulanmış bilgi bulamadım. "
                    "Lütfen daha spesifik bir mevzuat sorusu sorun."
                ),
                blocked=True,
                reasons=reasons + [f"invalid={invalid_citations}"],
            )

        return GuardrailsResult(answer=masked_output, blocked=False, reasons=reasons)

    @staticmethod
    def _format_chunks(retrieved_chunks: list[dict[str, Any]]) -> str:
        if not retrieved_chunks:
            return "(boş)"

        rows: list[str] = []
        for i, chunk in enumerate(retrieved_chunks, start=1):
            citation = chunk.get("citation") or chunk.get("source") or f"chunk-{i}"
            text = str(chunk.get("text", "")).strip()
            rows.append(f"[{i}] {citation}: {text}")
        return "\n".join(rows)
