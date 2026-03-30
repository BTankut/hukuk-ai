#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz30_lib import (  # type: ignore
    BIND_ORDER_ROWS,
    BOUNDARY_PACK_PATH,
    COMBINED_PACK_PATH,
    COMPACT_DATE,
    CONTROL_SET_ROWS,
    CONTROL_ROWS,
    DATE,
    FAZ21_CANONICAL_GATE_JSON,
    FAZ21_CANONICAL_REFERENCE_JSON,
    INCONCLUSIVE_RECAPTURE_REF,
    MATERIALIZED_REFERENCE_JSON,
    PRIMARY_REASON_SET,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    ROOT,
    RUNTIME_STAGE_LADDER,
    SPILLOVER_PACK_PATH,
    STABLE_REPAIR_TRUTH_REF,
    bool_text,
    build_boundary_frontier_records,
    build_combined_records,
    build_spillover_guard_records,
    load_json,
    load_text,
    markdown_table,
    stable_hash,
    write_json,
    write_question_pack,
    write_text,
)


def _build_current_authority_gate() -> dict[str, Any]:
    canonical_reference = load_json(FAZ21_CANONICAL_REFERENCE_JSON)
    canonical_gate = load_json(FAZ21_CANONICAL_GATE_JSON)
    families = []
    for row in canonical_reference.get("families", []):
        families.append(
            {
                "family_name": str(row["family_name"]),
                "mismatch_count": int(row.get("mismatch_count", 0)),
                "runtime_error_count": int(row.get("runtime_error_count", 0)),
                "family_metric_delta_zero": bool(row.get("family_metric_delta_zero", False)),
                "pass": (
                    int(row.get("mismatch_count", 0)) == 0
                    and int(row.get("runtime_error_count", 0)) == 0
                    and bool(row.get("family_metric_delta_zero", False)) is True
                ),
            }
        )
    return {
        "control_pair_authority_match": all(row["pass"] for row in families),
        "current_authority_contract_breach": bool(canonical_reference.get("current_authority_contract_breach", True)),
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_authority_adopted": bool(canonical_gate.get("current_canonical_authority_adopted", False)),
        "control_pair_runtime_error_count": int(canonical_reference.get("control_pair_runtime_error_count", 0)),
        "families": families,
    }


