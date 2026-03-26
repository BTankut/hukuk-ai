from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE_TAG = "2026-03-25"

FAMILY_SEQUENCE = ("faz1-50", "v2-95", "v3-170")
FAMILY_ORDER = {family_id: index for index, family_id in enumerate(FAMILY_SEQUENCE)}
CANDIDATE_SEQUENCE = ("rc_g", "rc_j")

QUESTIONS_PATH_BY_FAMILY = {
    "faz1-50": "configs/evaluation/test_questions.json",
    "v2-95": "configs/evaluation/test_questions_v2_95.json",
    "v3-170": "configs/evaluation/test_questions_v3_170.json",
}

STAGE_LADDER = (
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
)

UPSTREAM_STAGES = STAGE_LADDER[:6]
EQUIVALENCE_FIELDS = STAGE_LADDER + (
    "answer_body_hash",
    "citation_body_hash",
    "refusal_body_hash",
)

PRIMARY_REASONS = {
    "capture_runtime_topology_delta",
    "effective_view_accounting_delta",
    "response_envelope_only_shift",
    "final_mode_mapping_delta",
    "blocked_reason_projection_delta",
    "output_surface_snapshot_rotation",
    "historical_authority_restored",
    "current_authority_non_reproducible",
    "current_authority_contract_breach",
    "unexplained_current_authority_drift",
}

DECISION_TO_NEXT_WORK = {
    "PASS - Historical Authority Restored": "rc-m authoritative summary truth recapture reopen",
    "PASS - Stable Current Authority Re-Captured": "current authority baseline rotation gate",
    "NO-GO - Current Authority Non-Reproducible": "current authority runtime forensics",
    "NO-GO - Current Authority Contract Breach": "current authority contract-breach forensics",
    "NO-GO - Unexplained Current Authority Drift": "current authority drift forensics recapture",
}


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def family_sort_key(family_id: str) -> tuple[int, str]:
    return (FAMILY_ORDER.get(family_id, 999), family_id)


def bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def markdown_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> list[str]:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return [header, divider, *body]


def family_slug(family_id: str) -> str:
    return family_id.replace("-", "_")


def _stage_counter(mismatch_rows: list[dict[str, Any]]) -> dict[str, int]:
    histogram: Counter[str] = Counter()
    for row in mismatch_rows:
        stage = row.get("first_divergence_stage")
        if isinstance(stage, str) and stage:
            histogram[stage] += 1
    return dict(sorted(histogram.items()))


def family_report_row(report: dict[str, Any], *, report_path: str) -> dict[str, Any]:
    mismatch_rows = [row for row in report.get("mismatch_rows") or [] if isinstance(row, dict)]
    stage_histogram = _stage_counter(mismatch_rows)
    mismatch_question_ids = [str(row["question_id"]) for row in mismatch_rows]
    mismatch_ordinals = [int(row["ordinal_index"]) for row in mismatch_rows]
    runtime_error_count = int(report.get("reference_runtime_error_count", 0)) + int(
        report.get("candidate_runtime_error_count", 0)
    )
    breach_in_o0_o5 = any(stage in UPSTREAM_STAGES for stage in stage_histogram)
    return {
        "family_id": str(report["family_id"]),
        "report_path": report_path,
        "mismatch_count": int(report.get("mismatch_count", 0)),
        "runtime_error_count": runtime_error_count,
        "family_metric_delta_zero": bool(report.get("family_metric_delta_zero")),
        "mismatch_stage_histogram": stage_histogram,
        "mismatch_question_ids": mismatch_question_ids,
        "mismatch_ordinals": mismatch_ordinals,
        "breach_in_o0_o5": breach_in_o0_o5,
        "breach_in_f0_f12": breach_in_o0_o5,
    }


