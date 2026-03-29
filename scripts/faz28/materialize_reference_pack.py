#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz28_lib import (  # type: ignore
    BOUNDARY_FRONTIER_PACK_PATH,
    COMPACT_DATE,
    DATE,
    FAZ21_CANONICAL_GATE_JSON,
    FAZ21_CANONICAL_REFERENCE_JSON,
    FAZ27_REFERENCE_PACK_JSON,
    MATERIALIZED_REFERENCE_JSON,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    ROOT,
    build_frontier_records,
    build_spillover_guard_records,
    bool_text,
    load_json,
    load_text,
    markdown_table,
    stable_hash,
    write_json,
    write_question_pack,
    write_text,
    SPILLOVER_GUARD_PACK_PATH,
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

    control_pair_authority_match = all(row["pass"] for row in families)
    return {
        "control_pair_reference": str(canonical_reference.get("reference_name") or "canonical_current_authority_ref"),
        "control_pair_authority_match": control_pair_authority_match,
        "current_authority_contract_breach": bool(canonical_reference.get("current_authority_contract_breach", True)),
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_authority_adopted": bool(canonical_gate.get("current_canonical_authority_adopted", False)),
        "canonicalization_gate_pass": bool(canonical_gate.get("canonicalization_gate_pass", False)),
        "control_pair_runtime_error_count": int(canonical_reference.get("control_pair_runtime_error_count", 0)),
        "families": families,
    }


