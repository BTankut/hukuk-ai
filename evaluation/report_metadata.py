"""Shared identity metadata helpers for eval report artifacts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
KNOWN_EVAL_FAMILIES = {
    "test_questions.json": "faz1-50",
    "test_questions_v2_95.json": "v2-95",
    "test_questions_v3_170.json": "v3-170",
}


def infer_eval_family(questions_path: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit.strip()
    return KNOWN_EVAL_FAMILIES.get(questions_path.name, questions_path.stem)


def resolve_model_ref(
    explicit: str | None,
    *,
    runner: str,
    mock_mode: bool,
    model: str | None = None,
) -> str:
    if explicit:
        return explicit.strip()
    env_value = os.getenv("MODEL_REF")
    if env_value:
        return env_value.strip()
    if runner in {"eval_vllm_direct", "eval_transformers_direct"} and model:
        return model
    return "mock-chat-client" if mock_mode else "gateway-api"


def resolve_checkpoint_ref(
    explicit: str | None,
    *,
    runner: str,
    api_url: str,
    mock_mode: bool,
    model: str | None = None,
) -> str:
    if explicit:
        return explicit.strip()
    env_value = os.getenv("CHECKPOINT_REF")
    if env_value:
        return env_value.strip()
    if mock_mode:
        return "mock-runtime"
    if runner == "eval_transformers_direct" and model:
        return f"transformers:{model}"
    if model:
        return f"vllm:{model}"
    return f"api:{api_url.rstrip('/')}"


def resolve_git_commit(explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    env_value = os.getenv("GIT_COMMIT")
    if env_value:
        return env_value.strip()
    return "unknown"


def build_identity_metadata(
    *,
    runner: str,
    questions_path: Path,
    api_url: str,
    mock_mode: bool,
    eval_family: str | None = None,
    model_ref: str | None = None,
    checkpoint_ref: str | None = None,
    git_commit: str | None = None,
    report_role: str = "evaluation",
    model: str | None = None,
    config_fingerprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "runner": runner,
        "report_role": report_role,
        "eval_family": infer_eval_family(questions_path, explicit=eval_family),
        "model_ref": resolve_model_ref(
            model_ref,
            runner=runner,
            mock_mode=mock_mode,
            model=model,
        ),
        "checkpoint_ref": resolve_checkpoint_ref(
            checkpoint_ref,
            runner=runner,
            api_url=api_url,
            mock_mode=mock_mode,
            model=model,
        ),
        "git_commit": resolve_git_commit(git_commit),
        "config_fingerprint": config_fingerprint or {},
    }
