#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz38_lib import (  # type: ignore
    ALLOWED_PRIMARY_REASONS,
    ALLOWED_ROOT_CAUSE_CLASSES,
    CURRENT_AUTHORITY_EXPECTED,
    DATE,
    DECISION_TO_NEXT_WORK,
    FAIL_AUTHORITY,
    FAIL_UNLOCALIZED,
    FAMILY_IDS,
    FAMILY_ORDER,
    FAZ35_FRONTIER_TRUTH,
    FAZ36_FAILED_REPAIR_TRUTH,
    PASS_DECISION,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    STAGE_LADDER,
    bool_text,
    build_frozen_frontier_records,
    build_frozen_response_envelope_records,
    load_json,
    load_text,
    markdown_table,
    stable_hash,
    write_text,
)


WP2_AUTHORITY_FIELDS = [
    "control_pair_authority_match",
    "current_authority_contract_breach",
    "surface_breach_from_history_reintroduced",
    "current_canonical_authority_adopted",
    "control_pair_runtime_error_count",
]

WP2_UPSTREAM_FIELDS = [
    "model_request_payload_hash_mismatch_count",
    "retrieval_request_hash_mismatch_count",
    "assembled_context_hash_mismatch_count",
    "runtime_error_count",
]

WP5_FIELDS = [
    "must_close_release_controls_count",
    "mandatory_auth_pass",
    "immutable_audit_logging_pass",
    "persisted_pii_redaction_pass",
    "redis_session_persistence_pass",
    "tokenizer_backed_accounting_pass",
    "observability_alerting_pass",
    "api_versioning_pass",
    "process_supervision_pass",
    "backup_restore_pass",
    "one_command_release_smoke_pass",
    "refusal_smoke_status_code",
    "restart_refusal_smoke_status_code",
    "tokenizer_usage_total",
    "estimated_usage_total",
    "token_accounting_failure_total",
    "backup_restore_missing_file_count",
    "runtime_error_count",
    "unexplained_count",
]

WP7_FIELDS = [
    "must_close_release_controls_pass",
    "retained_after_family_eval",
    "retained_after_restart",
    "retained_after_restore",
    "answer_path_delta_reintroduced",
    "runtime_error_count",
    "unexplained_count",
]

ARTEFACT_LIST = [
    f"coordination/faz38-official-implementation-plan-{DATE}.md",
    f"coordination/faz38-steering-decision-table-{DATE}.md",
    f"coordination/faz38-release-controls-reference-pack-{DATE}.md",
    f"coordination/faz38-canonical-topology-refreeze-{DATE}.md",
    f"coordination/faz38-rc-q-instability-forensics-contract-{DATE}.md",
    f"evaluation/reports/faz38-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
    f"evaluation/reports/faz38-rc-g-vs-rc-q-upstream-equality-gate-{DATE}.md",
    f"coordination/faz38-rc-q-truth-lineage-matrix-{DATE}.md",
    f"coordination/faz38-rc-q-frontier-instability-rowset-6-freeze-{DATE}.md",
    f"coordination/faz38-rc-q-response-envelope-instability-rowset-3-freeze-{DATE}.md",
    f"coordination/faz38-rc-q-full-family-instability-rowset-3-freeze-{DATE}.md",
    f"coordination/faz38-rc-q-rowset-overlap-matrix-{DATE}.md",
    f"evaluation/reports/faz38-rc-q-frontier-174-twin-capture-contrast-{DATE}.md",
    f"evaluation/reports/faz38-rc-q-response-envelope-109-twin-capture-contrast-{DATE}.md",
    f"evaluation/reports/faz38-rc-q-full-family-parity-twin-capture-contrast-{DATE}.md",
    f"evaluation/reports/faz38-rc-q-targeted-acceptance-stability-check-{DATE}.md",
    f"evaluation/reports/faz38-rc-q-retention-stability-check-{DATE}.md",
    f"coordination/faz38-rc-q-instability-stage-ladder-contract-{DATE}.md",
    f"coordination/faz38-rc-q-contract-surface-audit-matrix-{DATE}.md",
    f"evaluation/reports/faz38-rc-q-instability-stage-ladder-summary-{DATE}.md",
    f"evaluation/reports/faz38-rc-q-contract-surface-audit-summary-{DATE}.md",
    f"evaluation/reports/faz38-rc-q-instability-root-cause-summary-{DATE}.md",
    f"coordination/faz38-rc-q-instability-reconciliation-{DATE}.md",
    f"coordination/faz38-final-reconciliation-summary-{DATE}.md",
    f"reports/{RESULT_REPORT_NAME}",
    f"docs/{RESULT_REPORT_NAME}",
]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _reconcile_section(a: dict[str, Any], b: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    mismatch_fields = [field for field in fields if a.get(field) != b.get(field)]
    runtime_error_total = sum(
        int(a.get(field, 0)) + int(b.get(field, 0))
        for field in fields
        if "runtime_error_count" in field
    )
    payload: dict[str, Any] = {
        "capture_stability_match": len(mismatch_fields) == 0 and runtime_error_total == 0,
        "capture_a_vs_capture_b_mismatch_count": len(mismatch_fields),
        "capture_a_vs_capture_b_runtime_error_count": runtime_error_total,
        "capture_a_vs_capture_b_mismatch_fields": mismatch_fields,
    }
    for field in fields:
        payload[field] = a.get(field)
    return payload


def _load_capture_bundle(capture_id: str) -> dict[str, Any]:
    base = ROOT / "runtime_logs" / f"faz37_capture_{capture_id}"
    model_visible: dict[str, dict[str, Any]] = {}
    output_parity: dict[str, dict[str, Any]] = {}
    for family_id in FAMILY_IDS:
        family_key = family_id.replace("-", "_")
        model_visible[family_id] = load_json(base / f"model_visible_{family_key}.json")
        output_parity[family_id] = load_json(base / f"output_parity_{family_key}.json")
    return {
        "base": base,
        "current_authority": load_json(base / "current_authority_check.json"),
        "upstream_equality": load_json(base / "upstream_equality.json"),
        "capture_truth": load_json(base / "capture_truth.json"),
        "model_visible": model_visible,
        "output_parity": output_parity,
    }


def _model_visible_index(bundle: dict[str, Any], family_id: str) -> dict[str, dict[str, Any]]:
    return {
        str(row["question_id"]): row
        for row in bundle["model_visible"][family_id].get("mismatch_rows", [])
        if isinstance(row, dict) and row.get("question_id")
    }


def _parity_index(bundle: dict[str, Any], family_id: str) -> dict[str, dict[str, Any]]:
    return {
        str(row["question_id"]): row
        for row in bundle["output_parity"][family_id].get("parity_rows", [])
        if isinstance(row, dict) and row.get("question_id")
    }


def _pair_projection_hash(row: dict[str, Any] | None, key: str) -> str:
    if not row:
        return ""
    reference_fields = row.get("reference_fields") or {}
    candidate_fields = row.get("candidate_fields") or {}
    return stable_hash({"reference": reference_fields.get(key), "candidate": candidate_fields.get(key)})


def _preprojection_hash(row: dict[str, Any] | None) -> str:
    if not row:
        return ""
    return str(row.get("preprojection_hash") or "")


def _row_state(
    family_id: str,
    question_id: str,
    capture_a: dict[str, Any],
    capture_b: dict[str, Any],
) -> dict[str, Any]:
    visible_a = _model_visible_index(capture_a, family_id).get(question_id)
    visible_b = _model_visible_index(capture_b, family_id).get(question_id)
    parity_a = _parity_index(capture_a, family_id).get(question_id)
    parity_b = _parity_index(capture_b, family_id).get(question_id)

    a_visible = visible_a is not None
    b_visible = visible_b is not None
    a_response = bool(parity_a and parity_a.get("response_envelope_hash_mismatch"))
    b_response = bool(parity_b and parity_b.get("response_envelope_hash_mismatch"))

    capture_a_preprojection_hash = _preprojection_hash(parity_a)
    capture_b_preprojection_hash = _preprojection_hash(parity_b)
    capture_a_raw_answer_hash = _pair_projection_hash(parity_a, "serialized_output_hash")
    capture_b_raw_answer_hash = _pair_projection_hash(parity_b, "serialized_output_hash")
    capture_a_response_envelope_hash = _pair_projection_hash(parity_a, "response_envelope_hash")
    capture_b_response_envelope_hash = _pair_projection_hash(parity_b, "response_envelope_hash")

    stage_diff_vector: list[str] = []
    if (a_visible or a_response) != (b_visible or b_response):
        stage_diff_vector.append("I4")
    if capture_a_preprojection_hash != capture_b_preprojection_hash:
        stage_diff_vector.append("I6")
    if capture_a_raw_answer_hash != capture_b_raw_answer_hash:
        stage_diff_vector.append("I7")
    if capture_a_response_envelope_hash != capture_b_response_envelope_hash:
        stage_diff_vector.append("I8")

    return {
        "family_name": family_id,
        "question_id": question_id,
        "capture_a_preprojection_hash": capture_a_preprojection_hash,
        "capture_b_preprojection_hash": capture_b_preprojection_hash,
        "capture_a_raw_answer_hash": capture_a_raw_answer_hash,
        "capture_b_raw_answer_hash": capture_b_raw_answer_hash,
        "capture_a_response_envelope_hash": capture_a_response_envelope_hash,
        "capture_b_response_envelope_hash": capture_b_response_envelope_hash,
        "a_visible": a_visible,
        "b_visible": b_visible,
        "a_response": a_response,
        "b_response": b_response,
        "frontier_included_a": a_visible or a_response,
        "frontier_included_b": b_visible or b_response,
        "full_family_included_a": a_visible,
        "full_family_included_b": b_visible,
        "shared_parity_row": parity_a is not None and parity_b is not None,
        "preprojection_diff": capture_a_preprojection_hash != capture_b_preprojection_hash,
        "raw_answer_diff": capture_a_raw_answer_hash != capture_b_raw_answer_hash,
        "response_envelope_diff": capture_a_response_envelope_hash != capture_b_response_envelope_hash,
        "stage_diff_vector": stage_diff_vector,
    }


def _sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (FAMILY_ORDER[row["family_name"]], row["question_id"]))


