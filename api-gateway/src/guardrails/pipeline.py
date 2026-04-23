from __future__ import annotations

import asyncio
import ast
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import Settings
from guardrails.actions import PresidioMasker, validate_citations

logger = logging.getLogger(__name__)


def _tr_lower(text: str) -> str:
    tr_map = str.maketrans("İIĞÖÜŞÇ", "iiğöüşç")
    return text.translate(tr_map).lower()


@dataclass(slots=True)
class GuardrailsResult:
    answer: str
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)


class GuardrailsPipeline:
    """RAG post-processing guardrails katmanı (Phase 2 safe-scope)."""

    _SENSITIVE_DATA_PATTERNS = (
        "tc kimlik",
        "t.c. kimlik",
        "telefon numarasını ver",
        "adresini ver",
        "iban",
        "kişisel verisini ver",
        "mail adresini ver",
        "e-posta adresini ver",
    )
    _UNSAFE_PATTERNS = (
        "hackle",
        "şifre kır",
        "zarar ver",
        "bomba",
        "silah yap",
        "uyuşturucu üret",
        "dolandır",
        "saldırı planla",
    )
    _OFF_TOPIC_PATTERNS = (
        "hava durumu",
        "yemek tarifi",
        "burç",
        "maç sonucu",
        "film öner",
        "şarkı öner",
        "fıkra",
    )
    _LEGAL_HINT_PATTERNS = (
        "hukuk",
        "kanun",
        "madde",
        "tbk",
        "tmk",
        "tck",
        "dava",
        "mahkeme",
        "sözleş",
        "tazminat",
        "icra",
        "ceza",
        "borç",
        "mevzuat",
    )
    _REFUSAL_HINTS = (
        "yardımcı olamam",
        "yanıt veremem",
        "bu konuda bilgi veremem",
        "kapsam dışı",
        "güvenlik nedeniyle",
        "i'm sorry, i can't respond to that",
        "i cannot respond to that",
        "i can't assist with that",
        "i cannot assist with that",
        "unable to comply with that request",
    )
    _STRINGIFIED_RESPONSE_RE = re.compile(r"response=(\[[\s\S]*?\])\s+llm_output=")
    _STRINGIFIED_RESPONSE_MARKERS = (
        " llm_output=",
        " output_data=",
        " log=",
        " state=",
    )

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
            except Exception:  # pragma: no cover - optional dependency
                self._rails = None
                return None

            config_dir = self._resolve_config_dir()
            config = RailsConfig.from_path(str(config_dir))
            self._seed_guardrails_env_defaults()
            self._apply_model_runtime_defaults(config)

            self._rails = LLMRails(config)
            self._register_custom_actions(self._rails)
            return self._rails

    def _resolve_config_dir(self) -> Path:
        configured = self.settings.guardrails_config_dir
        if configured.is_absolute():
            return configured
        return (Path(__file__).resolve().parents[2] / configured).resolve()

    def _seed_guardrails_env_defaults(self) -> None:
        os.environ.setdefault("DGX_BASE_URL", self.settings.dgx_base_url)
        os.environ.setdefault("DGX_MODEL", self.settings.dgx_model)
        os.environ.setdefault("DGX_API_KEY", self.settings.dgx_api_key)
        os.environ.setdefault("HALLUCINATION_SAMPLES", str(self.settings.hallucination_samples))

    @staticmethod
    def _is_unresolved_placeholder(value: Any) -> bool:
        return isinstance(value, str) and value.strip().startswith("${") and value.strip().endswith("}")

    def _apply_model_runtime_defaults(self, config: Any) -> None:
        models = getattr(config, "models", None) or []
        for model in models:
            model_name = getattr(model, "model", None)
            if self._is_unresolved_placeholder(model_name) or not model_name:
                setattr(model, "model", self.settings.dgx_model)

            params = dict(getattr(model, "parameters", None) or {})
            base_url = params.get("base_url")
            if self._is_unresolved_placeholder(base_url) or not base_url:
                params["base_url"] = self.settings.dgx_base_url

            api_key = params.get("api_key")
            if self._is_unresolved_placeholder(api_key) or api_key is None or api_key == "":
                params["api_key"] = self.settings.dgx_api_key

            setattr(model, "parameters", params)

    def _register_custom_actions(self, rails: Any) -> None:
        register = getattr(rails, "register_action", None)
        if register is None:
            return

        async def presidio_mask_input(text: str) -> str:
            return self.masker.mask(text)

        async def presidio_mask_output(text: str) -> str:
            return self.masker.mask(text, allow_ner=False)

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

    async def _generate_with_rails_guarded(self, prompt: str, context: dict[str, Any]) -> str:
        limit_ms = self.settings.guardrails_latency_limit_ms

        try:
            if limit_ms <= 0:
                return await self._generate_with_rails(prompt, context)

            return await asyncio.wait_for(
                self._generate_with_rails(prompt, context),
                timeout=limit_ms / 1000.0,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Guardrails latency limit aşıldı (%dms), draft_answer fallback uygulandı",
                limit_ms,
            )
            return context["draft_answer"]
        except Exception as exc:  # pragma: no cover - canlı SDK/LLM uyumsuzluklarına karşı fail-open
            logger.warning(
                "Guardrails çalışması hata verdi (%s), draft_answer fallback uygulandı",
                type(exc).__name__,
            )
            return context["draft_answer"]

    @staticmethod
    def _safe_literal_list(payload_text: str) -> list[dict[str, Any]] | None:
        try:
            payload = ast.literal_eval(payload_text)
        except Exception:
            return None
        return payload if isinstance(payload, list) else None

    @classmethod
    def _extract_stringified_response_payload(cls, result: str) -> list[dict[str, Any]] | None:
        if not result.startswith("response="):
            return None

        match = cls._STRINGIFIED_RESPONSE_RE.search(result)
        if match:
            return cls._safe_literal_list(match.group(1))

        start = len("response=")
        end_positions = [
            result.find(marker, start)
            for marker in cls._STRINGIFIED_RESPONSE_MARKERS
            if result.find(marker, start) != -1
        ]
        if not end_positions:
            return None

        return cls._safe_literal_list(result[start : min(end_positions)].strip())

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
        if isinstance(result, list):
            first = result[0] if result else None
            if first is not None:
                return cls._extract_text(first)
            return ""
        if isinstance(result, dict):
            if "content" in result:
                return cls._extract_text(result["content"])
            if "response" in result:
                return cls._extract_text(result["response"])
        response = getattr(result, "response", None)
        if response is not None:
            return cls._extract_text(response)
        content = getattr(result, "content", None)
        if content:
            return cls._extract_text(content)
        return str(result)

    def _deterministic_input_moderation_reason(self, query: str) -> str | None:
        q = _tr_lower(query)

        if any(pattern in q for pattern in self._SENSITIVE_DATA_PATTERNS):
            return "input_sensitive_data_request"

        if any(pattern in q for pattern in self._UNSAFE_PATTERNS):
            return "input_unsafe_request"

        has_legal_signal = any(pattern in q for pattern in self._LEGAL_HINT_PATTERNS)
        if (not has_legal_signal) and any(pattern in q for pattern in self._OFF_TOPIC_PATTERNS):
            return "input_out_of_scope"

        return None

    def _build_input_refusal(self, reason: str) -> str:
        if reason == "input_sensitive_data_request":
            return (
                "Kişisel verilerin kötüye kullanımına veya ifşasına yönelik taleplere yardımcı olamam. "
                "Lütfen hukuka uygun bir mevzuat sorusu sorun."
            )
        if reason == "input_unsafe_request":
            return (
                "Zararlı veya yasa dışı eylemlere yönelik taleplere yardımcı olamam. "
                "İsterseniz hukuka uygun bir konuda bilgi verebilirim."
            )
        return (
            "Bu istek hukuk asistanı kapsamı dışında görünüyor. "
            "Lütfen Türk hukuku/mevzuatıyla ilgili bir soru sorun."
        )

    def _looks_like_refusal(self, text: str) -> bool:
        q = _tr_lower(text or "")
        return any(hint in q for hint in self._REFUSAL_HINTS)

    async def run(
        self,
        *,
        user_query: str,
        draft_answer: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> GuardrailsResult:
        """Taslak yanıtı düşük-risk guardrails politikalarıyla işler."""

        masked_query = self.masker.mask(user_query)
        reasons: list[str] = []

        if self.settings.guardrails_input_moderation_enabled:
            # Input moderation, kullanıcı niyeti üzerinde çalışmalıdır.
            # Presidio masking bazı anahtar ifadeleri anonimleştirebildiği için
            # önce ham sorguyu değerlendiriyoruz.
            moderation_reason = self._deterministic_input_moderation_reason(user_query)
            if moderation_reason is None:
                moderation_reason = self._deterministic_input_moderation_reason(masked_query)
            if moderation_reason is not None:
                return GuardrailsResult(
                    answer=self._build_input_refusal(moderation_reason),
                    blocked=True,
                    reasons=[moderation_reason],
                )

        context = {
            "user_query": masked_query,
            "draft_answer": draft_answer,
            "retrieved_chunks": retrieved_chunks,
            "hallucination_samples": self.settings.hallucination_samples,
        }

        guard_prompt = (
            "Aşağıda kullanıcı sorusu, taslak yanıt ve kaynak özetleri var. "
            "Eğer girdi güvenliyse TASLAK YANIT'ı mümkün olduğunca aynen döndür. "
            "Sadece güvenlik/politika nedeniyle gerekli minimum düzenlemeyi yap.\n\n"
            f"SORU:\n{masked_query}\n\n"
            f"TASLAK YANIT:\n{draft_answer}\n\n"
            f"KAYNAKLAR:\n{self._format_chunks(retrieved_chunks)}"
        )

        guarded = await self._generate_with_rails_guarded(guard_prompt, context)
        if not guarded.strip():
            guarded = draft_answer

        if self._looks_like_refusal(guarded) and not self._looks_like_refusal(draft_answer):
            # Geçerli hukuki sorularda self_check_input false-positive riskine karşı fail-open.
            guarded = draft_answer
            reasons.append("guardrails_fail_open_refusal_fallback")

        masked_output = self.masker.mask(guarded, allow_ner=False)

        blocked = False
        if self.settings.guardrails_strict_mode:
            citations_ok, invalid_citations = validate_citations(masked_output, retrieved_chunks)
            if not citations_ok:
                blocked = True
                reasons.append("invalid_or_missing_citation")
                return GuardrailsResult(
                    answer=(
                        "Bu konuda elimdeki kaynaklarda yeterli doğrulanmış bilgi bulamadım. "
                        "Lütfen daha spesifik bir mevzuat sorusu sorun."
                    ),
                    blocked=True,
                    reasons=reasons + [f"invalid={invalid_citations}"],
                )

        return GuardrailsResult(answer=masked_output, blocked=blocked, reasons=reasons)

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
