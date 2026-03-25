from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


STAGE_LADDER = [
    "normalized_request_hash",
    "model_request_payload_hash",
    "generation_contract_hash",
    "preprojection_anchor_hash",
    "cited_projection_hash",
    "citation_set_projection_hash",
    "final_mode_mapping_hash",
    "blocked_reason_set_hash",
    "final_answer_payload_hash",
    "response_envelope_hash",
    "serialized_output_hash",
]

ALLOWED_CHANGED_FIELDS = {
    "final_mode_mapping_hash",
    "blocked_reason_set_hash",
    "response_envelope_hash",
    "serialized_output_hash",
}

IMMUTABLE_BREACH_STAGES = {
    "normalized_request_hash",
    "model_request_payload_hash",
    "generation_contract_hash",
    "preprojection_anchor_hash",
    "cited_projection_hash",
    "citation_set_projection_hash",
    "final_answer_payload_hash",
}

PRIMARY_REASONS = {
    "final_mode_mapping_delta",
    "blocked_reason_projection_delta",
    "response_envelope_projection_delta",
    "repair_surface_breach",
    "unexplained_authoritative_output_repair_drift",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def question_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in report.get("per_question", [])
        if isinstance(row, dict) and row.get("question_id")
    ]


def question_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["question_id"]): row for row in question_rows(report)}


def question_bank_rows(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        rows = payload["questions"]
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError(f"unsupported question bank format: {path}")

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        question_id = row.get("question_id") or row.get("id")
        if not question_id:
            continue
        normalized_rows.append({"question_id": str(question_id), **row})
    return normalized_rows


def question_bank_index(path: Path) -> dict[str, dict[str, Any]]:
    rows = question_bank_rows(path)
    return {
        str(row["question_id"]): {"ordinal_index": idx, **row}
        for idx, row in enumerate(rows, start=1)
    }


def runtime_error_row(question: dict[str, Any] | None) -> tuple[bool, str | None]:
    if not isinstance(question, dict):
        return True, "question_missing"
    error_value = question.get("error")
    if isinstance(error_value, str) and error_value.strip():
        return True, error_value.strip()
    return False, None


def _parity_trace(question: dict[str, Any]) -> dict[str, Any]:
    trace = (question.get("trace") or {}) if isinstance(question, dict) else {}
    v3_trace = trace.get("v3_runtime_parity_trace")
    if isinstance(v3_trace, dict):
        return v3_trace
    parity_trace = trace.get("parity_trace")
    if isinstance(parity_trace, dict):
        return parity_trace
    return {}


def _stage_entries(question: dict[str, Any]) -> list[dict[str, Any]]:
    trace = _parity_trace(question)
    stages = trace.get("stages") or []
    if isinstance(stages, dict):
        return [{"stage": name, **payload} for name, payload in stages.items() if isinstance(payload, dict)]
    return [item for item in stages if isinstance(item, dict) and item.get("stage")]


def stage_map(question: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["stage"]): item for item in _stage_entries(question) if item.get("stage")}


def stage_hash(question: dict[str, Any], stage_name: str) -> str | None:
    stage = stage_map(question).get(stage_name) or {}
    value = stage.get("hash")
    if isinstance(value, str) and value:
        return value
    payload = stage.get("payload")
    if isinstance(payload, dict):
        return stable_hash(payload)
    return None


def stage_payload(question: dict[str, Any], stage_name: str) -> dict[str, Any]:
    stage = stage_map(question).get(stage_name) or {}
    payload = stage.get("payload")
    return payload if isinstance(payload, dict) else {}


def preprojection_hash(question: dict[str, Any]) -> str | None:
    trace = _parity_trace(question)
    value = trace.get("preprojection_hash")
    return value if isinstance(value, str) and value else None


def candidate_identity(report: dict[str, Any], fallback: str) -> str:
    meta = report.get("report_meta") if isinstance(report.get("report_meta"), dict) else {}
    checkpoint_ref = meta.get("checkpoint_ref")
    if isinstance(checkpoint_ref, str) and checkpoint_ref.strip():
        return checkpoint_ref.strip()
    return fallback


