from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from rag.token_manager import estimate_tokens


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _release_controls_strict() -> bool:
    return _to_bool(os.getenv("RELEASE_CONTROLS_STRICT"), False)


def _token_accounting_fallback_allowed() -> bool:
    default = not _release_controls_strict()
    return _to_bool(os.getenv("TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK"), default)


def token_accounting_fallback_allowed() -> bool:
    return _token_accounting_fallback_allowed()


def _configured_tokenizer_path() -> str | None:
    explicit = os.getenv("TOKEN_ACCOUNTING_TOKENIZER_PATH") or os.getenv(
        "TOKEN_ACCOUNTING_TOKENIZER_ID"
    )
    if explicit:
        return explicit

    hub_root = Path.home() / ".cache" / "huggingface" / "hub"
    preferred_patterns = (
        "models--Qwen--Qwen3-32B",
        "models--Qwen--Qwen2.5-32B-Instruct",
        "models--Qwen--Qwen2.5-14B",
        "models--Qwen--Qwen2.5-7B-Instruct",
    )
    for pattern in preferred_patterns:
        snapshots_dir = hub_root / pattern / "snapshots"
        if not snapshots_dir.exists():
            continue
        snapshots = sorted(p for p in snapshots_dir.iterdir() if p.is_dir())
        if snapshots:
            return str(snapshots[-1])
    return None


@dataclass(slots=True)
class TokenAccountingResult:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    source: str
    tokenizer_ref: str | None = None

    def as_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class TokenAccountingError(RuntimeError):
    pass


class TokenAccountingEngine:
    def __init__(self, tokenizer_path: str) -> None:
        self.tokenizer_path = tokenizer_path
        try:
            from transformers import AutoTokenizer
        except Exception as exc:  # pragma: no cover - runtime dependency
            raise TokenAccountingError("transformers/tokenizers yüklenemedi") from exc

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_path,
                local_files_only=True,
                trust_remote_code=True,
            )
        except Exception as exc:  # pragma: no cover - runtime dependency
            raise TokenAccountingError(
                f"Tokenizer yüklenemedi: {tokenizer_path}"
            ) from exc

    def count_messages(self, messages: Sequence[object]) -> int:
        payload: list[dict[str, str]] = []
        for item in messages:
            role = getattr(item, "role", None)
            content = getattr(item, "content", None)
            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content")
            if not isinstance(role, str) or not isinstance(content, str):
                raise TokenAccountingError("Mesaj biçimi tokenizer accounting için geçersiz")
            payload.append({"role": role, "content": content})

        try:
            token_ids = self._tokenizer.apply_chat_template(
                payload,
                tokenize=True,
                add_generation_prompt=True,
            )
        except Exception as exc:
            raise TokenAccountingError("Chat template tokenize edilemedi") from exc

        if not isinstance(token_ids, list):
            raise TokenAccountingError("Tokenizer beklenmeyen chat template sonucu üretti")
        return len(token_ids)

    def count_text(self, text: str) -> int:
        if not isinstance(text, str):
            raise TokenAccountingError("Yanıt metni tokenizer accounting için geçersiz")
        try:
            token_ids = self._tokenizer.encode(text, add_special_tokens=False)
        except Exception as exc:
            raise TokenAccountingError("Metin tokenize edilemedi") from exc
        if not isinstance(token_ids, list):
            raise TokenAccountingError("Tokenizer beklenmeyen encode sonucu üretti")
        return len(token_ids)


@lru_cache(maxsize=1)
def _get_engine() -> TokenAccountingEngine | None:
    tokenizer_path = _configured_tokenizer_path()
    if not tokenizer_path:
        return None
    return TokenAccountingEngine(tokenizer_path)


def reset_token_accounting_engine_cache() -> None:
    _get_engine.cache_clear()


def resolve_token_usage(
    *,
    messages: Sequence[object],
    answer_text: str,
    upstream_usage: dict[str, int] | None,
) -> TokenAccountingResult:
    if upstream_usage and all(
        isinstance(upstream_usage.get(key), int) and upstream_usage[key] >= 0
        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
    ):
        return TokenAccountingResult(
            prompt_tokens=upstream_usage["prompt_tokens"],
            completion_tokens=upstream_usage["completion_tokens"],
            total_tokens=upstream_usage["total_tokens"],
            source="upstream",
        )

    engine = _get_engine()
    if engine is not None:
        prompt_tokens = engine.count_messages(messages)
        completion_tokens = engine.count_text(answer_text)
        return TokenAccountingResult(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            source="tokenizer",
            tokenizer_ref=engine.tokenizer_path,
        )

    if not _token_accounting_fallback_allowed():
        raise TokenAccountingError("Tokenizer-backed accounting gerekli ama tokenizer bulunamadı")

    prompt_tokens = sum(estimate_tokens(getattr(message, "content", "")) for message in messages)
    completion_tokens = estimate_tokens(answer_text)
    return TokenAccountingResult(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        source="estimated",
    )