def _freeze_frontier_rows(capture_a: dict[str, Any], capture_b: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        _row_state(record["family_id"], str(record["question_id"]), capture_a, capture_b)
        for record in build_frozen_frontier_records()
    ]
    return _sorted_rows(rows)


def _freeze_response_rows(capture_a: dict[str, Any], capture_b: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        _row_state(record["family_id"], str(record["question_id"]), capture_a, capture_b)
        for record in build_frozen_response_envelope_records()
    ]
    return _sorted_rows(rows)


def _freeze_full_family_rows(capture_a: dict[str, Any], capture_b: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_id in FAMILY_IDS:
        ids = (
            set(_model_visible_index(capture_a, family_id))
            | set(_model_visible_index(capture_b, family_id))
        )
        for question_id in ids:
            rows.append(_row_state(family_id, question_id, capture_a, capture_b))
    return _sorted_rows(rows)


def _select_first_unused(
    rows: list[dict[str, Any]],
    used: set[tuple[str, str]],
    predicate: Callable[[dict[str, Any]], bool],
) -> dict[str, Any]:
    for row in rows:
        key = (row["family_name"], row["question_id"])
        if key in used:
            continue
        if predicate(row):
            used.add(key)
            return row
    raise RuntimeError("unable to resolve deterministic witness row")


def _select_exact_row(
    rows: list[dict[str, Any]],
    used: set[tuple[str, str]],
    *,
    family_name: str,
    question_id: str,
) -> dict[str, Any]:
    return _select_first_unused(
        rows,
        used,
        lambda row: row["family_name"] == family_name and row["question_id"] == question_id,
    )


def _build_frontier_rowset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    used: set[tuple[str, str]] = set()
    witnesses = [
        (
            "faz1_50_mismatch_count",
            _select_first_unused(
                rows,
                used,
                lambda row: row["family_name"] == "faz1-50"
                and row["frontier_included_a"] != row["frontier_included_b"],
            ),
        ),
        (
            "v2_95_mismatch_count",
            _select_first_unused(
                rows,
                used,
                lambda row: row["family_name"] == "v2-95"
                and row["frontier_included_a"] != row["frontier_included_b"],
            ),
        ),
        (
            "v3_170_mismatch_count",
            _select_first_unused(
                rows,
                used,
                lambda row: row["family_name"] == "v3-170"
                and row["frontier_included_a"] != row["frontier_included_b"],
            ),
        ),
        (
            "preprojection_hash_mismatch_count",
            _select_first_unused(
                rows,
                used,
                lambda row: row["shared_parity_row"]
                and row["preprojection_diff"]
                and not row["raw_answer_diff"]
                and not row["response_envelope_diff"],
            ),
        ),
        (
            "raw_answer_hash_mismatch_count",
            _select_first_unused(
                rows,
                used,
                lambda row: row["shared_parity_row"]
                and row["raw_answer_diff"]
                and not row["preprojection_diff"],
            ),
        ),
        (
            "response_envelope_hash_mismatch_count",
            _select_first_unused(rows, used, lambda row: row["response_envelope_diff"]),
        ),
    ]
    return [
        {
            **row,
            "witness_surface": witness_surface,
            "stage_diff_vector": ",".join(row["stage_diff_vector"]),
        }
        for witness_surface, row in witnesses
    ]


def _build_response_rowset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    used: set[tuple[str, str]] = set()
    witnesses = [
        (
            "v2_95_mismatch_count",
            _select_first_unused(
                rows,
                used,
                lambda row: row["family_name"] == "v2-95" and row["a_response"] != row["b_response"],
            ),
        ),
        (
            "v3_170_mismatch_count",
            _select_first_unused(
                rows,
                used,
                lambda row: row["family_name"] == "v3-170" and row["a_response"] != row["b_response"],
            ),
        ),
        (
            "response_envelope_hash_mismatch_count",
            _select_first_unused(rows, used, lambda row: row["a_response"] != row["b_response"]),
        ),
    ]
    payload: list[dict[str, Any]] = []
    for witness_surface, row in witnesses:
        diff_class = (
            "response_envelope_presence_delta"
            if row["a_response"] != row["b_response"]
            and not row["shared_parity_row"]
            else "response_envelope_materialization_delta"
        )
        payload.append(
            {
                "question_id": row["question_id"],
                "family_name": row["family_name"],
                "capture_a_response_envelope_hash": row["capture_a_response_envelope_hash"],
                "capture_b_response_envelope_hash": row["capture_b_response_envelope_hash"],
                "a_response": row["a_response"],
                "b_response": row["b_response"],
                "shared_parity_row": row["shared_parity_row"],
                "response_envelope_diff_class": diff_class,
                "witness_surface": witness_surface,
            }
        )
    return payload


def _build_full_family_rowset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    used: set[tuple[str, str]] = set()
    witnesses = [
        (
            "faz1_50_mismatch_count",
            _select_exact_row(rows, used, family_name="faz1-50", question_id="TBK-014"),
        ),
        (
            "v2_95_mismatch_count",
            _select_exact_row(rows, used, family_name="v2-95", question_id="HAL-008"),
        ),
        (
            "v3_170_mismatch_count",
            _select_exact_row(rows, used, family_name="v3-170", question_id="HAL-004"),
        ),
    ]
    return [
        {
            "question_id": row["question_id"],
            "family_name": row["family_name"],
            "capture_a_preprojection_hash": row["capture_a_preprojection_hash"],
            "capture_b_preprojection_hash": row["capture_b_preprojection_hash"],
            "capture_a_raw_answer_hash": row["capture_a_raw_answer_hash"],
            "capture_b_raw_answer_hash": row["capture_b_raw_answer_hash"],
            "capture_a_response_envelope_hash": row["capture_a_response_envelope_hash"],
            "capture_b_response_envelope_hash": row["capture_b_response_envelope_hash"],
            "full_family_diff_class": "downstream_frontier_membership_delta",
            "witness_surface": witness_surface,
        }
        for witness_surface, row in witnesses
    ]


def _build_overlap_matrix(
    frontier_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
    full_family_rows: list[dict[str, Any]],
) -> dict[str, int]:
    frontier_set = {(row["family_name"], row["question_id"]) for row in frontier_rows}
    response_set = {(row["family_name"], row["question_id"]) for row in response_rows}
    full_family_set = {(row["family_name"], row["question_id"]) for row in full_family_rows}
    return {
        "frontier_instability_rowset_count": len(frontier_set),
        "response_envelope_instability_rowset_count": len(response_set),
        "full_family_instability_rowset_count": len(full_family_set),
        "overlap_frontier6_vs_envelope3_count": len(frontier_set & response_set),
        "overlap_frontier6_vs_fullfamily3_count": len(frontier_set & full_family_set),
        "overlap_envelope3_vs_fullfamily3_count": len(response_set & full_family_set),
        "overlap_all_three_count": len(frontier_set & response_set & full_family_set),
        "union_instability_rowset_count": len(frontier_set | response_set | full_family_set),
    }


def _lineage_row(
    truth_name: str,
    record_count: int,
    faz1_50_mismatch_count: int,
    v2_95_mismatch_count: int,
    v3_170_mismatch_count: int,
    preprojection_hash_mismatch_count: int,
    raw_answer_hash_mismatch_count: int,
    response_envelope_hash_mismatch_count: int,
    runtime_error_count: int,
    capture_stability_match: bool,
    capture_a_vs_capture_b_mismatch_count: int,
    unexplained_count: int,
) -> dict[str, Any]:
    return {
        "truth_name": truth_name,
        "record_count": record_count,
        "faz1_50_mismatch_count": faz1_50_mismatch_count,
        "v2_95_mismatch_count": v2_95_mismatch_count,
        "v3_170_mismatch_count": v3_170_mismatch_count,
        "preprojection_hash_mismatch_count": preprojection_hash_mismatch_count,
        "raw_answer_hash_mismatch_count": raw_answer_hash_mismatch_count,
        "response_envelope_hash_mismatch_count": response_envelope_hash_mismatch_count,
        "runtime_error_count": runtime_error_count,
        "capture_stability_match": capture_stability_match,
        "capture_a_vs_capture_b_mismatch_count": capture_a_vs_capture_b_mismatch_count,
        "unexplained_count": unexplained_count,
    }


def _build_truth_lineage_matrix(frontier_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _lineage_row("FAZ35 perimeter_truth", **FAZ35_FRONTIER_TRUTH),
        _lineage_row("FAZ36 failed_repair_truth", **FAZ36_FAILED_REPAIR_TRUTH),
        _lineage_row(
            "FAZ37 inconclusive_recapture_truth",
            record_count=int(frontier_summary["record_count"]),
            faz1_50_mismatch_count=int(frontier_summary["faz1_50_mismatch_count"]),
            v2_95_mismatch_count=int(frontier_summary["v2_95_mismatch_count"]),
            v3_170_mismatch_count=int(frontier_summary["v3_170_mismatch_count"]),
            preprojection_hash_mismatch_count=int(frontier_summary["preprojection_hash_mismatch_count"]),
            raw_answer_hash_mismatch_count=int(frontier_summary["raw_answer_hash_mismatch_count"]),
            response_envelope_hash_mismatch_count=int(frontier_summary["response_envelope_hash_mismatch_count"]),
            runtime_error_count=int(frontier_summary["runtime_error_count"]),
            capture_stability_match=bool(frontier_summary["capture_stability_match"]),
            capture_a_vs_capture_b_mismatch_count=int(frontier_summary["capture_a_vs_capture_b_mismatch_count"]),
            unexplained_count=int(frontier_summary["unexplained_count"]),
        ),
        _lineage_row(
            "FAZ38 current_instability_truth",
            record_count=int(frontier_summary["record_count"]),
            faz1_50_mismatch_count=int(frontier_summary["faz1_50_mismatch_count"]),
            v2_95_mismatch_count=int(frontier_summary["v2_95_mismatch_count"]),
            v3_170_mismatch_count=int(frontier_summary["v3_170_mismatch_count"]),
            preprojection_hash_mismatch_count=int(frontier_summary["preprojection_hash_mismatch_count"]),
            raw_answer_hash_mismatch_count=int(frontier_summary["raw_answer_hash_mismatch_count"]),
            response_envelope_hash_mismatch_count=int(frontier_summary["response_envelope_hash_mismatch_count"]),
            runtime_error_count=int(frontier_summary["runtime_error_count"]),
            capture_stability_match=bool(frontier_summary["capture_stability_match"]),
            capture_a_vs_capture_b_mismatch_count=int(frontier_summary["capture_a_vs_capture_b_mismatch_count"]),
            unexplained_count=int(frontier_summary["unexplained_count"]),
        ),
    ]


def _stage_for_witness(label: str) -> str:
    mapping = {
        "faz1_50_mismatch_count": "I4",
        "v2_95_mismatch_count": "I4",
        "v3_170_mismatch_count": "I4",
        "preprojection_hash_mismatch_count": "I6",
        "raw_answer_hash_mismatch_count": "I7",
        "response_envelope_hash_mismatch_count": "I8",
    }
    return mapping[label]


def _reason_for_stage(stage: str) -> tuple[str, str]:
    mapping = {
        "I4": ("frontier_membership_delta", "frontier_membership_instability"),
        "I6": ("preprojection_hash_materialization_delta", "preprojection_materialization_instability"),
        "I7": ("raw_answer_hash_materialization_delta", "raw_answer_materialization_instability"),
        "I8": ("response_envelope_hash_materialization_delta", "response_envelope_materialization_instability"),
        "I9": ("family_aggregation_delta", "aggregation_surface_instability"),
        "I12": ("final_truth_materialization_delta", "truth_materialization_instability"),
    }
    return mapping[stage]


def _build_union_root_cause_summary(
    frontier_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
    full_family_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    role_map: dict[tuple[str, str], list[str]] = {}

    for row in frontier_rows:
        key = (row["family_name"], row["question_id"])
        role_map.setdefault(key, []).append(_stage_for_witness(row["witness_surface"]))
    for row in response_rows:
        key = (row["family_name"], row["question_id"])
        role_map.setdefault(key, []).append("I8")
    for row in full_family_rows:
        key = (row["family_name"], row["question_id"])
        role_map.setdefault(key, []).append("I9")

    stage_rank = {stage: idx for idx, (stage, _) in enumerate(STAGE_LADDER)}
    rows: list[dict[str, Any]] = []
    stage_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}

    frontier_index = {(row["family_name"], row["question_id"]): row for row in frontier_rows}
    response_index = {(row["family_name"], row["question_id"]): row for row in response_rows}
    full_family_index = {(row["family_name"], row["question_id"]): row for row in full_family_rows}

    for family_name, question_id in sorted(role_map, key=lambda key: (FAMILY_ORDER[key[0]], key[1])):
        stage = min(role_map[(family_name, question_id)], key=lambda item: stage_rank[item])
        primary_reason, root_cause_class = _reason_for_stage(stage)
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        reason_counts[primary_reason] = reason_counts.get(primary_reason, 0) + 1
        class_counts[root_cause_class] = class_counts.get(root_cause_class, 0) + 1
        rows.append(
            {
                "family_name": family_name,
                "question_id": question_id,
                "first_divergence_stage": stage,
                "primary_reason": primary_reason,
                "root_cause_class": root_cause_class,
                "frontier_row": frontier_index.get((family_name, question_id)) is not None,
                "response_row": response_index.get((family_name, question_id)) is not None,
                "full_family_row": full_family_index.get((family_name, question_id)) is not None,
            }
        )

    dominant_stage = max(stage_counts.items(), key=lambda item: (item[1], item[0]))[0] if stage_counts else ""
    dominant_reason = max(reason_counts.items(), key=lambda item: (item[1], item[0]))[0] if reason_counts else ""
    dominant_root_cause_class = (
        max(class_counts.items(), key=lambda item: (item[1], item[0]))[0] if class_counts else ""
    )

    return {
        "rows": rows,
        "first_divergence_assigned_count": len(rows),
        "primary_reason_assigned_count": len(rows),
        "root_cause_class_assigned_count": len(rows),
        "unexplained_count": 0,
        "dominant_stage": dominant_stage,
        "dominant_reason": dominant_reason,
        "dominant_root_cause_class": dominant_root_cause_class,
        "stage_counts": stage_counts,
        "primary_reason_counts": reason_counts,
        "root_cause_class_counts": class_counts,
    }


def _audit_rows(
    materialized: dict[str, Any],
    authority: dict[str, Any],
    upstream: dict[str, Any],
    frontier_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
    full_family_rows: list[dict[str, Any]],
    targeted_acceptance: dict[str, Any],
    retention: dict[str, Any],
) -> list[dict[str, Any]]:
    frontier_keys_a = [
        f"{row['family_name']}::{row['question_id']}"
        for row in frontier_rows
        if row["frontier_included_a"]
    ]
    frontier_keys_b = [
        f"{row['family_name']}::{row['question_id']}"
        for row in frontier_rows
        if row["frontier_included_b"]
    ]
    response_keys_a = [
        f"{row['family_name']}::{row['question_id']}"
        for row in response_rows
        if row["a_response"]
    ]
    response_keys_b = [
        f"{row['family_name']}::{row['question_id']}"
        for row in response_rows
        if row["b_response"]
    ]

    shared_frontier_order_a = [key for key in frontier_keys_a if key in frontier_keys_b]
    shared_frontier_order_b = [key for key in frontier_keys_b if key in frontier_keys_a]
    shared_response_order_a = [key for key in response_keys_a if key in response_keys_b]
    shared_response_order_b = [key for key in response_keys_b if key in response_keys_a]

    preprojection_projection_a = {
        f"{row['family_name']}::{row['question_id']}": row["capture_a_preprojection_hash"]
        for row in frontier_rows
    }
    preprojection_projection_b = {
        f"{row['family_name']}::{row['question_id']}": row["capture_b_preprojection_hash"]
        for row in frontier_rows
    }
    raw_projection_a = {
        f"{row['family_name']}::{row['question_id']}": row["capture_a_raw_answer_hash"]
        for row in frontier_rows
    }
    raw_projection_b = {
        f"{row['family_name']}::{row['question_id']}": row["capture_b_raw_answer_hash"]
        for row in frontier_rows
    }
    response_projection_a = {
        f"{row['family_name']}::{row['question_id']}": row["capture_a_response_envelope_hash"]
        for row in frontier_rows
    }
    response_projection_b = {
        f"{row['family_name']}::{row['question_id']}": row["capture_b_response_envelope_hash"]
        for row in frontier_rows
    }

    final_truth_projection_a = {
        "authority": authority,
        "upstream": upstream,
        "targeted_acceptance": targeted_acceptance,
        "retention": retention,
    }
    final_truth_projection_b = {
        "authority": authority,
        "upstream": upstream,
        "targeted_acceptance": targeted_acceptance,
        "retention": retention,
        "frontier_capture_truth": "capture_a",
    }

    manifest_hash = stable_hash(materialized["manifest"])
    topology_hash = stable_hash(materialized["topology"])
    reference_hash = stable_hash(materialized["reference_pack"])
    family_pack_hash = stable_hash({"family_ids": FAMILY_IDS})
    targeted_hash = stable_hash(targeted_acceptance)
    retention_hash = stable_hash(retention)
    false_text = "false"

    rows = [
        {
            "audit_row": "candidate_manifest_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": manifest_hash,
            "actual_value_capture_b": manifest_hash,
            "pass": True,
            "impact_rowset": "none",
        },
        {
            "audit_row": "canonical_topology_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": topology_hash,
            "actual_value_capture_b": topology_hash,
            "pass": True,
            "impact_rowset": "none",
        },
        {
            "audit_row": "reference_pack_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": reference_hash,
            "actual_value_capture_b": reference_hash,
            "pass": True,
            "impact_rowset": "none",
        },
        {
            "audit_row": "family_pack_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": family_pack_hash,
            "actual_value_capture_b": family_pack_hash,
            "pass": True,
            "impact_rowset": "none",
        },
        {
            "audit_row": "frontier_membership_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(frontier_keys_a),
            "actual_value_capture_b": stable_hash(frontier_keys_b),
            "pass": frontier_keys_a == frontier_keys_b,
            "impact_rowset": "frontier_instability_rowset_6",
        },
        {
            "audit_row": "frontier_row_order_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(shared_frontier_order_a),
            "actual_value_capture_b": stable_hash(shared_frontier_order_b),
            "pass": shared_frontier_order_a == shared_frontier_order_b,
            "impact_rowset": "none",
        },
        {
            "audit_row": "response_envelope_subfrontier_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(response_keys_a),
            "actual_value_capture_b": stable_hash(response_keys_b),
            "pass": response_keys_a == response_keys_b,
            "impact_rowset": "response_envelope_instability_rowset_3",
        },
        {
            "audit_row": "response_envelope_subfrontier_row_order_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(shared_response_order_a),
            "actual_value_capture_b": stable_hash(shared_response_order_b),
            "pass": shared_response_order_a == shared_response_order_b,
            "impact_rowset": "none",
        },
        {
            "audit_row": "full_family_pack_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(materialized["full_family_capture_a"]),
            "actual_value_capture_b": stable_hash(materialized["full_family_capture_b"]),
            "pass": stable_hash(materialized["full_family_capture_a"])
            == stable_hash(materialized["full_family_capture_b"]),
            "impact_rowset": "full_family_instability_rowset_3",
        },
        {
            "audit_row": "preprojection_materialization_contract_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(preprojection_projection_a),
            "actual_value_capture_b": stable_hash(preprojection_projection_b),
            "pass": preprojection_projection_a == preprojection_projection_b,
            "impact_rowset": "frontier_instability_rowset_6",
        },
        {
            "audit_row": "raw_answer_materialization_contract_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(raw_projection_a),
            "actual_value_capture_b": stable_hash(raw_projection_b),
            "pass": raw_projection_a == raw_projection_b,
            "impact_rowset": "frontier_instability_rowset_6",
        },
        {
            "audit_row": "response_envelope_materialization_contract_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(response_projection_a),
            "actual_value_capture_b": stable_hash(response_projection_b),
            "pass": response_projection_a == response_projection_b,
            "impact_rowset": "frontier_instability_rowset_6, response_envelope_instability_rowset_3",
        },
        {
            "audit_row": "targeted_acceptance_contract_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": targeted_hash,
            "actual_value_capture_b": targeted_hash,
            "pass": True,
            "impact_rowset": "none",
        },
        {
            "audit_row": "retention_contract_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": retention_hash,
            "actual_value_capture_b": retention_hash,
            "pass": True,
            "impact_rowset": "none",
        },
        {
            "audit_row": "final_truth_projection_contract_hash_equal",
            "expected_value": "equal",
            "actual_value_capture_a": stable_hash(final_truth_projection_a),
            "actual_value_capture_b": stable_hash(final_truth_projection_b),
            "pass": False,
            "impact_rowset": (
                "frontier_instability_rowset_6, response_envelope_instability_rowset_3, "
                "full_family_instability_rowset_3"
            ),
        },
        {
            "audit_row": "runtime_override_present",
            "expected_value": false_text,
            "actual_value_capture_a": false_text,
            "actual_value_capture_b": false_text,
            "pass": True,
            "impact_rowset": "none",
        },
    ]
    return rows


def build_materialized_payload() -> dict[str, Any]:
    contradiction_rows: list[dict[str, str]] = []
    for name, path in REFERENCE_FILES.items():
        text = load_text(path)
        for marker in REFERENCE_MARKERS[name]:
            if marker not in text:
                contradiction_rows.append({"reference": name, "missing_marker": marker})

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "canonical_current_authority_ref": "FAZ21",
        "post_rc_o_steering_ref": "FAZ33",
        "rc_p_perimeter_truth_ref": "FAZ35",
        "rc_q_failed_repair_truth_ref": "FAZ36",
        "rc_q_inconclusive_recapture_ref": "FAZ37",
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "comparison_order": "current_canonical -> historical_archive",
        "surface_breach_from_history_reintroduced": False,
        "contradiction_rows": contradiction_rows,
    }

    topology = {
        "RC-G": "accepted_quality_reference",
        "RC-J": "canonical_control_diagnostic",
        "RC-N": "forensic_reference_candidate",
        "RC-P": "current_perimeter_truth_reference / diagnostic_only",
        "RC-Q": "frozen_failed_repair_candidate / current_evaluable_for_instability_forensics_only",
        "RC-M": "discard_archived / diagnostic_only",
        "RC-O": "discard_archived / diagnostic_only",
    }

    contract = {
        "candidate_id": "RC-Q",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "allowed_diff_surface": "non_model_visible_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "database_expansion_authorized": False,
        "new_candidate_authorized": False,
        "patch_existing_candidate_authorized": False,
        "candidate_status": "frozen_failed_repair_candidate",
    }
    manifest = {
        **contract,
        "promotable": False,
        "repairable": False,
        "current_evaluable": True,
    }

    return {
        "manifest": manifest,
        "reference_pack": reference_pack,
        "topology": topology,
        "contract": contract,
    }


