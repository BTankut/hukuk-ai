from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz7"))

from build_output_parity_report import normalize_question  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def family_from_report(report: dict[str, Any]) -> str:
    return str(report.get("report_meta", {}).get("eval_family") or "unknown")


def question_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["question_id"]): item
        for item in report.get("per_question", [])
        if isinstance(item, dict) and item.get("question_id")
    }


def collect_error_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    family = family_from_report(report)
    for item in report.get("per_question", []):
        if not isinstance(item, dict) or not item.get("question_id") or not item.get("error"):
            continue
        rows.append(
            {
                "family": family,
                "question_id": item["question_id"],
                "kind": "parity_runtime_error",
                "error": item["error"],
            }
        )
    return rows


def load_question_bank(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions = payload if isinstance(payload, list) else payload.get("questions", [])
    return {str(item["id"]): item for item in questions if isinstance(item, dict) and item.get("id")}


def stage_map(question: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parity_trace = (question.get("trace") or {}).get("parity_trace") or {}
    stages = parity_trace.get("stages") or []
    return {
        str(item.get("stage")): item
        for item in stages
        if isinstance(item, dict) and item.get("stage")
    }


def eval_client_payload(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "final_mode": question.get("final_mode"),
        "answer_text": question.get("answer_text") or "",
        "cited_sources": list(question.get("cited_sources") or []),
        "final_reason": question.get("final_reason"),
        "answer_contract": question.get("answer_contract"),
    }


def normalized_parity_payload(question: dict[str, Any]) -> dict[str, Any]:
    return normalize_question(question)
