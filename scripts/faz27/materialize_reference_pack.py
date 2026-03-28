#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz27_lib import (  # type: ignore
    BIND_ORDER_ROWS,
    COMPACT_DATE,
    CONTROL_ROWS,
    DATE,
    FAZ26_ARTEFACTS,
    FAZ26_FAMILY_MODEL_VISIBLE_REPORTS,
    FAZ26_RC_G_EVALS,
    FAZ26_RC_N_EVALS,
    FIELD_SPECS,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    build_frontier_records,
    bool_text,
    compare_question_maps,
    load_json,
    load_text,
    markdown_table,
    merge_eval_question_maps,
    render_pair_report_markdown,
    stable_hash,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]


def _family_rows_from_surface_reports() -> list[dict[str, Any]]:
    rows = []
    for family_id in ("faz1-50", "v2-95", "v3-170"):
        report = load_json(FAZ26_FAMILY_MODEL_VISIBLE_REPORTS[family_id])
        row = {
            "family_id": family_id,
            "question_count": int(report["question_count"]),
        }
        for counter_key, _, _ in FIELD_SPECS[:-1]:
            row[counter_key] = int(report.get(counter_key, 0))
        row["first_break_stage_assigned_count"] = int(report.get("first_break_stage_assigned_count", 0))
        row["primary_reason_assigned_count"] = int(report.get("primary_reason_assigned_count", 0))
        row["unexplained_count"] = int(report.get("unexplained_count", 0))
        rows.append(row)
    return rows


