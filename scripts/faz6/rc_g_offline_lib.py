#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "api-gateway" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))

from eval_runner import build_report  # noqa: E402
from faz2a_hardening import (  # noqa: E402
    StructuredAnswerContract,
    apply_visible_citation_projection_v1,
    dedupe_strings,
    normalize_query_text,
)
from metrics import QuestionResult, aggregate_metrics, compute_metrics  # noqa: E402


DEFAULT_TODAY = date(2026, 3, 23)


def load_question_map(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions = payload["questions"] if isinstance(payload, dict) else payload
    return {item["id"]: item for item in questions}


def load_report_rows(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["question_id"]: item for item in payload["per_question"]}


def _normalize_explicit_article_refs(values: list[Any] | None) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for item in values or []:
        if isinstance(item, dict):
            law = item.get("law")
            madde = item.get("madde")
            if law and madde:
                refs.append((str(law), str(madde)))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            refs.append((str(item[0]), str(item[1])))
    return refs


def _build_rc_g_trace(
    *,
    reference_trace: dict[str, Any],
    result: Any,
    question_raw: str,
) -> dict[str, Any]:
    trace = copy.deepcopy(reference_trace)
    trace["question_raw"] = question_raw
    trace["question_normalized"] = normalize_query_text(question_raw)
    trace["answer_contract"] = result.answer_contract
    trace["model_cited_source_ids"] = result.model_cited_source_ids
    trace["law_scope_signal"] = result.law_scope_signal
    trace["final_mode"] = result.final_mode
    trace["final_reason"] = result.final_reason
    trace["recovery_profile"] = result.recovery_profile
    trace["hardening_diagnostics"] = result.diagnostics
    generation_outcome = trace.get("generation_outcome")
    if isinstance(generation_outcome, dict):
        generation_outcome["final_mode"] = result.final_mode
        generation_outcome["final_reason"] = result.final_reason
        generation_outcome["blocked"] = result.internal_blocked
    return trace


def replay_rc_g_row(
    *,
    question: dict[str, Any],
    rc_a_row: dict[str, Any],
    rc_d_row: dict[str, Any],
    today: date = DEFAULT_TODAY,
) -> QuestionResult:
    reference_trace = rc_d_row.get("trace") or {}
    parsed_query = reference_trace.get("parsed_query") or {}
    query_signals = reference_trace.get("query_signals") or {}
    question_raw = (
        reference_trace.get("question_raw")
        or rc_d_row.get("question_text")
        or question.get("question")
        or ""
    )
    mentioned_laws = parsed_query.get("mentioned_laws") or query_signals.get("mentioned_laws") or []
    explicit_article_refs = _normalize_explicit_article_refs(
        parsed_query.get("explicit_article_refs") or query_signals.get("explicit_article_refs")
    )
    law_filter = parsed_query.get("law_filter") or query_signals.get("law_filter")
    assembled_evidence = (
        reference_trace.get("assembled_evidence")
        or ((reference_trace.get("context_assembly") or {}).get("assembled_evidence"))
        or []
    )
    allowed_source_whitelist = (
        reference_trace.get("allowed_source_whitelist")
        or ((reference_trace.get("context_assembly") or {}).get("allowed_source_whitelist"))
        or []
    )
    generation_outcome = reference_trace.get("generation_outcome") or {}
    verification = generation_outcome.get("verification")
    blocked = bool(generation_outcome.get("blocked", False))

    contract = StructuredAnswerContract.model_validate(reference_trace.get("answer_contract") or {})
    current_citations = dedupe_strings(list(rc_d_row.get("cited_sources") or []))
    if contract.primary_source_id and contract.primary_source_id not in current_citations:
        current_citations = [contract.primary_source_id, *current_citations]
    contract.secondary_source_ids = [source_id for source_id in current_citations if source_id != contract.primary_source_id]

    if contract.unsupported_reason is None and contract.final_mode not in {"refusal", "blocked"}:
        projection_outcome = apply_visible_citation_projection_v1(
            contract=contract,
            mentioned_laws=list(mentioned_laws),
            explicit_article_refs=explicit_article_refs,
            assembled_evidence=list(assembled_evidence),
            allowed_source_whitelist=list(allowed_source_whitelist),
            law_scope_signal=reference_trace.get("law_scope_signal") or {},
            target_date=today,
        )
    else:
        projection_outcome = {
            "active": False,
            "applied": False,
            "added_source_ids": [],
            "final_citations": [],
            "skipped_reason": "final_mode_or_reason_ineligible",
        }

    if hasattr(projection_outcome, "final_citations"):
        final_citations = list(projection_outcome.final_citations)
    else:
        final_citations = list(projection_outcome.get("final_citations", current_citations))
    result = type(
        "RCGResult",
        (),
        {
            "answer_text": str(rc_d_row.get("answer_text") or contract.answer_text or ""),
            "citations": list(final_citations),
            "final_mode": str(rc_d_row.get("final_mode") or contract.final_mode),
            "final_reason": rc_d_row.get("final_reason") or contract.unsupported_reason,
            "internal_blocked": bool(rc_d_row.get("blocked", blocked)),
            "answer_contract": contract.model_dump(),
            "model_cited_source_ids": list(reference_trace.get("model_cited_source_ids") or []),
            "law_scope_signal": reference_trace.get("law_scope_signal") or {},
            "recovery_profile": "rc_g",
            "diagnostics": {
                "visible_citation_projection": (
                    {
                        "active": projection_outcome.active,
                        "applied": projection_outcome.applied,
                        "added_source_ids": projection_outcome.added_source_ids,
                        "final_citations": projection_outcome.final_citations,
                        "skipped_reason": projection_outcome.skipped_reason,
                    }
                    if hasattr(projection_outcome, "active")
                    else projection_outcome
                )
            },
        },
    )()
    trace = _build_rc_g_trace(reference_trace=reference_trace, result=result, question_raw=question_raw)

    metric = compute_metrics(
        question=question,
        answer_text=result.answer_text,
        cited_sources=result.citations,
        response_time_ms=float(rc_a_row.get("response_time_ms") or 0.0),
        blocked=result.internal_blocked,
        verification=verification,
        final_mode=result.final_mode,
        final_reason=result.final_reason,
        answer_contract=result.answer_contract,
        error=None,
        trace=trace,
    )
    metric.is_refusal = result.final_mode == "refusal"
    metric.refusal_correct = (bool(question.get("refusal_expected", False)) == metric.is_refusal)
    return metric


def question_result_to_row(result: QuestionResult) -> dict[str, Any]:
    payload = asdict(result)
    return {key: value for key, value in payload.items() if value is not None}


def build_rc_g_report(
    *,
    results: list[QuestionResult],
    questions_path: Path,
    eval_family: str,
    checkpoint_ref: str,
    git_commit: str,
) -> dict[str, Any]:
    summary = aggregate_metrics(results)
    return build_report(
        results=results,
        summary=summary,
        questions_path=questions_path,
        api_url="offline-rc-g-replay",
        mock_mode=False,
        eval_family=eval_family,
        model_ref="Qwen/Qwen3.5-35B-A3B-FP8",
        checkpoint_ref=checkpoint_ref,
        git_commit=git_commit,
        report_role="post_guardrail",
        config_fingerprint={
            "runner_mode": "offline_rc_g_replay",
            "claim_binding_version": "selective-claim-binding-v3",
            "final_mode_mapping_version": "final-mode-mapping-v3",
            "visible_citation_projection_version": "visible-citation-projection-v1",
            "primary_source_freeze_version": "immutable-primary-source-freeze-v1",
        },
    )


def current_git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
