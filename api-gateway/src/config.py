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
    dgx_enable_thinking: bool = False

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

    # Judicial runtime retrieval
    judicial_runtime_enabled: bool = False
    judicial_processed_dir: Path = Path("/Users/btmacstudio/Projects/yargi/_work/final_package/processed")
    judicial_exact_lookup_path: Path = Path(
        "/Users/btmacstudio/Projects/yargi/_work/final_package/processed/judicial_exact_lookup.sqlite"
    )
    judicial_lexical_index_path: Path = Path(
        "/Users/btmacstudio/Projects/yargi/_work/final_package/processed/judicial_lexical_index.sqlite"
    )
    judicial_vector_collection: str = "judicial_decisions_v1_shadow"
    judicial_vector_enabled: bool = False
    legal_advisor_llm_enabled: bool = True
    legal_rag_max_mevzuat_evidence: int = 6
    legal_rag_judicial_top_k: int = 20
    legal_rag_max_judicial_decisions: int = 5
    legal_rag_max_chunks_per_decision: int = 2
    legal_rag_max_total_evidence_chars: int = 8000
    legal_rag_retrieval_timeout_ms: int = 8000
    legal_rag_llm_timeout_ms: int = 15000
    legal_rag_verification_timeout_ms: int = 5000
    legal_rag_max_query_chars: int = 4000

    def __init__(self, **overrides):
        default_judicial_processed_dir = Path(
            os.getenv(
                "JUDICIAL_PROCESSED_DIR",
                "/Users/btmacstudio/Projects/yargi/_work/final_package/processed",
            )
        )
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
            "dgx_enable_thinking": _to_bool(os.getenv("DGX_ENABLE_THINKING"), False),
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
            "judicial_runtime_enabled": _to_bool(os.getenv("JUDICIAL_RUNTIME_ENABLED"), False),
            "judicial_processed_dir": default_judicial_processed_dir,
            "judicial_exact_lookup_path": Path(
                os.getenv(
                    "JUDICIAL_EXACT_LOOKUP_PATH",
                    str(default_judicial_processed_dir / "judicial_exact_lookup.sqlite"),
                )
            ),
            "judicial_lexical_index_path": Path(
                os.getenv(
                    "JUDICIAL_LEXICAL_INDEX_PATH",
                    str(default_judicial_processed_dir / "judicial_lexical_index.sqlite"),
                )
            ),
            "judicial_vector_collection": os.getenv(
                "JUDICIAL_VECTOR_COLLECTION",
                "judicial_decisions_v1_shadow",
            ),
            "judicial_vector_enabled": _to_bool(os.getenv("JUDICIAL_VECTOR_ENABLED"), False),
            "legal_advisor_llm_enabled": _to_bool(os.getenv("LEGAL_ADVISOR_LLM_ENABLED"), True),
            "legal_rag_max_mevzuat_evidence": _to_int(os.getenv("LEGAL_RAG_MAX_MEVZUAT_EVIDENCE"), 6),
            "legal_rag_judicial_top_k": _to_int(os.getenv("LEGAL_RAG_JUDICIAL_TOP_K"), 20),
            "legal_rag_max_judicial_decisions": _to_int(os.getenv("LEGAL_RAG_MAX_JUDICIAL_DECISIONS"), 5),
            "legal_rag_max_chunks_per_decision": _to_int(os.getenv("LEGAL_RAG_MAX_CHUNKS_PER_DECISION"), 2),
            "legal_rag_max_total_evidence_chars": _to_int(os.getenv("LEGAL_RAG_MAX_TOTAL_EVIDENCE_CHARS"), 8000),
            "legal_rag_retrieval_timeout_ms": _to_int(os.getenv("LEGAL_RAG_RETRIEVAL_TIMEOUT_MS"), 8000),
            "legal_rag_llm_timeout_ms": _to_int(os.getenv("LEGAL_RAG_LLM_TIMEOUT_MS"), 15000),
            "legal_rag_verification_timeout_ms": _to_int(os.getenv("LEGAL_RAG_VERIFICATION_TIMEOUT_MS"), 5000),
            "legal_rag_max_query_chars": _to_int(os.getenv("LEGAL_RAG_MAX_QUERY_CHARS"), 4000),
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