def _candidate_row_from_authoritative(
    row: dict[str, Any],
    *,
    candidate_kind: str,
) -> dict[str, Any]:
    if candidate_kind == "rc_g":
        field = lambda name: row.get(f"reference_{name}")
        runtime_error = int(row.get("reference_effective_runtime_error", 0))
        error_type = row.get("reference_effective_error_type")
        error_rerun_used = int(row.get("reference_error_rerun_used", 0))
        worker_id = row.get("reference_worker_id")
        process_id = row.get("reference_process_id")
        session_namespace = row.get("reference_session_namespace")
        cache_namespace = row.get("reference_cache_namespace")
    else:
        field = lambda name: row.get(name)
        runtime_error = int(row.get("effective_runtime_error", 0))
        error_type = row.get("effective_error_type")
        error_rerun_used = int(row.get("candidate_error_rerun_used", 0))
        worker_id = row.get("worker_id")
        process_id = row.get("process_id")
        session_namespace = row.get("session_namespace")
        cache_namespace = row.get("cache_namespace")
    return {
        "question_id": str(row["question_id"]),
        "ordinal_index": int(row["ordinal_index"]),
        "runtime_error": runtime_error,
        "error_type": error_type if isinstance(error_type, str) else None,
        "error_rerun_used": error_rerun_used,
        "effective_view_member": int(row.get("effective_view_member", 0)),
        "worker_id": worker_id if isinstance(worker_id, str) else None,
        "process_id": process_id if isinstance(process_id, str) else None,
        "session_namespace": session_namespace if isinstance(session_namespace, str) else None,
        "cache_namespace": cache_namespace if isinstance(cache_namespace, str) else None,
        "normalized_request_hash": field("normalized_request_hash"),
        "model_request_payload_hash": field("model_request_payload_hash"),
        "generation_contract_hash": field("generation_contract_hash"),
        "preprojection_anchor_hash": field("preprojection_anchor_hash"),
        "cited_projection_hash": field("cited_projection_hash"),
        "citation_set_projection_hash": field("citation_set_projection_hash"),
        "final_mode_mapping_hash": field("final_mode_mapping_hash"),
        "blocked_reason_set_hash": field("blocked_reason_set_hash"),
        "final_answer_payload_hash": field("final_answer_payload_hash"),
        "response_envelope_hash": field("response_envelope_hash"),
        "serialized_output_hash": field("serialized_output_hash"),
        "answer_body_hash": field("answer_body_hash"),
        "citation_body_hash": field("citation_body_hash"),
        "refusal_body_hash": field("refusal_body_hash"),
    }


def candidate_rows_from_report(report: dict[str, Any], candidate_kind: str) -> list[dict[str, Any]]:
    rows = [
        _candidate_row_from_authoritative(item, candidate_kind=candidate_kind)
        for item in report.get("authoritative_rows") or []
        if isinstance(item, dict)
    ]
    rows.sort(key=lambda item: item["ordinal_index"])
    return rows


def candidate_fingerprint_entry(
    report: dict[str, Any],
    *,
    report_path: str,
    capture_id: str,
    candidate_kind: str,
) -> dict[str, Any]:
    rows = candidate_rows_from_report(report, candidate_kind)
    row_payload = [
        {
            "question_id": row["question_id"],
            "ordinal_index": row["ordinal_index"],
            "runtime_error": row["runtime_error"],
            "error_type": row["error_type"],
            "error_rerun_used": row["error_rerun_used"],
            "effective_view_member": row["effective_view_member"],
            **{field: row.get(field) for field in EQUIVALENCE_FIELDS},
        }
        for row in rows
    ]
    if candidate_kind == "rc_g":
        checkpoint_ref = str(report.get("reference_checkpoint_ref") or "rc_g")
        lane_id = str(rows[0].get("process_id") or report.get("reference_run_label") or "rc_g") if rows else "rc_g"
    else:
        checkpoint_ref = str(report.get("candidate_checkpoint_ref") or "rc_j")
        lane_id = str(rows[0].get("process_id") or report.get("candidate_run_label") or "rc_j") if rows else "rc_j"
    return {
        "capture_id": capture_id,
        "family_id": str(report["family_id"]),
        "candidate_kind": candidate_kind,
        "report_path": report_path,
        "checkpoint_ref": checkpoint_ref,
        "lane_id": lane_id,
        "row_count": len(rows),
        "runtime_error_count": sum(int(row["runtime_error"]) for row in rows),
        "error_rerun_row_count": sum(int(row["error_rerun_used"]) for row in rows),
        "worker_ids": sorted({row["worker_id"] for row in rows if row.get("worker_id")}),
        "process_ids": sorted({row["process_id"] for row in rows if row.get("process_id")}),
        "session_namespaces": sorted({row["session_namespace"] for row in rows if row.get("session_namespace")}),
        "cache_namespaces": sorted({row["cache_namespace"] for row in rows if row.get("cache_namespace")}),
        "fingerprint_hash": stable_hash(row_payload),
    }


