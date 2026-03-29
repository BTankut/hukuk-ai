#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz29_lib import (  # type: ignore
    ACCEPTANCE_EXPECTED,
    BOUNDARY_EXPECTED,
    BOUNDARY_FRONTIER_PACK_PATH,
    COMPACT_DATE,
    DATE,
    FAILING_CONTROL_TRIPLET,
    FAZ21_CANONICAL_GATE_JSON,
    FAZ21_CANONICAL_REFERENCE_JSON,
    FAZ28_PHASE_PACKAGE_JSON,
    MATERIALIZED_REFERENCE_JSON,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    REPAIR_DELTA_PACK_PATH,
    RETENTION_EXPECTED,
    ROOT,
    SPILLOVER_EXPECTED,
    SPILLOVER_GUARD_PACK_PATH,
    bool_text,
    build_frontier_records,
    build_repair_delta_records,
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
        family_row = {
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
        families.append(family_row)
    return {
        "control_pair_reference": str(canonical_reference.get("reference_name") or "canonical_current_authority_ref"),
        "control_pair_authority_match": all(row["pass"] for row in families),
        "current_authority_contract_breach": bool(canonical_reference.get("current_authority_contract_breach", True)),
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_authority_adopted": bool(canonical_gate.get("current_canonical_authority_adopted", False)),
        "canonicalization_gate_pass": bool(canonical_gate.get("canonicalization_gate_pass", False)),
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

    faz28_phase = load_json(FAZ28_PHASE_PACKAGE_JSON)
    frontier_records = build_frontier_records()
    repair_delta_records = build_repair_delta_records(frontier_records)
    spillover_records = build_spillover_guard_records()

    reference_pack = {
        "reference_pack_integrity_pass": len(contradictions) == 0,
        "reference_pack_contradiction_count": len(contradictions),
        "quality_reference_ref": "FAZ6",
        "canonical_current_authority_ref": "FAZ21",
        "release_controls_legacy_ref": "FAZ26",
        "archival_closure_ref": "FAZ24",
        "candidate_id": "RC-O",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "reference_contradictions": contradictions,
    }

    manifest = {
        "candidate_id": "RC-O",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "candidate_status": "frozen_failed_repair_candidate",
        "promotable": False,
        "repairable": False,
        "current_evaluable": True,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "report_hash": stable_hash("faz29-rc-o-manifest-v1"),
    }

    phase28_boundary = faz28_phase["boundary_frontier_summary"]
    phase28_spillover = faz28_phase["spillover_summary"]
    acceptance_truth = {
        **ACCEPTANCE_EXPECTED,
        "control_rows": list((faz28_phase.get("acceptance_summary") or {}).get("control_rows") or []),
    }

    return {
        "reference_pack": reference_pack,
        "manifest": manifest,
        "current_authority_gate": _build_current_authority_gate(),
        "boundary_truth": {
            **BOUNDARY_EXPECTED,
            "phase28_mismatch_rows": list(phase28_boundary.get("mismatch_rows") or []),
        },
        "spillover_truth": {
            **SPILLOVER_EXPECTED,
            "phase28_mismatch_rows": list(phase28_spillover.get("mismatch_rows") or []),
        },
        "acceptance_truth": acceptance_truth,
        "retention_truth": RETENTION_EXPECTED,
        "frontier_records": frontier_records,
        "repair_delta_records": repair_delta_records,
        "spillover_guard_records": spillover_records,
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    reference_pack = payload["reference_pack"]
    manifest = payload["manifest"]
    current = payload["current_authority_gate"]
    boundary = payload["boundary_truth"]
    spillover = payload["spillover_truth"]
    acceptance = payload["acceptance_truth"]
    retention = payload["retention_truth"]
    frontier_records = payload["frontier_records"]
    repair_delta_records = payload["repair_delta_records"]
    spillover_records = payload["spillover_guard_records"]

    implementation_plan_lines = [
        "# FAZ29 Official Implementation Plan",
        "",
        "- phase_scope = `recapture_only`",
        "- candidate_id = `RC-O`",
        "- base_candidate = `RC-G`",
        "- control_candidate = `RC-J`",
        "- forensic_reference_candidate = `RC-N`",
        "- execution_order = `WP-1 -> WP-2 -> WP-3 -> WP-4 -> WP-5 -> WP-6 -> WP-7`",
        "- recapture_mode = `twin_capture`",
        "- boundary_frontier_total = `166`",
        "- repair_delta_total = `14`",
        "- spillover_guard_total = `24`",
        "- cutover_authorized = `false`",
        "- pilot_authorized = `false`",
    ]

    reference_lines = [
        "# FAZ29 Release Controls Reference Pack",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- quality_reference_ref = `{reference_pack['quality_reference_ref']}`",
        f"- canonical_current_authority_ref = `{reference_pack['canonical_current_authority_ref']}`",
        f"- release_controls_legacy_ref = `{reference_pack['release_controls_legacy_ref']}`",
        f"- archival_closure_ref = `{reference_pack['archival_closure_ref']}`",
        "",
    ]

    contract_lines = [
        "# FAZ29 RC-O Recapture Contract",
        "",
        f"- candidate_id = `{manifest['candidate_id']}`",
        f"- base_candidate = `{manifest['base_candidate']}`",
        f"- control_candidate = `{manifest['control_candidate']}`",
        f"- forensic_reference_candidate = `{manifest['forensic_reference_candidate']}`",
        f"- allowed_diff_surface = `{manifest['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(manifest['answer_path_delta_allowed'])}`",
        f"- candidate_status = `{manifest['candidate_status']}`",
        f"- promotable = `{bool_text(manifest['promotable'])}`",
        f"- repairable = `{bool_text(manifest['repairable'])}`",
        f"- current_evaluable = `{bool_text(manifest['current_evaluable'])}`",
        f"- cutover_authorized = `{bool_text(manifest['cutover_authorized'])}`",
        f"- pilot_authorized = `{bool_text(manifest['pilot_authorized'])}`",
    ]

    frontier_lines = [
        "# FAZ29 RC-O Boundary Frontier 166 Freeze",
        "",
        f"- input_pack_count = `{boundary['input_pack_count']}`",
        f"- expected_remaining_mismatch_count = `{boundary['remaining_mismatch_count']}`",
        f"- expected_repaired_count_vs_rc_n = `{boundary['repair_delta_record_count']}`",
        "",
        "| family | expected_mismatch_count |",
        "| --- | --- |",
        f"| faz1-50 | {boundary['faz1_50_mismatch_count']} |",
        f"| v2-95 | {boundary['v2_95_mismatch_count']} |",
        f"| v3-170 | {boundary['v3_170_mismatch_count']} |",
        "",
    ]

    repair_delta_lines = [
        "# FAZ29 RC-O Repair Delta 14 Freeze",
        "",
        f"- repair_delta_record_count = `{len(repair_delta_records)}`",
        "- construction_rule = `faz27 frontier 166 mismatch set MINUS faz28 remaining mismatch set`",
        "",
    ]

    spillover_lines = [
        "# FAZ29 RC-O Spillover Guard 24 Freeze",
        "",
        f"- record_count = `{spillover['record_count']}`",
        f"- expected_mismatch_count = `{spillover['mismatch_count']}`",
        "- source = `faz28 exact spillover pack`",
        "",
    ]

    failing_control_lines = [
        "# FAZ29 RC-O Failing Control Triplet",
        "",
        *[f"- `{name}`" for name in FAILING_CONTROL_TRIPLET],
        "",
        f"- must_close_release_controls_count = `{acceptance['must_close_release_controls_count']}`",
        "",
        *markdown_table([("control", "control"), ("pass", "pass")], acceptance["control_rows"]),
        "",
    ]

    retention_lines = [
        "# FAZ29 RC-O Retention Recapture Contract",
        "",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
        "",
    ]

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "coordination" / f"faz29-official-implementation-plan-{DATE}.md": "\n".join(implementation_plan_lines),
        ROOT / "coordination" / f"faz29-release-controls-reference-pack-{DATE}.md": "\n".join(reference_lines),
        ROOT / "coordination" / f"faz29-rc-o-recapture-contract-{DATE}.md": "\n".join(contract_lines),
        ROOT / "coordination" / f"faz29-rc-o-boundary-frontier-166-freeze-{DATE}.md": "\n".join(frontier_lines),
        ROOT / "coordination" / f"faz29-rc-o-repair-delta-14-freeze-{DATE}.md": "\n".join(repair_delta_lines),
        ROOT / "coordination" / f"faz29-rc-o-spillover-guard-24-freeze-{DATE}.md": "\n".join(spillover_lines),
        ROOT / "coordination" / f"faz29-rc-o-failing-control-triplet-{DATE}.md": "\n".join(failing_control_lines),
        ROOT / "coordination" / f"faz29-rc-o-retention-recapture-contract-{DATE}.md": "\n".join(retention_lines),
        ROOT / "coordination" / f"faz29-rc-o-manifest-{DATE}.json": manifest,
        MATERIALIZED_REFERENCE_JSON: payload,
        BOUNDARY_FRONTIER_PACK_PATH: {"questions": frontier_records},
        REPAIR_DELTA_PACK_PATH: {"questions": repair_delta_records},
        SPILLOVER_GUARD_PACK_PATH: {"questions": spillover_records},
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