def build_materialization_payload() -> dict[str, Any]:
    reference_contradictions: list[dict[str, str]] = []
    for ref_name, path in REFERENCE_FILES.items():
        text = load_text(path)
        for marker in REFERENCE_MARKERS[ref_name]:
            if marker not in text:
                reference_contradictions.append(
                    {
                        "reference_name": ref_name,
                        "missing_marker": marker,
                    }
                )

    faz27_payload = load_json(FAZ27_REFERENCE_PACK_JSON)
    boundary_summary = dict(faz27_payload["boundary_summary"])
    frontier_freeze = dict(faz27_payload["frontier_freeze"])
    frontier_records = build_frontier_records()
    spillover_records = build_spillover_guard_records(frontier_records)

    reference_pack = {
        "reference_pack_integrity_pass": len(reference_contradictions) == 0,
        "reference_pack_contradiction_count": len(reference_contradictions),
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
        "reference_contradictions": reference_contradictions,
    }

    manifest = {
        "candidate_id": "RC-O",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "candidate_status": "release_controls_boundary_repair_candidate",
        "diagnostic_only": False,
        "promotable": False,
        "repairable": False,
        "current_evaluable": True,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "report_hash": stable_hash("faz28-rc-o-manifest-v1"),
    }

    return {
        "reference_pack": reference_pack,
        "current_authority_gate": _build_current_authority_gate(),
        "boundary_summary": boundary_summary,
        "frontier_freeze": frontier_freeze,
        "frontier_records": frontier_records,
        "spillover_guard": {
            "record_count": len(spillover_records),
            "records": spillover_records,
            "selection_rule": {
                "faz1-50": 4,
                "v2-95": 8,
                "v3-170": 12,
            },
        },
        "manifest": manifest,
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    reference_pack = payload["reference_pack"]
    current = payload["current_authority_gate"]
    boundary = payload["boundary_summary"]
    frontier_freeze = payload["frontier_freeze"]
    spillover = payload["spillover_guard"]
    manifest = payload["manifest"]

    implementation_plan_lines = [
        "# FAZ28 Official Implementation Plan",
        "",
        "- phase_scope = `boundary_repair_only`",
        "- candidate_id = `RC-O`",
        "- base_candidate = `RC-G`",
        "- control_candidate = `RC-J`",
        "- forensic_reference_candidate = `RC-N`",
        "- allowed_diff_surface = `release_controls_boundary_only`",
        "- answer_path_delta_allowed = `false`",
        "- execution_order = `WP-1 -> WP-2 -> WP-3 -> WP-4 -> WP-5 -> WP-6 -> WP-7`",
        "- frozen_frontier_total = `166`",
        "- spillover_guard_total = `24`",
        "- cutover_authorized = `false`",
        "- pilot_authorized = `false`",
    ]

    reference_lines = [
        "# FAZ28 Release Controls Reference Pack",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- quality_reference_ref = `{reference_pack['quality_reference_ref']}`",
        f"- canonical_current_authority_ref = `{reference_pack['canonical_current_authority_ref']}`",
        f"- release_controls_legacy_ref = `{reference_pack['release_controls_legacy_ref']}`",
        f"- archival_closure_ref = `{reference_pack['archival_closure_ref']}`",
        "",
    ]

    build_contract_lines = [
        "# FAZ28 RC-O Build Contract",
        "",
        f"- candidate_id = `{reference_pack['candidate_id']}`",
        f"- base_candidate = `{reference_pack['base_candidate']}`",
        f"- control_candidate = `{reference_pack['control_candidate']}`",
        f"- forensic_reference_candidate = `{reference_pack['forensic_reference_candidate']}`",
        f"- allowed_diff_surface = `{reference_pack['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(reference_pack['answer_path_delta_allowed'])}`",
        f"- candidate_status = `{manifest['candidate_status']}`",
        f"- cutover_authorized = `{bool_text(manifest['cutover_authorized'])}`",
        f"- pilot_authorized = `{bool_text(manifest['pilot_authorized'])}`",
    ]

    boundary_contract_lines = [
        "# FAZ28 RC-O Boundary Repair Contract",
        "",
        "- mandatory auth = `enabled`",
        "- immutable audit logging = `enabled`",
        "- Redis session persistence = `enabled`",
        "- persisted PII redaction = `persist-only`",
        "- tokenizer-backed accounting = `required`",
        "- answer_path_delta_allowed = `false`",
        "- release_controls_boundary_proxy = `required`",
        "- operational_smoke_runner = `one-command only`",
    ]

    snapshot_contract_lines = [
        "# FAZ28 Canonical Answer-Path Snapshot Contract",
        "",
        "- canonical_request_snapshot_authoritative = `true`",
        "- model_visible_source = `canonical_request_snapshot`",
        "- auth_metadata_in_model_visible_surface = `false`",
        "- session_metadata_in_model_visible_surface = `false`",
        "- audit_metadata_in_model_visible_surface = `false`",
        "- version_metadata_in_model_visible_surface = `false`",
        "- tokenizer_accounting_metadata_in_model_visible_surface = `false`",
    ]

    frontier_lines = [
        "# FAZ28 Boundary Frontier 166 Freeze",
        "",
        f"- frontier_total = `{frontier_freeze['frontier_total']}`",
        f"- faz1_50_mismatch_count = `{boundary['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{boundary['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{boundary['v3_170_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{boundary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{boundary['raw_answer_hash_mismatch_count']}`",
        "",
    ]

    spillover_lines = [
        "# FAZ28 Spillover Guard 24",
        "",
        f"- record_count = `{spillover['record_count']}`",
        "- deterministic_selection = `family asc question_id asc frontier excluded`",
        "- faz1_50_selected = `4`",
        "- v2_95_selected = `8`",
        "- v3_170_selected = `12`",
        "",
    ]

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "coordination" / f"faz28-official-implementation-plan-{DATE}.md": "\n".join(implementation_plan_lines),
        ROOT / "coordination" / f"faz28-release-controls-reference-pack-{DATE}.md": "\n".join(reference_lines),
        ROOT / "coordination" / f"faz28-rc-o-build-contract-{DATE}.md": "\n".join(build_contract_lines),
        ROOT / "coordination" / f"faz28-rc-o-boundary-repair-contract-{DATE}.md": "\n".join(boundary_contract_lines),
        ROOT / "coordination" / f"faz28-canonical-answer-path-snapshot-contract-{DATE}.md": "\n".join(snapshot_contract_lines),
        ROOT / "coordination" / f"faz28-boundary-frontier-166-freeze-{DATE}.md": "\n".join(frontier_lines),
        ROOT / "coordination" / f"faz28-spillover-guard-24-{DATE}.md": "\n".join(spillover_lines),
        ROOT / "coordination" / f"faz28-rc-o-manifest-{DATE}.json": manifest,
        MATERIALIZED_REFERENCE_JSON: payload,
        BOUNDARY_FRONTIER_PACK_PATH: {"questions": payload["frontier_records"]},
        SPILLOVER_GUARD_PACK_PATH: {"questions": spillover["records"]},
    }

    return outputs


def materialize() -> dict[str, Any]:
    payload = build_materialization_payload()
    outputs = render_outputs(payload)
    for path, body in outputs.items():
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
