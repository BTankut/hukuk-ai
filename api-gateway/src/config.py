from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _to_bool(value: str | bool | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | int | None, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except ValueError:
        return default


def _to_float(value: str | float | int | None, default: float | None) -> float | None:
    if value is None:
        return default
    if isinstance(value, (float, int)):
        return float(value)
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(slots=True)
class Settings:
    """API Gateway runtime ayarları (lightweight env loader)."""

    app_name: str = "hukuk-ai-api-gateway"
    environment: str = "dev"
    log_level: str = "INFO"

    # DGX OpenAI-compatible endpoint
    dgx_base_url: str = "http://192.168.12.243:30000/v1"
    dgx_model: str = "Qwen/Qwen3.5-35B-A3B-FP8"
    dgx_api_key: str = "not-needed"
    dgx_temperature_default: float = 0.1
    dgx_max_tokens_default: int = 512
    dgx_top_p: float | None = None
    dgx_top_k: int | None = None
    dgx_seed: int | None = None
    dgx_request_timeout_seconds: float = 180.0
    dgx_retry_count: int = 0

    # Guardrails
    guardrails_enabled: bool = True
    # Düşük riskli varsayılan: facts/output block KAPALI.
    # Sadece açık opt-in'de strict citation/facts denetimi uygulanır.
    guardrails_strict_mode: bool = False
    guardrails_config_dir: Path = Path("guardrails")
    guardrails_latency_limit_ms: int = 8000
    guardrails_input_moderation_enabled: bool = True

    # Presidio / KVKK
    presidio_enabled: bool = True
    presidio_mask_char: str = "*"
    presidio_language: str = "tr"
    presidio_entities: str = "PERSON,PHONE_NUMBER,EMAIL_ADDRESS,LOCATION,TR_ID_NUMBER"

    # Hallucination self-check
    hallucination_samples: int = 3

    def __init__(self, **overrides):
        values = {
            "app_name": os.getenv("APP_NAME", "hukuk-ai-api-gateway"),
            "environment": os.getenv("ENVIRONMENT", "dev"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "dgx_base_url": os.getenv("DGX_BASE_URL", "http://192.168.12.243:30000/v1"),
            "dgx_model": os.getenv("DGX_MODEL", "Qwen/Qwen3.5-35B-A3B-FP8"),
            "dgx_api_key": os.getenv("DGX_API_KEY", "not-needed"),
            "dgx_temperature_default": _to_float(os.getenv("DGX_TEMPERATURE_DEFAULT"), 0.1),
            "dgx_max_tokens_default": _to_int(os.getenv("DGX_MAX_TOKENS_DEFAULT"), 512),
            "dgx_top_p": _to_float(os.getenv("DGX_TOP_P"), None),
            "dgx_top_k": _to_int(os.getenv("DGX_TOP_K"), -1),
            "dgx_seed": _to_int(os.getenv("DGX_SEED"), -1),
            "dgx_request_timeout_seconds": _to_float(os.getenv("DGX_REQUEST_TIMEOUT_SECONDS"), 180.0),
            "dgx_retry_count": _to_int(os.getenv("DGX_RETRY_COUNT"), 0),
            "guardrails_enabled": _to_bool(os.getenv("GUARDRAILS_ENABLED"), True),
            "guardrails_strict_mode": _to_bool(os.getenv("GUARDRAILS_STRICT_MODE"), False),
            "guardrails_config_dir": Path(os.getenv("GUARDRAILS_CONFIG_DIR", "guardrails")),
            "guardrails_latency_limit_ms": _to_int(os.getenv("GUARDRAILS_LATENCY_LIMIT_MS"), 8000),
            "guardrails_input_moderation_enabled": _to_bool(
                os.getenv("GUARDRAILS_INPUT_MODERATION_ENABLED"),
                True,
            ),
            "presidio_enabled": _to_bool(os.getenv("PRESIDIO_ENABLED"), True),
            "presidio_mask_char": os.getenv("PRESIDIO_MASK_CHAR", "*"),
            "presidio_language": os.getenv("PRESIDIO_LANGUAGE", "tr"),
            "presidio_entities": os.getenv(
                "PRESIDIO_ENTITIES",
                "PERSON,PHONE_NUMBER,EMAIL_ADDRESS,LOCATION,TR_ID_NUMBER",
            ),
            "hallucination_samples": _to_int(os.getenv("HALLUCINATION_SAMPLES"), 3),
        }

        values.update(overrides)
        if values["dgx_top_k"] is not None and int(values["dgx_top_k"]) < 0:
            values["dgx_top_k"] = None
        if values["dgx_seed"] is not None and int(values["dgx_seed"]) < 0:
            values["dgx_seed"] = None
        for key, value in values.items():
            setattr(self, key, value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