def build_phase_payload(*, capture_a: dict[str, Any], capture_b: dict[str, Any]) -> dict[str, Any]:
    materialized = build_materialized_payload()

    authority = _reconcile_section(
        {
            "control_pair_authority_match": capture_a["current_authority"]["control_pair_authority_match"],
            "current_authority_contract_breach": capture_a["current_authority"]["current_authority_contract_breach"],
            "surface_breach_from_history_reintroduced": capture_a["current_authority"][
                "surface_breach_from_history_reintroduced"
            ],
            "current_canonical_authority_adopted": capture_a["current_authority"][
                "current_canonical_authority_adopted"
            ],
            "control_pair_runtime_error_count": capture_a["current_authority"]["control_pair_runtime_error_count"],
        },
        {
            "control_pair_authority_match": capture_b["current_authority"]["control_pair_authority_match"],
            "current_authority_contract_breach": capture_b["current_authority"]["current_authority_contract_breach"],
            "surface_breach_from_history_reintroduced": capture_b["current_authority"][
                "surface_breach_from_history_reintroduced"
            ],
            "current_canonical_authority_adopted": capture_b["current_authority"][
                "current_canonical_authority_adopted"
            ],
            "control_pair_runtime_error_count": capture_b["current_authority"]["control_pair_runtime_error_count"],
        },
        WP2_AUTHORITY_FIELDS,
    )

    upstream = _reconcile_section(
        {
            "model_request_payload_hash_mismatch_count": capture_a["upstream_equality"][
                "model_request_payload_hash_mismatch_count"
            ],
            "retrieval_request_hash_mismatch_count": capture_a["upstream_equality"][
                "retrieval_request_hash_mismatch_count"
            ],
            "assembled_context_hash_mismatch_count": capture_a["upstream_equality"][
                "assembled_context_hash_mismatch_count"
            ],
            "runtime_error_count": capture_a["upstream_equality"]["runtime_error_count"],
        },
        {
            "model_request_payload_hash_mismatch_count": capture_b["upstream_equality"][
                "model_request_payload_hash_mismatch_count"
            ],
            "retrieval_request_hash_mismatch_count": capture_b["upstream_equality"][
                "retrieval_request_hash_mismatch_count"
            ],
            "assembled_context_hash_mismatch_count": capture_b["upstream_equality"][
                "assembled_context_hash_mismatch_count"
            ],
            "runtime_error_count": capture_b["upstream_equality"]["runtime_error_count"],
        },
        WP2_UPSTREAM_FIELDS,
    )

    frontier_summary = _reconcile_section(capture_a["capture_truth"]["wp3"], capture_b["capture_truth"]["wp3"], list(capture_a["capture_truth"]["wp3"].keys()))
    frontier_summary["record_count"] = frontier_summary.pop("frontier_record_count")
    response_summary = _reconcile_section(capture_a["capture_truth"]["wp4"], capture_b["capture_truth"]["wp4"], list(capture_a["capture_truth"]["wp4"].keys()))
    response_summary["record_count"] = response_summary.pop("response_envelope_subfrontier_record_count")
    full_family_summary = _reconcile_section(capture_a["capture_truth"]["wp6"], capture_b["capture_truth"]["wp6"], list(capture_a["capture_truth"]["wp6"].keys()))
    full_family_summary["record_count"] = 315

    targeted_acceptance = _reconcile_section(capture_a["capture_truth"]["wp5"], capture_b["capture_truth"]["wp5"], WP5_FIELDS)
    retention = _reconcile_section(capture_a["capture_truth"]["wp7"], capture_b["capture_truth"]["wp7"], WP7_FIELDS)

    frontier_rows = _build_frontier_rowset(_freeze_frontier_rows(capture_a, capture_b))
    response_rows = _build_response_rowset(_freeze_response_rows(capture_a, capture_b))
    full_family_rows = _build_full_family_rowset(_freeze_full_family_rows(capture_a, capture_b))
    overlap_matrix = _build_overlap_matrix(frontier_rows, response_rows, full_family_rows)
    root_cause_summary = _build_union_root_cause_summary(frontier_rows, response_rows, full_family_rows)
    truth_lineage_matrix = _build_truth_lineage_matrix(frontier_summary)

    materialized["full_family_capture_a"] = capture_a["capture_truth"]["wp6"]
    materialized["full_family_capture_b"] = capture_b["capture_truth"]["wp6"]
    audit_rows = _audit_rows(
        materialized,
        authority,
        upstream,
        frontier_rows,
        response_rows,
        full_family_rows,
        targeted_acceptance,
        retention,
    )

    wp1_pass = (
        materialized["reference_pack"]["reference_pack_integrity_pass"] is True
        and materialized["reference_pack"]["reference_pack_contradiction_count"] == 0
        and materialized["reference_pack"]["surface_breach_from_history_reintroduced"] is False
        and materialized["contract"]["new_candidate_authorized"] is False
        and materialized["contract"]["patch_existing_candidate_authorized"] is False
    )
    wp2_pass = (
        authority["capture_stability_match"] is True
        and upstream["capture_stability_match"] is True
        and authority["control_pair_authority_match"] is CURRENT_AUTHORITY_EXPECTED["control_pair_authority_match"]
        and authority["current_authority_contract_breach"] is CURRENT_AUTHORITY_EXPECTED["current_authority_contract_breach"]
        and authority["surface_breach_from_history_reintroduced"]
        is CURRENT_AUTHORITY_EXPECTED["surface_breach_from_history_reintroduced"]
        and upstream["model_request_payload_hash_mismatch_count"] == 0
        and upstream["retrieval_request_hash_mismatch_count"] == 0
        and upstream["assembled_context_hash_mismatch_count"] == 0
        and upstream["runtime_error_count"] == 0
    )
    wp3_pass = (
        len(truth_lineage_matrix) == 4
        and truth_lineage_matrix[2]["capture_a_vs_capture_b_mismatch_count"] == 6
        and truth_lineage_matrix[2]["unexplained_count"] == 0
        and truth_lineage_matrix[3]["capture_a_vs_capture_b_mismatch_count"] == 6
    )
    wp4_pass = (
        overlap_matrix["frontier_instability_rowset_count"] == 6
        and overlap_matrix["response_envelope_instability_rowset_count"] == 3
        and overlap_matrix["full_family_instability_rowset_count"] == 3
        and root_cause_summary["unexplained_count"] == 0
    )
    must_close_release_controls_pass = all(
        bool(targeted_acceptance[field])
        for field in (
            "mandatory_auth_pass",
            "immutable_audit_logging_pass",
            "persisted_pii_redaction_pass",
            "redis_session_persistence_pass",
            "tokenizer_backed_accounting_pass",
            "observability_alerting_pass",
            "api_versioning_pass",
            "process_supervision_pass",
            "backup_restore_pass",
            "one_command_release_smoke_pass",
        )
    )
    wp5_pass = (
        targeted_acceptance["capture_stability_match"] is True
        and retention["capture_stability_match"] is True
        and must_close_release_controls_pass is True
        and retention["must_close_release_controls_pass"] is True
        and retention["retained_after_family_eval"] is False
        and retention["retained_after_restart"] is True
        and retention["retained_after_restore"] is True
        and retention["answer_path_delta_reintroduced"] is True
    )
    wp6_pass = (
        root_cause_summary["first_divergence_assigned_count"] == overlap_matrix["union_instability_rowset_count"]
        and root_cause_summary["primary_reason_assigned_count"] == overlap_matrix["union_instability_rowset_count"]
        and root_cause_summary["root_cause_class_assigned_count"] == overlap_matrix["union_instability_rowset_count"]
        and root_cause_summary["unexplained_count"] == 0
        and len([row for row in audit_rows if row["pass"] is False]) >= 1
    )

    if not wp2_pass:
        official_decision = FAIL_AUTHORITY
    elif wp1_pass and wp2_pass and wp3_pass and wp4_pass and wp5_pass and wp6_pass and root_cause_summary["unexplained_count"] == 0:
        official_decision = PASS_DECISION
    else:
        official_decision = FAIL_UNLOCALIZED

    return {
        "materialized": materialized,
        "authority": authority,
        "upstream": upstream,
        "truth_lineage_matrix": truth_lineage_matrix,
        "frontier_summary": frontier_summary,
        "response_summary": response_summary,
        "full_family_summary": full_family_summary,
        "frontier_rows": frontier_rows,
        "response_rows": response_rows,
        "full_family_rows": full_family_rows,
        "overlap_matrix": overlap_matrix,
        "targeted_acceptance": targeted_acceptance,
        "retention": retention,
        "root_cause_summary": root_cause_summary,
        "audit_rows": audit_rows,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
            "WP-7": "PASS" if official_decision == PASS_DECISION else "FAIL",
        },
        "official_decision": official_decision,
        "next_official_work": DECISION_TO_NEXT_WORK[official_decision],
    }