def build_materialization_payload() -> dict[str, Any]:
    reference_contradictions: list[dict[str, str]] = []
    reference_texts: dict[str, str] = {}
    for ref_name, path in REFERENCE_FILES.items():
        text = load_text(path)
        reference_texts[ref_name] = text
        for marker in REFERENCE_MARKERS[ref_name]:
            if marker not in text:
                reference_contradictions.append({"reference_name": ref_name, "missing_marker": marker})

    faz26_current_authority = load_json(FAZ26_ARTEFACTS["current_authority"])
    faz26_surface_summary = load_json(FAZ26_ARTEFACTS["model_visible_summary"])
    faz26_output_parity = load_json(FAZ26_ARTEFACTS["output_parity_summary"])
    faz26_retention = load_json(FAZ26_ARTEFACTS["retention_gate"])

    frontier_records = build_frontier_records()
    frontier_ids = [row["id"] for row in frontier_records]
    rc_g_family_questions = {
        family_id: merge_eval_question_maps([path])
        for family_id, path in FAZ26_RC_G_EVALS.items()
    }
    rc_n_family_questions = {
        family_id: merge_eval_question_maps([path])
        for family_id, path in FAZ26_RC_N_EVALS.items()
    }
    rc_g_frontier_questions = {
        row["id"]: rc_g_family_questions[row["authority_family_id"]][row["source_question_id"]]
        for row in frontier_records
    }
    rc_n_frontier_questions = {
        row["id"]: rc_n_family_questions[row["authority_family_id"]][row["source_question_id"]]
        for row in frontier_records
    }
    full_family_comparison = compare_question_maps(
        family_id="full-family",
        reference_questions=rc_g_frontier_questions,
        candidate_questions=rc_n_frontier_questions,
        question_ids=frontier_ids,
    )
    reference_pack = {
        "reference_pack_integrity_pass": len(reference_contradictions) == 0,
        "reference_pack_contradiction_count": len(reference_contradictions),
        "quality_reference_ref": "FAZ6",
        "canonical_current_authority_ref": "FAZ21",
        "release_controls_legacy_ref": "FAZ26",
        "archival_closure_ref": "FAZ24",
        "candidate_id": "RC-N",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "reference_contradictions": reference_contradictions,
    }

    current_authority_gate = {
        "control_pair_authority_match": bool(faz26_current_authority["control_pair_authority_match"]),
        "current_authority_contract_breach": bool(faz26_current_authority["current_authority_contract_breach"]),
        "surface_breach_from_history_reintroduced": bool(faz26_current_authority["surface_breach_from_history_reintroduced"]),
        "current_canonical_authority_adopted": bool(faz26_current_authority["current_canonical_authority_adopted"]),
        "control_pair_runtime_error_count": int(faz26_current_authority["control_pair_runtime_error_count"]),
    }

    upstream_equality_gate = {
        "control_pair_authority_match": current_authority_gate["control_pair_authority_match"],
        "current_authority_contract_breach": current_authority_gate["current_authority_contract_breach"],
        "surface_breach_from_history_reintroduced": current_authority_gate["surface_breach_from_history_reintroduced"],
        "current_canonical_authority_adopted": current_authority_gate["current_canonical_authority_adopted"],
        "control_pair_runtime_error_count": current_authority_gate["control_pair_runtime_error_count"],
        "model_request_payload_hash_mismatch_count": int(faz26_surface_summary["model_request_payload_hash_mismatch_count"]),
        "retrieval_request_hash_mismatch_count": int(faz26_surface_summary["retrieval_request_hash_mismatch_count"]),
        "assembled_context_hash_mismatch_count": int(faz26_surface_summary["assembled_context_hash_mismatch_count"]),
        "runtime_error_count": int(faz26_surface_summary["runtime_error_count"]),
    }

    boundary_summary = {
        "faz1_50_mismatch_count": int(faz26_output_parity["faz1_50_mismatch_count"]),
        "v2_95_mismatch_count": int(faz26_output_parity["v2_95_mismatch_count"]),
        "v3_170_mismatch_count": int(faz26_output_parity["v3_170_mismatch_count"]),
        "model_request_payload_hash_mismatch_count": int(faz26_surface_summary["model_request_payload_hash_mismatch_count"]),
        "retrieval_request_hash_mismatch_count": int(faz26_surface_summary["retrieval_request_hash_mismatch_count"]),
        "assembled_context_hash_mismatch_count": int(faz26_surface_summary["assembled_context_hash_mismatch_count"]),
        "preprojection_hash_mismatch_count": int(faz26_surface_summary["preprojection_hash_mismatch_count"]),
        "raw_answer_hash_mismatch_count": int(faz26_surface_summary["raw_answer_hash_mismatch_count"]),
        "response_envelope_hash_mismatch_count": int(full_family_comparison["response_envelope_hash_mismatch_count"]),
        "first_break_stage_assigned_count": int(faz26_surface_summary["first_break_stage_assigned_count"]),
        "primary_reason_assigned_count": int(faz26_surface_summary["primary_reason_assigned_count"]),
        "unexplained_count": int(faz26_surface_summary["unexplained_count"]),
        "frontier_total": len(frontier_records),
        "family_rows": _family_rows_from_surface_reports(),
    }

    frontier_freeze = {
        "frontier_total": len(frontier_records),
        "question_ids": frontier_ids,
        "records": frontier_records,
        "authoritative_counts": {
            "faz1_50_mismatch_count": boundary_summary["faz1_50_mismatch_count"],
            "v2_95_mismatch_count": boundary_summary["v2_95_mismatch_count"],
            "v3_170_mismatch_count": boundary_summary["v3_170_mismatch_count"],
            "preprojection_hash_mismatch_count": boundary_summary["preprojection_hash_mismatch_count"],
            "raw_answer_hash_mismatch_count": boundary_summary["raw_answer_hash_mismatch_count"],
            "response_envelope_hash_mismatch_count": boundary_summary["response_envelope_hash_mismatch_count"],
        },
        "report_hash": stable_hash(frontier_ids),
    }

    retention_matrix = {
        "must_close_release_controls_pass": bool(faz26_retention["must_close_release_controls_pass"]),
        "must_close_release_controls_count": int(faz26_retention["must_close_release_controls_count"]),
        "retained_after_family_eval": bool(faz26_retention["retained_after_family_eval"]),
        "retained_after_restart": bool(faz26_retention["retained_after_restart"]),
        "retained_after_restore": bool(faz26_retention["retained_after_restore"]),
        "pii_leak_found": bool(faz26_retention["pii_leak_found"]),
        "token_accounting_fallback_found": bool(faz26_retention["token_accounting_fallback_found"]),
        "release_smoke_gap_found": bool(faz26_retention["release_smoke_gap_found"]),
        "auth_bypass_found": bool(faz26_retention["auth_bypass_found"]),
        "audit_write_loss_found": bool(faz26_retention["audit_write_loss_found"]),
        "redis_continuity_break_found": bool(faz26_retention["redis_continuity_break_found"]),
        "observability_gap_found": bool(faz26_retention["observability_gap_found"]),
        "api_versioning_gap_found": bool(faz26_retention["api_versioning_gap_found"]),
        "supervision_gap_found": bool(faz26_retention["supervision_gap_found"]),
        "backup_restore_gap_found": bool(faz26_retention["backup_restore_gap_found"]),
        "control_rows": faz26_retention["control_rows"],
    }

    return {
        "reference_pack": reference_pack,
        "current_authority_gate": current_authority_gate,
        "upstream_equality_gate": upstream_equality_gate,
        "boundary_summary": boundary_summary,
        "frontier_freeze": frontier_freeze,
        "retention_matrix": retention_matrix,
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    reference_pack = payload["reference_pack"]
    current = payload["current_authority_gate"]
    upstream = payload["upstream_equality_gate"]
    boundary = payload["boundary_summary"]
    frontier = payload["frontier_freeze"]
    retention = payload["retention_matrix"]

    implementation_plan_lines = [
        "# FAZ27 Official Implementation Plan",
        "",
        "- faz_scope = `forensic-only`",
        "- candidate_id = `RC-N`",
        "- base_candidate = `RC-G`",
        "- control_candidate = `RC-J`",
        "- allowed_diff_surface = `release_controls_boundary_only`",
        "- answer_path_delta_allowed = `false`",
        "- open_sequence = `WP-1 -> WP-2 -> WP-3 -> WP-4 -> WP-5 -> WP-6 -> WP-7`",
        "- ladder_order = `B0 -> B8`",
        "- operational_controls_ladder_excluded = `true`",
        "- authoritative_frontier_total = `166`",
    ]

    contract_lines = [
        "# FAZ27 RC-N Boundary Forensics Contract",
        "",
        f"- candidate_id = `{reference_pack['candidate_id']}`",
        f"- base_candidate = `{reference_pack['base_candidate']}`",
        f"- control_candidate = `{reference_pack['control_candidate']}`",
        f"- allowed_diff_surface = `{reference_pack['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(reference_pack['answer_path_delta_allowed'])}`",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
    ]

    classification_lines = [
        "# FAZ27 RC-N Release Controls Classification",
        "",
        *markdown_table(
            [
                ("control_name", "control_name"),
                ("control_class", "control_class"),
                ("bind_step", "bind_step"),
                ("has_distinct_runtime_handle", "has_distinct_runtime_handle"),
                ("runtime_surface_delegate", "runtime_surface_delegate"),
                ("should_touch_answer_path", "should_touch_answer_path"),
            ],
            CONTROL_ROWS,
        ),
        "",
    ]

    bind_order_lines = [
        "# FAZ27 RC-N Runtime Boundary Bind Order",
        "",
        *markdown_table(
            [
                ("step_id", "step_id"),
                ("label", "label"),
                ("bound_control_set", "bound_control_set"),
            ],
            BIND_ORDER_ROWS,
        ),
        "",
    ]

    current_authority_lines = [
        "# FAZ27 RC-G vs RC-J Current Authority Check",
        "",
        f"- control_pair_authority_match = `{bool_text(current['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(current['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(current['surface_breach_from_history_reintroduced'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(current['current_canonical_authority_adopted'])}`",
        f"- control_pair_runtime_error_count = `{current['control_pair_runtime_error_count']}`",
        "",
    ]

    upstream_lines = [
        "# FAZ27 RC-G vs RC-N Upstream Equality Gate",
        "",
        f"- control_pair_authority_match = `{bool_text(upstream['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(upstream['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(upstream['surface_breach_from_history_reintroduced'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(upstream['current_canonical_authority_adopted'])}`",
        f"- control_pair_runtime_error_count = `{upstream['control_pair_runtime_error_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
        f"- runtime_error_count = `{upstream['runtime_error_count']}`",
        "",
    ]

    boundary_lines = [
        "# FAZ27 RC-G vs RC-N Full-Family Boundary Summary",
        "",
        f"- faz1_50_mismatch_count = `{boundary['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{boundary['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{boundary['v3_170_mismatch_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{boundary['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{boundary['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{boundary['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{boundary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{boundary['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{boundary['response_envelope_hash_mismatch_count']}`",
        f"- first_break_stage_assigned_count = `{boundary['first_break_stage_assigned_count']}`",
        f"- primary_reason_assigned_count = `{boundary['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{boundary['unexplained_count']}`",
        f"- frontier_total = `{boundary['frontier_total']}`",
        "",
        *markdown_table(
            [
                ("family_id", "family"),
                ("question_count", "question_count"),
                ("preprojection_hash_mismatch_count", "preprojection"),
                ("raw_answer_hash_mismatch_count", "raw_answer"),
                ("first_break_stage_assigned_count", "first_break_assigned"),
                ("primary_reason_assigned_count", "primary_reason_assigned"),
                ("unexplained_count", "unexplained"),
            ],
            boundary["family_rows"],
        ),
        "",
    ]

    frontier_lines = [
        "# FAZ27 RC-N Boundary Frontier Freeze",
        "",
        f"- frontier_total = `{frontier['frontier_total']}`",
        f"- faz1_50_mismatch_count = `{frontier['authoritative_counts']['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{frontier['authoritative_counts']['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{frontier['authoritative_counts']['v3_170_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{frontier['authoritative_counts']['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{frontier['authoritative_counts']['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{frontier['authoritative_counts']['response_envelope_hash_mismatch_count']}`",
        "",
        "## Frontier Sample",
        "",
    ]
    for row in frontier["records"][:20]:
        frontier_lines.append(
            f"- `{row['id']}` source `{row['source_question_id']}` family `{row['authority_family_id']}` stage `{row['authoritative_first_break_stage']}` reason `{row['authoritative_primary_reason']}`"
        )
    frontier_lines.append("")

    retention_lines = [
        "# FAZ27 RC-N Release Controls Retention Matrix",
        "",
        f"- must_close_release_controls_pass = `{bool_text(retention['must_close_release_controls_pass'])}`",
        f"- must_close_release_controls_count = `{retention['must_close_release_controls_count']}`",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- pii_leak_found = `{bool_text(retention['pii_leak_found'])}`",
        f"- token_accounting_fallback_found = `{bool_text(retention['token_accounting_fallback_found'])}`",
        f"- release_smoke_gap_found = `{bool_text(retention['release_smoke_gap_found'])}`",
        f"- auth_bypass_found = `{bool_text(retention['auth_bypass_found'])}`",
        f"- audit_write_loss_found = `{bool_text(retention['audit_write_loss_found'])}`",
        f"- redis_continuity_break_found = `{bool_text(retention['redis_continuity_break_found'])}`",
        f"- observability_gap_found = `{bool_text(retention['observability_gap_found'])}`",
        f"- api_versioning_gap_found = `{bool_text(retention['api_versioning_gap_found'])}`",
        f"- supervision_gap_found = `{bool_text(retention['supervision_gap_found'])}`",
        f"- backup_restore_gap_found = `{bool_text(retention['backup_restore_gap_found'])}`",
        "",
        *markdown_table([("control", "control"), ("pass", "pass")], retention["control_rows"]),
        "",
    ]

    return {
        ROOT / "coordination" / f"faz27-official-implementation-plan-{DATE}.md": "\n".join(implementation_plan_lines),
        ROOT / "coordination" / f"faz27-rc-n-boundary-forensics-contract-{DATE}.md": "\n".join(contract_lines),
        ROOT / "coordination" / f"faz27-rc-n-release-controls-classification-{DATE}.md": "\n".join(classification_lines),
        ROOT / "coordination" / f"faz27-rc-n-runtime-boundary-bind-order-{DATE}.md": "\n".join(bind_order_lines),
        ROOT / "coordination" / f"faz27-rc-n-boundary-frontier-freeze-{DATE}.md": "\n".join(frontier_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-g-vs-rc-j-current-authority-check-{DATE}.md": "\n".join(current_authority_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-g-vs-rc-n-upstream-equality-gate-{DATE}.md": "\n".join(upstream_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-g-vs-rc-n-full-family-boundary-summary-{DATE}.md": "\n".join(boundary_lines),
        ROOT / "evaluation" / "reports" / f"faz27-rc-n-release-controls-retention-matrix-{DATE}.md": "\n".join(retention_lines),
        ROOT / "coordination" / f"faz27-reference-pack-{DATE}.json": payload,
        ROOT / "coordination" / f"faz27-rc-n-boundary-frontier-freeze-{DATE}.json": frontier,
        ROOT / "evaluation" / "reports" / f"faz27-rc-g-vs-rc-j-current-authority-check-{DATE}.json": current,
        ROOT / "evaluation" / "reports" / f"faz27-rc-g-vs-rc-n-upstream-equality-gate-{DATE}.json": upstream,
        ROOT / "evaluation" / "reports" / f"faz27-rc-g-vs-rc-n-full-family-boundary-summary-{DATE}.json": boundary,
        ROOT / "evaluation" / "reports" / f"faz27-rc-n-release-controls-retention-matrix-{DATE}.json": retention,
        ROOT / "configs" / "evaluation" / f"test_questions_faz27_boundary_frontier_166_{COMPACT_DATE}.json": {"questions": frontier["records"]},
    }


def main() -> int:
    payload = build_materialization_payload()
    outputs = render_outputs(payload)
    for path, content in outputs.items():
        if isinstance(content, dict):
            write_json(path, content)
        else:
            write_text(path, content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