def build_materialization_payload() -> dict[str, Any]:
    contradictions: list[dict[str, str]] = []
    for ref_name, path in REFERENCE_FILES.items():
        text = load_text(path)
        for marker in REFERENCE_MARKERS[ref_name]:
            if marker not in text:
                contradictions.append({"reference_name": ref_name, "missing_marker": marker})

    boundary_records = build_boundary_frontier_records()
    spillover_records = build_spillover_guard_records()
    combined_records = build_combined_records()

    reference_pack = {
        "reference_pack_integrity_pass": len(contradictions) == 0,
        "reference_pack_contradiction_count": len(contradictions),
        "stable_repair_truth_ref": "FAZ28",
        "inconclusive_recapture_ref": "FAZ29",
        "quality_reference_ref": "FAZ6",
        "canonical_current_authority_ref": "FAZ21",
        "steering_topology_ref": "FAZ25",
        "release_controls_legacy_ref": "FAZ26",
        "boundary_root_cause_ref": "FAZ27",
        "archival_closure_ref": "FAZ24",
        "candidate_id": "RC-O",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "reference_contradictions": contradictions,
    }

    contract = {
        "candidate_id": "RC-O",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "candidate_status": "frozen_failed_repair_candidate",
        "promotable": False,
        "repairable": False,
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "report_hash": stable_hash("faz30-rc-o-forensic-contract-v1"),
    }

    return {
        "reference_pack": reference_pack,
        "current_authority_gate": _build_current_authority_gate(),
        "contract": contract,
        "stable_repair_truth_ref": STABLE_REPAIR_TRUTH_REF,
        "inconclusive_recapture_ref": INCONCLUSIVE_RECAPTURE_REF,
        "boundary_records": boundary_records,
        "spillover_records": spillover_records,
        "combined_records": combined_records,
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    reference_pack = payload["reference_pack"]
    contract = payload["contract"]
    current_authority = payload["current_authority_gate"]
    boundary_records = payload["boundary_records"]
    spillover_records = payload["spillover_records"]
    combined_records = payload["combined_records"]

    implementation_lines = [
        "# FAZ30 Official Implementation Plan",
        "",
        "- phase_scope = `forensic_only`",
        "- candidate_id = `RC-O`",
        "- base_candidate = `RC-G`",
        "- control_candidate = `RC-J`",
        "- forensic_reference_candidate = `RC-N`",
        "- execution_order = `WP-1 -> WP-2 -> WP-3 -> WP-4 -> WP-5 -> WP-6 -> WP-7 -> WP-8 -> WP-9`",
        "- boundary_frontier_count = `166`",
        "- spillover_guard_count = `24`",
        "- control_set_count = `9`",
        "- build_or_patch_allowed = `false`",
    ]

    reference_lines = [
        "# FAZ30 Reference Pack",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- stable_repair_truth_ref = `{reference_pack['stable_repair_truth_ref']}`",
        f"- inconclusive_recapture_ref = `{reference_pack['inconclusive_recapture_ref']}`",
        f"- quality_reference_ref = `{reference_pack['quality_reference_ref']}`",
        f"- canonical_current_authority_ref = `{reference_pack['canonical_current_authority_ref']}`",
        "",
    ]

    lineage_lines = [
        "# FAZ30 RC-O Repair Truth Lineage Matrix",
        "",
        "| truth_class | record_count | mismatch_count | preprojection_hash_mismatch_count | raw_answer_hash_mismatch_count | response_envelope_hash_mismatch_count | runtime_error_count | first_break_stage_assigned_count | primary_reason_assigned_count | unexplained_count |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| boundary_root_cause_truth | 166 | 166 | 166 | 166 | 99 | 0 | 166 | 166 | 0 |",
        f"| stable_repair_truth | 166 | 152 | 152 | 152 | 92 | 0 | 152 | 152 | 0 |",
        f"| inconclusive_recapture_truth | 166 | 166 | 0 | 0 | 0 | 166 | 0 | 0 | 166 |",
        f"| current_forensic_truth | 166 | pending | pending | pending | pending | pending | pending | pending | pending |",
        "",
    ]

    ladder_lines = [
        "# FAZ30 Runtime Stage Ladder Contract",
        "",
        *[f"- `{stage}`" for stage in RUNTIME_STAGE_LADDER],
        "",
        "## Allowed Primary Reasons",
        "",
        *[f"- `{reason}`" for reason in PRIMARY_REASON_SET],
        "",
    ]

    control_set_lines = [
        "# FAZ30 Control-Set Isolation Matrix Contract",
        "",
        *markdown_table(
            [("control_set_id", "control_set_id"), ("controls", "controls")],
            [
                {"control_set_id": row["control_set_id"], "controls": row["controls"]}
                for row in CONTROL_SET_ROWS
            ],
        ),
        "",
    ]

    failing_triplet_lines = [
        "# FAZ30 Failing-Control Triplet Contrast Contract",
        "",
        "- exact_fields = `persisted_pii_redaction_pass, tokenizer_backed_accounting_pass, api_versioning_pass, one_command_release_smoke_pass, pii_leak_found, token_accounting_fallback_found, api_versioning_gap_found, release_smoke_gap_found, runtime_error_count, unexplained_count`",
        "",
    ]

    retention_lines = [
        "# FAZ30 Retention Truth Contrast Contract",
        "",
        "- exact_fields = `retained_after_family_eval, retained_after_restart, retained_after_restore, answer_path_delta_reintroduced, runtime_error_count, unexplained_count`",
        "- one_hot_flags = `matches_faz28_truth, matches_faz29_truth, matches_neither_new_stable_truth`",
        "",
    ]

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "coordination" / f"faz30-official-implementation-plan-{DATE}.md": "\n".join(implementation_lines),
        ROOT / "coordination" / f"faz30-reference-pack-{DATE}.md": "\n".join(reference_lines),
        ROOT / "coordination" / f"faz30-rc-o-repair-truth-lineage-matrix-{DATE}.md": "\n".join(lineage_lines),
        ROOT / "coordination" / f"faz30-runtime-stage-ladder-contract-{DATE}.md": "\n".join(ladder_lines),
        ROOT / "coordination" / f"faz30-control-set-isolation-matrix-contract-{DATE}.md": "\n".join(control_set_lines),
        ROOT / "coordination" / f"faz30-failing-control-triplet-contrast-contract-{DATE}.md": "\n".join(failing_triplet_lines),
        ROOT / "coordination" / f"faz30-retention-truth-contrast-contract-{DATE}.md": "\n".join(retention_lines),
        MATERIALIZED_REFERENCE_JSON: payload,
        BOUNDARY_PACK_PATH: {"questions": boundary_records},
        SPILLOVER_PACK_PATH: {"questions": spillover_records},
        COMBINED_PACK_PATH: {"questions": combined_records},
    }
    return outputs


def materialize() -> dict[str, Any]:
    payload = build_materialization_payload()
    for path, body in render_outputs(payload).items():
        if isinstance(body, (dict, list)):
            write_json(path, body)
        else:
            write_text(path, body)
    return payload


def main() -> int:
    materialize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