def _summary_compare_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "mismatch_count": int(row.get("mismatch_count", 0)),
        "runtime_error_count": int(row.get("runtime_error_count", 0)),
        "family_metric_delta_zero": bool(row.get("family_metric_delta_zero")),
        "mismatch_stage_histogram": dict(row.get("mismatch_stage_histogram") or {}),
        "mismatch_question_ids": list(row.get("mismatch_question_ids") or []),
        "mismatch_ordinals": list(row.get("mismatch_ordinals") or []),
    }


def compare_family_rows(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_core = _summary_compare_fields(left)
    right_core = _summary_compare_fields(right)
    mismatched_fields = sorted(key for key in left_core if left_core[key] != right_core[key])
    return {
        "family_id": str(left["family_id"]),
        "match": not mismatched_fields,
        "mismatched_fields": mismatched_fields,
        "left": left_core,
        "right": right_core,
    }


def compare_capture_reports(capture_a: dict[str, Any], capture_b: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    family_rows_a = {row["family_id"]: row for row in capture_a.get("families") or []}
    family_rows_b = {row["family_id"]: row for row in capture_b.get("families") or []}
    family_comparisons = [
        compare_family_rows(family_rows_a[family_id], family_rows_b[family_id])
        for family_id in FAMILY_SEQUENCE
        if family_id in family_rows_a and family_id in family_rows_b
    ]

    fingerprint_rows_a = {
        (row["family_id"], row["candidate_kind"]): row for row in capture_a.get("candidate_fingerprints") or []
    }
    fingerprint_rows_b = {
        (row["family_id"], row["candidate_kind"]): row for row in capture_b.get("candidate_fingerprints") or []
    }
    fingerprint_comparisons = []
    for family_id in FAMILY_SEQUENCE:
        for candidate_kind in CANDIDATE_SEQUENCE:
            left = fingerprint_rows_a[(family_id, candidate_kind)]
            right = fingerprint_rows_b[(family_id, candidate_kind)]
            match = left["fingerprint_hash"] == right["fingerprint_hash"]
            fingerprint_comparisons.append(
                {
                    "family_id": family_id,
                    "candidate_kind": candidate_kind,
                    "match": match,
                    "fingerprint_hash_a": left["fingerprint_hash"],
                    "fingerprint_hash_b": right["fingerprint_hash"],
                    "row_count_a": left["row_count"],
                    "row_count_b": right["row_count"],
                }
            )
    return family_comparisons, fingerprint_comparisons


def first_divergence_stage_for_rows(left: dict[str, Any], right: dict[str, Any]) -> str:
    if (
        int(left.get("runtime_error", 0)) != int(right.get("runtime_error", 0))
        or int(left.get("error_rerun_used", 0)) != int(right.get("error_rerun_used", 0))
        or int(left.get("effective_view_member", 0)) != int(right.get("effective_view_member", 0))
    ):
        return "normalized_request_hash"
    for stage in STAGE_LADDER:
        if left.get(stage) != right.get(stage):
            return stage
    if left.get("answer_body_hash") != right.get("answer_body_hash"):
        return "serialized_output_hash"
    if left.get("citation_body_hash") != right.get("citation_body_hash"):
        return "serialized_output_hash"
    if left.get("refusal_body_hash") != right.get("refusal_body_hash"):
        return "serialized_output_hash"
    return "serialized_output_hash"


def primary_reason_for_stage(stage: str, *, runtime_mismatch: bool, capture_compare: bool) -> str:
    if runtime_mismatch:
        return "effective_view_accounting_delta"
    if stage in UPSTREAM_STAGES:
        return "capture_runtime_topology_delta" if capture_compare else "current_authority_contract_breach"
    if stage == "final_mode_mapping_hash":
        return "final_mode_mapping_delta"
    if stage == "blocked_reason_set_hash":
        return "blocked_reason_projection_delta"
    if stage == "response_envelope_hash":
        return "response_envelope_only_shift"
    if stage in {"final_answer_payload_hash", "serialized_output_hash"}:
        return "output_surface_snapshot_rotation"
    return "unexplained_current_authority_drift"


def dominant_counter_value(rows: list[dict[str, Any]], key: str) -> str | None:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if isinstance(value, str) and value:
            counter[value] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]
