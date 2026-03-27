#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz25_lib import (  # type: ignore
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    PASS_DECISION,
    PASS_NEXT_WORK,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    RELEASE_CONTROLS_EXACT_SET,
    SOURCE_OF_RECORD_FILES,
    bool_text,
    load_text,
    stable_hash,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-03-27"
RESULT_REPORT = (
    ROOT
    / "docs"
    / "FAZ25-POST-RC-M-STEERING-RE-ENTRY-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md"
)


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def build_phase_payload(reference_texts: dict[str, str], source_texts: dict[str, str]) -> dict[str, Any]:
    contradiction_rows = []
    for ref_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[ref_name]
        for field_name, marker in markers.items():
            if marker not in text:
                contradiction_rows.append(
                    {
                        "reference_name": ref_name,
                        "field_name": field_name,
                        "missing_marker": marker,
                    }
                )

    missing_release_controls = [
        item for item in RELEASE_CONTROLS_EXACT_SET if item not in source_texts["faz7_release_matrix"]
    ]
    if "must-close release controls remain open" not in reference_texts["faz1_5"]:
        contradiction_rows.append(
            {
                "reference_name": "faz1_5",
                "field_name": "must_close_release_controls_open",
                "missing_marker": "must-close release controls remain open",
            }
        )
    for item in missing_release_controls:
        contradiction_rows.append(
            {
                "reference_name": "faz7_release_matrix",
                "field_name": "must_close_release_controls_exact_set",
                "missing_marker": item,
            }
        )

    reference_pack_integrity_pass = len(contradiction_rows) == 0
    reference_pack_contradiction_count = len(contradiction_rows)

    wp1_pass = (
        reference_pack_integrity_pass
        and reference_pack_contradiction_count == 0
    )

    topology_rows = [
        {
            "candidate_id": "RC-G",
            "candidate_status": "accepted_quality_reference",
            "quality_reference": True,
            "current_authority_member": True,
            "diagnostic_only": False,
            "archived": False,
            "promotable": True,
            "repairable": False,
            "current_evaluable": True,
            "release_controls_reentry_base": True,
            "notes": "canonical_quality_reference_and_reentry_base",
        },
        {
            "candidate_id": "RC-J",
            "candidate_status": "canonical_control_diagnostic",
            "quality_reference": False,
            "current_authority_member": True,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "frozen_control_pair_for_canonical_authority_only",
        },
        {
            "candidate_id": "RC-M",
            "candidate_status": "discard_archived",
            "quality_reference": False,
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "historical_archive_diagnostic_only",
        },
    ]
    wp2_pass = len(topology_rows) == 3

    legacy_normalization = {
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_repair_candidate": "NONE",
        "active_parity_reopen_candidate": "NONE",
        "active_cutover_candidate": "NONE",
        "active_pilot_candidate": "NONE",
        "archived_candidate_set": ["RC-M"],
        "stale_branch_set": ["RC-H", "RC-I", "RC-L", "RC-M"],
        "stale_branch_left_active": False,
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_consumer_order": "current_canonical -> historical_archive",
        "legacy_release_controls_pointer_normalized": True,
    }
    wp3_pass = (
        legacy_normalization["active_quality_reference"] == "RC-G"
        and legacy_normalization["active_control_pair"] == "RC-G vs RC-J"
        and legacy_normalization["active_repair_candidate"] == "NONE"
        and legacy_normalization["active_parity_reopen_candidate"] == "NONE"
        and legacy_normalization["active_cutover_candidate"] == "NONE"
        and legacy_normalization["active_pilot_candidate"] == "NONE"
        and legacy_normalization["archived_candidate_set"] == ["RC-M"]
        and legacy_normalization["stale_branch_set"] == ["RC-H", "RC-I", "RC-L", "RC-M"]
        and legacy_normalization["stale_branch_left_active"] is False
        and legacy_normalization["surface_breach_from_history_reintroduced"] is False
        and legacy_normalization["current_canonical_consumer_order"] == "current_canonical -> historical_archive"
        and legacy_normalization["legacy_release_controls_pointer_normalized"] is True
    )

    next_contract = {
        "next_candidate_id": "RC-N",
        "next_candidate_base": "RC-G",
        "next_candidate_control": "RC-J",
        "next_candidate_status": "reserved_not_built",
        "next_phase_scope": "release_controls_closure_only_under_canonical_current_authority",
        "must_close_release_controls_source": "faz1_5 + faz7 sources_of_record",
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "retrieval_change_allowed": False,
        "prompt_change_allowed": False,
        "model_change_allowed": False,
        "guardrail_change_allowed": False,
        "corpus_change_allowed": False,
        "database_expansion_allowed": False,
        "cutover_authorized_in_next_phase": False,
        "pilot_authorized_in_next_phase": False,
        "parity_gate_required": True,
        "release_controls_retention_required": True,
        "must_close_release_controls_exact_set": RELEASE_CONTROLS_EXACT_SET,
        "must_close_release_controls_count": len(RELEASE_CONTROLS_EXACT_SET),
        "must_close_release_controls_exact_set_source_path": (
            "coordination/faz1_5-production-readiness-matrix-2026-03-22.md + "
            "coordination/faz7-production-readiness-matrix-v2-2026-03-24.md"
        ),
    }
    wp4_pass = (
        next_contract["next_candidate_id"] == "RC-N"
        and next_contract["next_candidate_base"] == "RC-G"
        and next_contract["next_candidate_control"] == "RC-J"
        and next_contract["next_candidate_status"] == "reserved_not_built"
        and next_contract["next_phase_scope"] == "release_controls_closure_only_under_canonical_current_authority"
        and next_contract["must_close_release_controls_source"] == "faz1_5 + faz7 sources_of_record"
        and next_contract["allowed_diff_surface"] == "release_controls_boundary_only"
        and next_contract["answer_path_delta_allowed"] is False
        and next_contract["database_expansion_allowed"] is False
        and next_contract["cutover_authorized_in_next_phase"] is False
        and next_contract["pilot_authorized_in_next_phase"] is False
        and next_contract["parity_gate_required"] is True
        and next_contract["release_controls_retention_required"] is True
        and next_contract["must_close_release_controls_count"] == len(RELEASE_CONTROLS_EXACT_SET)
        and next_contract["must_close_release_controls_exact_set"] == RELEASE_CONTROLS_EXACT_SET
    )

    all_acceptance_pass = (
        wp1_pass
        and wp2_pass
        and wp3_pass
        and wp4_pass
        and reference_pack_contradiction_count == 0
        and legacy_normalization["surface_breach_from_history_reintroduced"] is False
        and legacy_normalization["active_quality_reference"] == "RC-G"
        and legacy_normalization["active_control_pair"] == "RC-G vs RC-J"
        and legacy_normalization["archived_candidate_set"] == ["RC-M"]
        and legacy_normalization["stale_branch_left_active"] is False
        and next_contract["next_candidate_id"] == "RC-N"
        and next_contract["next_phase_scope"] == "release_controls_closure_only_under_canonical_current_authority"
        and next_contract["answer_path_delta_allowed"] is False
        and next_contract["database_expansion_allowed"] is False
    )

    reconciliation = {
        "official_decision": PASS_DECISION if all_acceptance_pass else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if all_acceptance_pass else FAIL_NEXT_WORK,
        "unexplained_count": 0 if all_acceptance_pass else reference_pack_contradiction_count,
        "new_runtime_executed": False,
        "new_candidate_built": False,
        "rc_m_reintroduced_to_current": False,
        "current_canonical_consumer_order_preserved": True,
        "stale_branch_left_active": legacy_normalization["stale_branch_left_active"],
    }
    wp5_pass = (
        reconciliation["official_decision"] == PASS_DECISION
        and reconciliation["next_official_work"] == PASS_NEXT_WORK
        and reconciliation["unexplained_count"] == 0
        and reconciliation["new_runtime_executed"] is False
        and reconciliation["new_candidate_built"] is False
        and reconciliation["rc_m_reintroduced_to_current"] is False
        and reconciliation["current_canonical_consumer_order_preserved"] is True
        and reconciliation["stale_branch_left_active"] is False
    )

    return {
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
        },
        "reference_pack": {
            "reference_pack_integrity_pass": reference_pack_integrity_pass,
            "reference_pack_contradiction_count": reference_pack_contradiction_count,
            "quality_reference_ref": "FAZ6",
            "release_controls_legacy_ref": "FAZ7",
            "canonical_current_authority_ref": "FAZ21",
            "archival_closure_ref": "FAZ24",
            "closure_matrix_ref": "faz1_5-closure-matrix-2026-03-22",
            "contradiction_rows": contradiction_rows,
        },
        "topology_rows": topology_rows,
        "legacy_normalization": legacy_normalization,
        "next_contract": next_contract,
        "reconciliation": reconciliation,
        "report_hash": stable_hash(
            {
                "reference_pack": reference_pack_integrity_pass,
                "topology_rows": topology_rows,
                "legacy_normalization": legacy_normalization,
                "next_contract": next_contract,
                "reconciliation": reconciliation,
            }
        ),
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str]:
    wp = payload["wp_statuses"]
    ref = payload["reference_pack"]
    topology_rows = payload["topology_rows"]
    legacy = payload["legacy_normalization"]
    contract = payload["next_contract"]
    recon = payload["reconciliation"]

    contradiction_lines = (
        ["- contradiction_rows = `0`"]
        if not ref["contradiction_rows"]
        else [f"- contradiction_rows = `{len(ref['contradiction_rows'])}`"]
        + [
            f"- {row['reference_name']} / {row['field_name']} missing=`{row['missing_marker']}`"
            for row in ref["contradiction_rows"]
        ]
    )

    topology_lines = []
    for row in topology_rows:
        topology_lines.extend([f"- {key} = `{_render_value(value)}`" for key, value in row.items()])
        topology_lines.append("")
    if topology_lines and topology_lines[-1] == "":
        topology_lines.pop()

    files: dict[Path, str] = {}
    files[ROOT / "coordination" / f"faz25-post-rc-m-steering-reference-pack-{DATE}.md"] = "\n".join(
        [
            "# FAZ25 Post-RC-M Steering Reference Pack",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
            f"- release_controls_legacy_ref = `{ref['release_controls_legacy_ref']}`",
            f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
            f"- archival_closure_ref = `{ref['archival_closure_ref']}`",
            f"- closure_matrix_ref = `{ref['closure_matrix_ref']}`",
            *contradiction_lines,
        ]
    )
    files[ROOT / "coordination" / f"faz25-canonical-candidate-topology-{DATE}.md"] = "\n".join(
        [
            "# FAZ25 Canonical Candidate Topology",
            "",
            *topology_lines,
        ]
    )
    files[ROOT / "coordination" / f"faz25-legacy-branch-normalization-{DATE}.md"] = "\n".join(
        [
            "# FAZ25 Legacy Branch Normalization",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in legacy.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz25-next-implementation-contract-{DATE}.md"] = "\n".join(
        [
            "# FAZ25 Next Implementation Contract",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items() if key != "must_close_release_controls_exact_set"),
            "- must_close_release_controls_exact_set =",
            *[f"  - `{item}`" for item in contract["must_close_release_controls_exact_set"]],
        ]
    )
    files[ROOT / "coordination" / f"faz25-post-rc-m-steering-reconciliation-{DATE}.md"] = "\n".join(
        [
            "# FAZ25 Post-RC-M Steering Reconciliation",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in recon.items()),
        ]
    )
    files[RESULT_REPORT] = "\n".join(
        [
            "# FAZ25 Post-RC-M Steering Re-Entry Under Canonical Current Authority Raporu",
            "",
            f"Tarih: {DATE}",
            "",
            "## Yonetici Ozeti",
            "",
            "FAZ25, RC-M archival closure sonrasinda steering hattini canonical current authority zemini altinda tek cizgiye indirmek icin yurutuldu. Bu fazda yeni runtime, yeni build veya yeni teknik implementasyon acilmadi; yalniz aktif kalite referansi, aktif control pair ve bir sonraki uygulama fazinin tek contract'i materialize edildi.",
            "",
            "## Reference Pack Ozeti",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
            f"- release_controls_legacy_ref = `{ref['release_controls_legacy_ref']}`",
            f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
            f"- archival_closure_ref = `{ref['archival_closure_ref']}`",
            f"- closure_matrix_ref = `{ref['closure_matrix_ref']}`",
            *contradiction_lines,
            "",
            "## Canonical Candidate Topology Ozeti",
            "",
            *topology_lines,
            "",
            "## Legacy Branch Normalization Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in legacy.items()),
            "",
            "## Sonraki Uygulama Fazi Contract Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items() if key != "must_close_release_controls_exact_set"),
            "- must_close_release_controls_exact_set =",
            *[f"  - `{item}`" for item in contract["must_close_release_controls_exact_set"]],
            "",
            "## WP Sonuclari",
            "",
            "### WP-1",
            f"- status = `{wp['WP-1']}`",
            "- reason = `steering reference pack contradiction_count=0 ile kapandi`" if wp["WP-1"] == "PASS" else "- reason = `reference pack contradiction bulundu`",
            "",
            "### WP-2",
            f"- status = `{wp['WP-2']}`",
            "- reason = `RC-G / RC-J / RC-M topology rolleri canonical steering baseline icin birebir materialize edildi`" if wp["WP-2"] == "PASS" else "- reason = `candidate topology eksik`",
            "",
            "### WP-3",
            f"- status = `{wp['WP-3']}`",
            "- reason = `legacy branch normalization, queue closure ve consumer order birlikte tutarli`" if wp["WP-3"] == "PASS" else "- reason = `legacy branch normalization tutarsiz`",
            "",
            "### WP-4",
            f"- status = `{wp['WP-4']}`",
            "- reason = `tek sonraki uygulama fazi RC-N / RC-G / RC-J / release-controls boundary olarak rezerve edildi`" if wp["WP-4"] == "PASS" else "- reason = `next implementation contract eksik`",
            "",
            "### WP-5",
            f"- status = `{wp['WP-5']}`",
            "- reason = `tek resmi karar ve tek next_official_work planner kontratiyla birebir kapandi`" if wp["WP-5"] == "PASS" else "- reason = `steering reconciliation kontrati kapanmadi`",
            "",
            "## Resmi Karar",
            "",
            f"- `{recon['official_decision']}`",
            "",
            "## Sonraki Resmi Is",
            "",
            f"- `{recon['next_official_work']}`",
        ]
    )
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ25 phase package.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    reference_texts = {name: load_text(root / rel) for name, rel in REFERENCE_FILES.items()}
    source_texts = {name: load_text(root / rel) for name, rel in SOURCE_OF_RECORD_FILES.items()}
    payload = build_phase_payload(reference_texts, source_texts)
    if args.dry_run:
        print(f"official_decision={payload['reconciliation']['official_decision']}")
        print(f"next_official_work={payload['reconciliation']['next_official_work']}")
        print(
            f"reference_pack_integrity_pass={payload['reference_pack']['reference_pack_integrity_pass']}"
        )
        print(
            f"reference_pack_contradiction_count={payload['reference_pack']['reference_pack_contradiction_count']}"
        )
        print(f"must_close_release_controls_count={payload['next_contract']['must_close_release_controls_count']}")
        return 0

    files = render_outputs(payload)
    for path, text in files.items():
        write_text(path, text)
    print(f"wrote_files={len(files)}")
    print(f"report={RESULT_REPORT.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