def lane_identity(report: dict[str, Any], fallback: str) -> str:
    meta = report.get("report_meta") if isinstance(report.get("report_meta"), dict) else {}
    model_ref = meta.get("model_ref")
    if isinstance(model_ref, str) and model_ref.strip():
        return model_ref.strip()
    return fallback


def _sorted_unique_strs(values: list[Any]) -> list[str]:
    return sorted({str(item).strip() for item in values if isinstance(item, str) and str(item).strip()})


def normalized_parity_payload(question: dict[str, Any]) -> dict[str, Any]:
    payload = stage_payload(question, "normalized_parity_object")
    if payload:
        return payload
    answer_contract = question.get("answer_contract")
    contract = answer_contract if isinstance(answer_contract, dict) else {}
    cited_sources = question.get("cited_sources")
    citations = cited_sources if isinstance(cited_sources, list) else []
    answer_text = question.get("answer_text")
    final_mode = question.get("final_mode") or contract.get("final_mode") or "answer"
    refusal_reason = contract.get("unsupported_reason") or question.get("final_reason")
    source_ids: list[str] = []
    primary = contract.get("primary_source_id")
    if isinstance(primary, str) and primary.strip():
        source_ids.append(primary.strip())
    secondary = contract.get("secondary_source_ids")
    if isinstance(secondary, list):
        source_ids.extend(str(item).strip() for item in secondary if isinstance(item, str) and item.strip())
    return {
        "final_mode": final_mode,
        "answer_body": answer_text if final_mode != "refusal" and isinstance(answer_text, str) else "",
        "refusal_body": answer_text if final_mode == "refusal" and isinstance(answer_text, str) else "",
        "refusal_reason": refusal_reason if isinstance(refusal_reason, str) else None,
        "ordered_citation_list": citations,
        "ordered_source_id_list": source_ids,
        "ordered_canonical_norm_keys": source_ids,
        "visible_citation_projection": citations,
    }


def response_envelope_payload(question: dict[str, Any]) -> dict[str, Any]:
    payload = stage_payload(question, "response_envelope")
    if payload:
        return payload
    payload = stage_payload(question, "eval_client_parsed_object")
    if payload:
        return payload
    citations = question.get("cited_sources")
    return {
        "citations": citations if isinstance(citations, list) else [],
        "blocked": bool(question.get("blocked")),
        "guardrails_reasons": [],
        "final_mode": question.get("final_mode"),
        "final_reason": question.get("final_reason"),
        "answer_contract": question.get("answer_contract") if isinstance(question.get("answer_contract"), dict) else {},
    }


def serialized_output_payload(question: dict[str, Any]) -> dict[str, Any]:
    payload = stage_payload(question, "eval_client_parsed_object")
    if payload:
        return payload
    envelope = response_envelope_payload(question)
    return {
        "answer_text": question.get("answer_text") or "",
        "citations": envelope.get("citations") or [],
        "blocked": envelope.get("blocked"),
        "final_mode": envelope.get("final_mode"),
        "final_reason": envelope.get("final_reason"),
        "answer_contract": envelope.get("answer_contract") or {},
        "verification": envelope.get("verification"),
    }