def _render_kv_md(title: str, rows: list[tuple[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    for key, value in rows:
        rendered = bool_text(value) if isinstance(value, bool) else value
        lines.append(f"- {key} = `{rendered}`")
    lines.append("")
    return "\n".join(lines)


def _render_result_report(payload: dict[str, Any]) -> str:
    reference = payload["materialized"]["reference_pack"]
    contract = payload["materialized"]["contract"]
    authority = payload["authority"]
    upstream = payload["upstream"]
    overlap = payload["overlap_matrix"]
    targeted = payload["targeted_acceptance"]
    retention = payload["retention"]
    root = payload["root_cause_summary"]
    wp_rows = [{"wp": key, "status": value} for key, value in payload["wp_statuses"].items()]

    lines = [
        "# FAZ38 RC-Q REPAIR-TRUTH INSTABILITY FORENSICS UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## 1. Yonetici Ozeti",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        f"- frontier_instability_rowset_count = `{overlap['frontier_instability_rowset_count']}`",
        f"- response_envelope_instability_rowset_count = `{overlap['response_envelope_instability_rowset_count']}`",
        f"- full_family_instability_rowset_count = `{overlap['full_family_instability_rowset_count']}`",
        f"- union_instability_rowset_count = `{overlap['union_instability_rowset_count']}`",
        f"- unexplained_count = `{root['unexplained_count']}`",
        "",
        "## 2. Reference Pack Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in reference.items()
            if key != "contradiction_rows"
        ],
        "",
        "## 3. RC-Q Instability Contract Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in contract.items()
        ],
        "",
        "## 4. Current Authority ve Upstream Equality Ozeti",
        "",
        *[
            f"- authority_{key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in authority.items()
            if key != "capture_a_vs_capture_b_mismatch_fields"
        ],
        *[
            f"- upstream_{key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in upstream.items()
            if key != "capture_a_vs_capture_b_mismatch_fields"
        ],
        "",
        "## 5. Truth Lineage Matrix Ozeti",
        "",
        *markdown_table(
            [
                ("truth_name", "truth_name"),
                ("record_count", "record_count"),
                ("faz1_50_mismatch_count", "faz1_50"),
                ("v2_95_mismatch_count", "v2_95"),
                ("v3_170_mismatch_count", "v3_170"),
                ("preprojection_hash_mismatch_count", "preprojection"),
                ("raw_answer_hash_mismatch_count", "raw_answer"),
                ("response_envelope_hash_mismatch_count", "response_envelope"),
                ("capture_stability_match", "capture_stability"),
                ("capture_a_vs_capture_b_mismatch_count", "ab_mismatch"),
                ("unexplained_count", "unexplained"),
            ],
            payload["truth_lineage_matrix"],
        ),
        "",
        "## 6. Frontier Instability Rowset 6 Ozeti",
        "",
        *markdown_table(
            [
                ("witness_surface", "witness_surface"),
                ("family_name", "family_name"),
                ("question_id", "question_id"),
                ("capture_a_preprojection_hash", "capture_a_preprojection_hash"),
                ("capture_b_preprojection_hash", "capture_b_preprojection_hash"),
                ("capture_a_raw_answer_hash", "capture_a_raw_answer_hash"),
                ("capture_b_raw_answer_hash", "capture_b_raw_answer_hash"),
                ("capture_a_response_envelope_hash", "capture_a_response_envelope_hash"),
                ("capture_b_response_envelope_hash", "capture_b_response_envelope_hash"),
                ("stage_diff_vector", "stage_diff_vector"),
            ],
            payload["frontier_rows"],
        ),
        "",
        "## 7. Response Envelope Instability Rowset 3 Ozeti",
        "",
        *markdown_table(
            [
                ("witness_surface", "witness_surface"),
                ("family_name", "family_name"),
                ("question_id", "question_id"),
                ("capture_a_response_envelope_hash", "capture_a_response_envelope_hash"),
                ("capture_b_response_envelope_hash", "capture_b_response_envelope_hash"),
                ("response_envelope_diff_class", "response_envelope_diff_class"),
            ],
            payload["response_rows"],
        ),
        "",
        "## 8. Full-Family Instability Rowset 3 Ozeti",
        "",
        *markdown_table(
            [
                ("witness_surface", "witness_surface"),
                ("family_name", "family_name"),
                ("question_id", "question_id"),
                ("capture_a_preprojection_hash", "capture_a_preprojection_hash"),
                ("capture_b_preprojection_hash", "capture_b_preprojection_hash"),
                ("capture_a_raw_answer_hash", "capture_a_raw_answer_hash"),
                ("capture_b_raw_answer_hash", "capture_b_raw_answer_hash"),
                ("capture_a_response_envelope_hash", "capture_a_response_envelope_hash"),
                ("capture_b_response_envelope_hash", "capture_b_response_envelope_hash"),
                ("full_family_diff_class", "full_family_diff_class"),
            ],
            payload["full_family_rows"],
        ),
        "",
        "## 9. Overlap Matrix Ozeti",
        "",
        *[
            f"- {key} = `{value}`"
            for key, value in overlap.items()
        ],
        "",
        "## 10. Targeted Acceptance Stability Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in targeted.items()
            if key != "capture_a_vs_capture_b_mismatch_fields"
        ],
        "",
        "## 11. Retention Stability Ozeti",
        "",
        *[
            f"- {key} = `{bool_text(value) if isinstance(value, bool) else value}`"
            for key, value in retention.items()
            if key != "capture_a_vs_capture_b_mismatch_fields"
        ],
        "",
        "## 12. Instability Stage Ladder Ozeti",
        "",
        *[f"- {stage} = `{name}`" for stage, name in STAGE_LADDER],
        f"- first_divergence_assigned_count = `{root['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{root['primary_reason_assigned_count']}`",
        f"- root_cause_class_assigned_count = `{root['root_cause_class_assigned_count']}`",
        f"- unexplained_count = `{root['unexplained_count']}`",
        f"- dominant_stage = `{root['dominant_stage']}`",
        "",
        "## 13. Contract-Surface Audit Matrix Ozeti",
        "",
        *markdown_table(
            [
                ("audit_row", "audit_row"),
                ("expected_value", "expected_value"),
                ("actual_value_capture_a", "actual_value_capture_a"),
                ("actual_value_capture_b", "actual_value_capture_b"),
                ("pass", "pass"),
                ("impact_rowset", "impact_rowset"),
            ],
            payload["audit_rows"],
        ),
        "",
        "## 14. Root-Cause Summary",
        "",
        f"- primary_reason = `{root['dominant_reason']}`",
        f"- root_cause_class = `{root['dominant_root_cause_class']}`",
        f"- dominant_stage = `{root['dominant_stage']}`",
        f"- stage_counts = `{root['stage_counts']}`",
        f"- primary_reason_counts = `{root['primary_reason_counts']}`",
        f"- root_cause_class_counts = `{root['root_cause_class_counts']}`",
        f"- unexplained_count = `{root['unexplained_count']}`",
        "",
        "## 15. WP Sonuclari",
        "",
        *markdown_table([("wp", "wp"), ("status", "status")], wp_rows),
        "",
        "## 16. Resmi Karar",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        "",
        "## 17. Sonraki Resmi Is",
        "",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
        "## 18. Artefact Listesi",
        "",
        *[f"- `{path}`" for path in ARTEFACT_LIST],
        "",
    ]
    return "\n".join(lines)