def parity_fields(question: dict[str, Any]) -> dict[str, Any]:
    normalized = normalized_parity_payload(question)
    envelope = response_envelope_payload(question)
    serialized = serialized_output_payload(question)

    citations = normalized.get("ordered_citation_list")
    citations_list = citations if isinstance(citations, list) else []
    sources = normalized.get("ordered_source_id_list")
    source_list = sources if isinstance(sources, list) else []
    canonical = normalized.get("ordered_canonical_norm_keys")
    canonical_list = canonical if isinstance(canonical, list) else []
    visible_projection = normalized.get("visible_citation_projection")
    visible_projection_list = visible_projection if isinstance(visible_projection, list) else []
    guardrails = envelope.get("guardrails_reasons")
    blocked_reason_set = _sorted_unique_strs(guardrails if isinstance(guardrails, list) else [])
    final_mode = normalized.get("final_mode")
    refusal_mode = "refusal" if final_mode == "refusal" else "answer"
    answer_body = normalized.get("answer_body") if isinstance(normalized.get("answer_body"), str) else ""
    refusal_body = normalized.get("refusal_body") if isinstance(normalized.get("refusal_body"), str) else ""
    refusal_reason = normalized.get("refusal_reason") if isinstance(normalized.get("refusal_reason"), str) else None

    worker_payload = stage_payload(question, "worker_assignment_tuple")
    session_payload = stage_payload(question, "session_namespace_after_payload_freeze")
    cache_payload = stage_payload(question, "cache_namespace_or_cache_key")

    return {
        "normalized_request_hash": stage_hash(question, "normalized_request"),
        "model_request_payload_hash": stage_hash(question, "model_request_payload"),
        "generation_contract_hash": stage_hash(question, "generation_contract"),
        "preprojection_anchor_hash": preprojection_hash(question),
        "cited_projection_hash": stable_hash(visible_projection_list),
        "citation_set_projection_hash": stable_hash(_sorted_unique_strs(canonical_list or source_list or citations_list)),
        "final_mode_mapping_hash": stable_hash(
            {
                "final_mode": final_mode,
                "refusal_mode": refusal_mode,
                "refusal_reason": refusal_reason,
                "blocked_reason_set": blocked_reason_set,
            }
        ),
        "blocked_reason_set_hash": stable_hash(blocked_reason_set),
        "final_answer_payload_hash": stable_hash(normalized),
        "response_envelope_hash": stage_hash(question, "response_envelope") or stable_hash(envelope),
        "serialized_output_hash": stage_hash(question, "eval_client_parsed_object") or stable_hash(serialized),
        "refusal_mode": refusal_mode,
        "refusal_body_hash": stable_hash(refusal_body),
        "answer_body_hash": stable_hash(answer_body),
        "citation_body_hash": stable_hash(citations_list),
        "answer_body": answer_body,
        "citation_body": citations_list,
        "refusal_body": refusal_body,
        "blocked_reason_set": blocked_reason_set,
        "worker_id": worker_payload.get("pinned_worker_id"),
        "process_id": worker_payload.get("process_id"),
        "session_namespace": session_payload.get("namespace"),
        "cache_namespace": cache_payload.get("namespace") or cache_payload.get("cache_key"),
    }


def first_divergence(reference_fields: dict[str, Any], candidate_fields: dict[str, Any]) -> str | None:
    for key in STAGE_LADDER:
        if reference_fields.get(key) != candidate_fields.get(key):
            return key
    return None


def primary_reason(*, first_divergence_stage: str | None, unexplained: bool = False) -> str:
    if unexplained:
        return "unexplained_authoritative_output_repair_drift"
    if first_divergence_stage in IMMUTABLE_BREACH_STAGES:
        return "repair_surface_breach"
    if first_divergence_stage == "final_mode_mapping_hash":
        return "final_mode_mapping_delta"
    if first_divergence_stage == "blocked_reason_set_hash":
        return "blocked_reason_projection_delta"
    if first_divergence_stage in {"response_envelope_hash", "serialized_output_hash"}:
        return "response_envelope_projection_delta"
    return "unexplained_authoritative_output_repair_drift"


def metric_snapshot(question: dict[str, Any]) -> dict[str, float]:
    return {
        "citation": float(bool(question.get("has_citation"))),
        "correct_source": float(question.get("correct_source_rate", 0.0)),
        "hallucination": float(bool(question.get("is_hallucination"))),
        "refusal": float(question.get("refusal_correct", 0.0)),
        "error": float(bool(question.get("error"))),
    }


def metric_delta(reference_questions: list[dict[str, Any]], candidate_questions: list[dict[str, Any]]) -> dict[str, float]:
    def average(rows: list[dict[str, Any]], key: str) -> float:
        if not rows:
            return 0.0
        return sum(metric_snapshot(row)[key] for row in rows) / len(rows)

    return {
        "citation_delta": round(average(candidate_questions, "citation") - average(reference_questions, "citation"), 10),
        "correct_source_delta": round(
            average(candidate_questions, "correct_source") - average(reference_questions, "correct_source"),
            10,
        ),
        "hallucination_delta": round(
            average(candidate_questions, "hallucination") - average(reference_questions, "hallucination"),
            10,
        ),
        "refusal_delta": round(average(candidate_questions, "refusal") - average(reference_questions, "refusal"), 10),
        "error_delta": round(average(candidate_questions, "error") - average(reference_questions, "error"), 10),
    }