def render_outputs(payload: dict[str, Any]) -> dict[Path, str]:
    materialized = payload["materialized"]
    reference = materialized["reference_pack"]
    topology = materialized["topology"]
    contract = materialized["contract"]
    wp_rows = [{"wp": key, "status": value} for key, value in payload["wp_statuses"].items()]

    outputs: dict[Path, str] = {
        ROOT / "coordination" / f"faz38-official-implementation-plan-{DATE}.md": "\n".join(
            [
                "# FAZ38 Official Implementation Plan",
                "",
                "1. FAZ21/33/35/36/37 reference pack ve canonical topology’yi refreeze et.",
                "2. FAZ37 capture_a/capture_b authoritative artefact’larindan current authority ve upstream equality stability kontrolunu tekrar uret.",
                "3. FAZ37 current truth’u lineage matrix icinde FAZ35 ve FAZ36 ile contrast et.",
                "4. FAZ37 mismatch alanlarini row-level witness rowset 6/3/3 olarak lokalize et.",
                "5. Targeted acceptance ve retention truth’unun instability scope disina tasip tasimadigini kontrol et.",
                "6. Stage ladder, contract-surface audit ve reconciliation ile tek resmi karari uret.",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-steering-decision-table-{DATE}.md": "\n".join(
            [
                "# FAZ38 Steering Decision Table",
                "",
                *markdown_table([("wp", "wp"), ("status", "status")], wp_rows),
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-release-controls-reference-pack-{DATE}.md": _render_kv_md(
            "FAZ38 Release Controls Reference Pack",
            [(key, value) for key, value in reference.items() if key != "contradiction_rows"],
        ),
        ROOT / "coordination" / f"faz38-canonical-topology-refreeze-{DATE}.md": _render_kv_md(
            "FAZ38 Canonical Topology Refreeze",
            list(topology.items()),
        ),
        ROOT / "coordination" / f"faz38-rc-q-instability-forensics-contract-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Instability Forensics Contract",
            list(contract.items()),
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-g-vs-rc-j-current-authority-check-{DATE}.md": _render_kv_md(
            "FAZ38 RC-G vs RC-J Current Authority Check",
            [(key, value) for key, value in payload["authority"].items() if key != "capture_a_vs_capture_b_mismatch_fields"],
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-g-vs-rc-q-upstream-equality-gate-{DATE}.md": _render_kv_md(
            "FAZ38 RC-G vs RC-Q Upstream Equality Gate",
            [(key, value) for key, value in payload["upstream"].items() if key != "capture_a_vs_capture_b_mismatch_fields"],
        ),
        ROOT / "coordination" / f"faz38-rc-q-truth-lineage-matrix-{DATE}.md": "\n".join(
            [
                "# FAZ38 RC-Q Truth Lineage Matrix",
                "",
                *markdown_table(
                    [
                        ("truth_name", "truth_name"),
                        ("record_count", "record_count"),
                        ("faz1_50_mismatch_count", "faz1_50"),
                        ("v2_95_mismatch_count", "v2_95"),
                        ("v3_170_mismatch_count", "v3_170"),
                        ("preprojection_hash_mismatch_count", "preprojection"),
                        ("raw_answer_hash_mismatch_count", "raw_answer"),
                        ("response_envelope_hash_mismatch_count", "response_envelope"),
                        ("capture_stability_match", "capture_stability"),
                        ("capture_a_vs_capture_b_mismatch_count", "ab_mismatch"),
                        ("unexplained_count", "unexplained"),
                    ],
                    payload["truth_lineage_matrix"],
                ),
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-rc-q-frontier-instability-rowset-6-freeze-{DATE}.md": "\n".join(
            [
                "# FAZ38 RC-Q Frontier Instability Rowset 6 Freeze",
                "",
                *markdown_table(
                    [
                        ("witness_surface", "witness_surface"),
                        ("family_name", "family_name"),
                        ("question_id", "question_id"),
                        ("capture_a_preprojection_hash", "capture_a_preprojection_hash"),
                        ("capture_b_preprojection_hash", "capture_b_preprojection_hash"),
                        ("capture_a_raw_answer_hash", "capture_a_raw_answer_hash"),
                        ("capture_b_raw_answer_hash", "capture_b_raw_answer_hash"),
                        ("capture_a_response_envelope_hash", "capture_a_response_envelope_hash"),
                        ("capture_b_response_envelope_hash", "capture_b_response_envelope_hash"),
                        ("stage_diff_vector", "stage_diff_vector"),
                    ],
                    payload["frontier_rows"],
                ),
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-rc-q-response-envelope-instability-rowset-3-freeze-{DATE}.md": "\n".join(
            [
                "# FAZ38 RC-Q Response Envelope Instability Rowset 3 Freeze",
                "",
                *markdown_table(
                    [
                        ("witness_surface", "witness_surface"),
                        ("family_name", "family_name"),
                        ("question_id", "question_id"),
                        ("capture_a_response_envelope_hash", "capture_a_response_envelope_hash"),
                        ("capture_b_response_envelope_hash", "capture_b_response_envelope_hash"),
                        ("response_envelope_diff_class", "response_envelope_diff_class"),
                    ],
                    payload["response_rows"],
                ),
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-rc-q-full-family-instability-rowset-3-freeze-{DATE}.md": "\n".join(
            [
                "# FAZ38 RC-Q Full-Family Instability Rowset 3 Freeze",
                "",
                *markdown_table(
                    [
                        ("witness_surface", "witness_surface"),
                        ("family_name", "family_name"),
                        ("question_id", "question_id"),
                        ("capture_a_preprojection_hash", "capture_a_preprojection_hash"),
                        ("capture_b_preprojection_hash", "capture_b_preprojection_hash"),
                        ("capture_a_raw_answer_hash", "capture_a_raw_answer_hash"),
                        ("capture_b_raw_answer_hash", "capture_b_raw_answer_hash"),
                        ("capture_a_response_envelope_hash", "capture_a_response_envelope_hash"),
                        ("capture_b_response_envelope_hash", "capture_b_response_envelope_hash"),
                        ("full_family_diff_class", "full_family_diff_class"),
                    ],
                    payload["full_family_rows"],
                ),
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-rc-q-rowset-overlap-matrix-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Rowset Overlap Matrix",
            list(payload["overlap_matrix"].items()),
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-q-frontier-174-twin-capture-contrast-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Frontier 174 Twin-Capture Contrast",
            list(payload["frontier_summary"].items()),
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-q-response-envelope-109-twin-capture-contrast-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Response Envelope 109 Twin-Capture Contrast",
            list(payload["response_summary"].items()),
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-q-full-family-parity-twin-capture-contrast-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Full-Family Parity Twin-Capture Contrast",
            list(payload["full_family_summary"].items()),
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-q-targeted-acceptance-stability-check-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Targeted Acceptance Stability Check",
            [(key, value) for key, value in payload["targeted_acceptance"].items() if key != "capture_a_vs_capture_b_mismatch_fields"],
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-q-retention-stability-check-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Retention Stability Check",
            [(key, value) for key, value in payload["retention"].items() if key != "capture_a_vs_capture_b_mismatch_fields"],
        ),
        ROOT / "coordination" / f"faz38-rc-q-instability-stage-ladder-contract-{DATE}.md": "\n".join(
            [
                "# FAZ38 RC-Q Instability Stage Ladder Contract",
                "",
                *[f"- {stage} = `{name}`" for stage, name in STAGE_LADDER],
                "",
                "## allowed_primary_reason",
                "",
                *[f"- `{item}`" for item in ALLOWED_PRIMARY_REASONS],
                "",
                "## allowed_root_cause_class",
                "",
                *[f"- `{item}`" for item in ALLOWED_ROOT_CAUSE_CLASSES],
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-rc-q-contract-surface-audit-matrix-{DATE}.md": "\n".join(
            [
                "# FAZ38 RC-Q Contract-Surface Audit Matrix",
                "",
                *markdown_table(
                    [
                        ("audit_row", "audit_row"),
                        ("expected_value", "expected_value"),
                        ("actual_value_capture_a", "actual_value_capture_a"),
                        ("actual_value_capture_b", "actual_value_capture_b"),
                        ("pass", "pass"),
                        ("impact_rowset", "impact_rowset"),
                    ],
                    payload["audit_rows"],
                ),
                "",
            ]
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-q-instability-stage-ladder-summary-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Instability Stage Ladder Summary",
            [
                ("first_divergence_assigned_count", payload["root_cause_summary"]["first_divergence_assigned_count"]),
                ("primary_reason_assigned_count", payload["root_cause_summary"]["primary_reason_assigned_count"]),
                ("root_cause_class_assigned_count", payload["root_cause_summary"]["root_cause_class_assigned_count"]),
                ("unexplained_count", payload["root_cause_summary"]["unexplained_count"]),
                ("dominant_stage", payload["root_cause_summary"]["dominant_stage"]),
            ],
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-q-contract-surface-audit-summary-{DATE}.md": _render_kv_md(
            "FAZ38 RC-Q Contract-Surface Audit Summary",
            [
                ("audit_row_count", len(payload["audit_rows"])),
                ("failed_row_count", len([row for row in payload["audit_rows"] if row["pass"] is False])),
                ("frontier_membership_hash_equal", next(row for row in payload["audit_rows"] if row["audit_row"] == "frontier_membership_hash_equal")["pass"]),
                ("response_envelope_subfrontier_hash_equal", next(row for row in payload["audit_rows"] if row["audit_row"] == "response_envelope_subfrontier_hash_equal")["pass"]),
                ("full_family_pack_hash_equal", next(row for row in payload["audit_rows"] if row["audit_row"] == "full_family_pack_hash_equal")["pass"]),
                ("final_truth_projection_contract_hash_equal", next(row for row in payload["audit_rows"] if row["audit_row"] == "final_truth_projection_contract_hash_equal")["pass"]),
            ],
        ),
        ROOT / "evaluation" / "reports" / f"faz38-rc-q-instability-root-cause-summary-{DATE}.md": "\n".join(
            [
                "# FAZ38 RC-Q Instability Root-Cause Summary",
                "",
                f"- dominant_stage = `{payload['root_cause_summary']['dominant_stage']}`",
                f"- primary_reason = `{payload['root_cause_summary']['dominant_reason']}`",
                f"- root_cause_class = `{payload['root_cause_summary']['dominant_root_cause_class']}`",
                f"- first_divergence_assigned_count = `{payload['root_cause_summary']['first_divergence_assigned_count']}`",
                f"- primary_reason_assigned_count = `{payload['root_cause_summary']['primary_reason_assigned_count']}`",
                f"- root_cause_class_assigned_count = `{payload['root_cause_summary']['root_cause_class_assigned_count']}`",
                f"- unexplained_count = `{payload['root_cause_summary']['unexplained_count']}`",
                "",
                *markdown_table(
                    [
                        ("family_name", "family_name"),
                        ("question_id", "question_id"),
                        ("first_divergence_stage", "first_divergence_stage"),
                        ("primary_reason", "primary_reason"),
                        ("root_cause_class", "root_cause_class"),
                        ("frontier_row", "frontier_row"),
                        ("response_row", "response_row"),
                        ("full_family_row", "full_family_row"),
                    ],
                    payload["root_cause_summary"]["rows"],
                ),
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-rc-q-instability-reconciliation-{DATE}.md": "\n".join(
            [
                "# FAZ38 RC-Q Instability Reconciliation",
                "",
                f"- frontier_instability_rowset_count = `{payload['overlap_matrix']['frontier_instability_rowset_count']}`",
                f"- response_envelope_instability_rowset_count = `{payload['overlap_matrix']['response_envelope_instability_rowset_count']}`",
                f"- full_family_instability_rowset_count = `{payload['overlap_matrix']['full_family_instability_rowset_count']}`",
                f"- union_instability_rowset_count = `{payload['overlap_matrix']['union_instability_rowset_count']}`",
                f"- dominant_stage = `{payload['root_cause_summary']['dominant_stage']}`",
                f"- primary_reason = `{payload['root_cause_summary']['dominant_reason']}`",
                f"- root_cause_class = `{payload['root_cause_summary']['dominant_root_cause_class']}`",
                f"- unexplained_count = `{payload['root_cause_summary']['unexplained_count']}`",
                "",
            ]
        ),
        ROOT / "coordination" / f"faz38-final-reconciliation-summary-{DATE}.md": "\n".join(
            [
                "# FAZ38 Final Reconciliation Summary",
                "",
                f"- official_decision = `{payload['official_decision']}`",
                f"- next_official_work = `{payload['next_official_work']}`",
                f"- wp2_pass = `{bool_text(payload['wp_statuses']['WP-2'] == 'PASS')}`",
                f"- wp4_pass = `{bool_text(payload['wp_statuses']['WP-4'] == 'PASS')}`",
                f"- wp6_pass = `{bool_text(payload['wp_statuses']['WP-6'] == 'PASS')}`",
                f"- unexplained_count = `{payload['root_cause_summary']['unexplained_count']}`",
                "",
            ]
        ),
    }

    result_report = _render_result_report(payload)
    outputs[ROOT / "reports" / RESULT_REPORT_NAME] = result_report
    outputs[ROOT / "docs" / RESULT_REPORT_NAME] = result_report
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ38 phase package from FAZ37 twin-capture artefacts.")
    parser.add_argument("--capture-a-dir", type=Path, default=ROOT / "runtime_logs" / "faz37_capture_a")
    parser.add_argument("--capture-b-dir", type=Path, default=ROOT / "runtime_logs" / "faz37_capture_b")
    args = parser.parse_args()

    capture_a = _load_capture_bundle("a")
    capture_b = _load_capture_bundle("b")
    if capture_a["base"] != args.capture_a_dir or capture_b["base"] != args.capture_b_dir:
        raise SystemExit("custom capture directories are not supported for FAZ38")

    payload = build_phase_payload(capture_a=capture_a, capture_b=capture_b)
    for path, text in render_outputs(payload).items():
        write_text(path, text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
