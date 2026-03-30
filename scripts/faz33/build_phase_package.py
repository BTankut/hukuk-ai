#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz33_lib import (  # type: ignore
    DATE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    MUST_CLOSE_RELEASE_CONTROLS,
    PASS_DECISION,
    PASS_NEXT_WORK,
    PERIMETER_RULES,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    bool_text,
    load_text,
    stable_hash,
    write_text,
)


RESULT_REPORT_DOCS = ROOT / "docs" / RESULT_REPORT_NAME
RESULT_REPORT_REPORTS = ROOT / "reports" / RESULT_REPORT_NAME


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def build_phase_payload(reference_texts: dict[str, str]) -> dict[str, Any]:
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

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "canonical_current_authority_ref": "FAZ21",
        "post_rc_m_steering_ref": "FAZ25",
        "rc_n_boundary_root_cause_ref": "FAZ27",
        "rc_o_repair_truth_ref": "FAZ31",
        "rc_o_archival_closure_ref": "FAZ32",
        "contradiction_rows": contradiction_rows,
    }
    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
    )

    topology_rows = [
        {
            "candidate_id": "RC-G",
            "candidate_status": "accepted_quality_reference",
            "role": "quality_reference",
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
            "role": "control_diagnostic",
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
            "candidate_id": "RC-N",
            "candidate_status": "forensic_reference_candidate",
            "role": "forensic_reference",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "release_controls_boundary_forensics_reference_only",
        },
        {
            "candidate_id": "RC-M",
            "candidate_status": "discard_archived",
            "role": "historical_summary_archive",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "historical_archive_diagnostic_only",
        },
        {
            "candidate_id": "RC-O",
            "candidate_status": "discard_archived",
            "role": "historical_repair_archive",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
            "notes": "historical_repair_archive_diagnostic_only",
        },
    ]
    wp2_pass = (
        len(topology_rows) == 5
        and len({row["candidate_id"] for row in topology_rows}) == 5
        and sum(1 for row in topology_rows if row["current_authority_member"]) == 2
        and sum(1 for row in topology_rows if row["archived"]) == 2
    )

    legacy_normalization = {
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "active_repair_candidate": "NONE",
        "active_release_controls_candidate": "NONE",
        "active_cutover_candidate": "NONE",
        "active_pilot_candidate": "NONE",
        "archived_candidate_set": ["RC-M", "RC-O"],
        "stale_branch_set": ["RC-H", "RC-I", "RC-L"],
        "stale_branch_left_active": False,
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_consumer_order": "current_canonical -> historical_archive",
        "legacy_release_controls_pointer_normalized": True,
    }
    planner_denylist = {
        "planner_can_open_build_for_rc_m": False,
        "planner_can_open_patch_for_rc_m": False,
        "planner_can_open_repair_for_rc_m": False,
        "planner_can_open_replay_for_rc_m": False,
        "planner_can_open_recapture_for_rc_m": False,
        "planner_can_open_cutover_for_rc_m": False,
        "planner_can_open_pilot_for_rc_m": False,
        "planner_can_open_build_for_rc_o": False,
        "planner_can_open_patch_for_rc_o": False,
        "planner_can_open_repair_for_rc_o": False,
        "planner_can_open_replay_for_rc_o": False,
        "planner_can_open_recapture_for_rc_o": False,
        "planner_can_open_release_controls_reentry_for_rc_o": False,
        "planner_can_open_cutover_for_rc_o": False,
        "planner_can_open_pilot_for_rc_o": False,
    }
    wp3_pass = (
        legacy_normalization["stale_branch_left_active"] is False
        and legacy_normalization["surface_breach_from_history_reintroduced"] is False
        and legacy_normalization["active_quality_reference"] == "RC-G"
        and legacy_normalization["active_control_pair"] == "RC-G vs RC-J"
        and legacy_normalization["active_forensic_reference"] == "RC-N"
        and legacy_normalization["archived_candidate_set"] == ["RC-M", "RC-O"]
        and legacy_normalization["stale_branch_set"] == ["RC-H", "RC-I", "RC-L"]
        and all(value is False for value in planner_denylist.values())
    )

    next_phase_contract = {
        "next_candidate_id": "RC-P",
        "next_candidate_base": "RC-G",
        "next_candidate_control": "RC-J",
        "next_candidate_forensic_reference": "RC-N",
        "next_candidate_status": "reserved_not_built",
        "next_phase_scope": "release_controls_perimeter_isolation_only_under_canonical_current_authority",
        "allowed_diff_surface": "non_model_visible_release_controls_perimeter_only",
        "answer_path_delta_allowed": False,
        "model_request_payload_delta_allowed": False,
        "retrieval_request_delta_allowed": False,
        "assembled_context_delta_allowed": False,
        "preprojection_delta_allowed": False,
        "raw_answer_delta_allowed": False,
        "response_envelope_delta_allowed": False,
        "runtime_error_delta_allowed": False,
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
        "must_close_release_controls_count": len(MUST_CLOSE_RELEASE_CONTROLS),
        "must_close_release_controls_source": "faz1_5 + faz7 sources_of_record",
        "must_close_release_controls_exact_set": MUST_CLOSE_RELEASE_CONTROLS,
        "next_official_work": PASS_NEXT_WORK,
    }
    wp4_pass = (
        next_phase_contract["next_candidate_id"] == "RC-P"
        and next_phase_contract["next_phase_scope"]
        == "release_controls_perimeter_isolation_only_under_canonical_current_authority"
        and next_phase_contract["allowed_diff_surface"]
        == "non_model_visible_release_controls_perimeter_only"
        and next_phase_contract["answer_path_delta_allowed"] is False
        and next_phase_contract["database_expansion_allowed"] is False
        and next_phase_contract["cutover_authorized_in_next_phase"] is False
        and next_phase_contract["pilot_authorized_in_next_phase"] is False
        and next_phase_contract["must_close_release_controls_count"] == 10
    )

    acceptance_pass = wp1_pass and wp2_pass and wp3_pass and wp4_pass
    reconciliation = {
        "official_decision": PASS_DECISION if acceptance_pass else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if acceptance_pass else FAIL_NEXT_WORK,
        "unexplained_count": 0 if acceptance_pass else reference_pack["reference_pack_contradiction_count"],
        "stale_branch_left_active": legacy_normalization["stale_branch_left_active"],
        "surface_breach_from_history_reintroduced": legacy_normalization[
            "surface_breach_from_history_reintroduced"
        ],
        "new_runtime_executed": False,
        "new_candidate_built": False,
    }
    wp5_pass = (
        reconciliation["official_decision"] == PASS_DECISION
        and reconciliation["next_official_work"] == PASS_NEXT_WORK
        and reconciliation["unexplained_count"] == 0
    )

    report_hash = stable_hash(
        {
            "reference_pack": reference_pack,
            "topology_rows": topology_rows,
            "legacy_normalization": legacy_normalization,
            "planner_denylist": planner_denylist,
            "next_phase_contract": next_phase_contract,
            "perimeter_rules": PERIMETER_RULES,
            "reconciliation": reconciliation,
        }
    )

    return {
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
        },
        "reference_pack": reference_pack,
        "topology_rows": topology_rows,
        "legacy_normalization": legacy_normalization,
        "planner_denylist": planner_denylist,
        "next_phase_contract": next_phase_contract,
        "perimeter_rules": PERIMETER_RULES,
        "reconciliation": reconciliation,
        "report_hash": report_hash,
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str]:
    wp = payload["wp_statuses"]
    ref = payload["reference_pack"]
    topology = payload["topology_rows"]
    legacy = payload["legacy_normalization"]
    deny = payload["planner_denylist"]
    contract = payload["next_phase_contract"]
    rules = payload["perimeter_rules"]
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

    topology_lines: list[str] = []
    for row in topology:
        topology_lines.extend(f"- {key} = `{_render_value(value)}`" for key, value in row.items())
        topology_lines.append("")
    if topology_lines and topology_lines[-1] == "":
        topology_lines.pop()

    legacy_lines = [f"- {key} = `{_render_value(value)}`" for key, value in legacy.items()]
    deny_lines = [f"- {key} = `{_render_value(value)}`" for key, value in deny.items()]

    contract_lines = [f"- {key} = `{_render_value(value)}`" for key, value in contract.items()]

    perimeter_lines = [f"- {key} = `{_render_value(value)}`" for key, value in rules.items()]
    perimeter_lines.extend(
        [
            "",
            "- retrieval_change_allowed = `false`",
            "- prompt_change_allowed = `false`",
            "- model_change_allowed = `false`",
            "- corpus_change_allowed = `false`",
            "- guardrail_change_allowed = `false`",
            "- database_expansion_allowed = `false`",
            "- cutover = `false`",
            "- pilot = `false`",
        ]
    )

    files: dict[Path, str] = {}
    files[ROOT / "coordination" / f"faz33-official-implementation-plan-{DATE}.md"] = "\n".join(
        [
            "# FAZ33 Official Implementation Plan",
            "",
            "- phase_type = `steering_only`",
            "- runtime_execution = `disabled`",
            "- candidate_build_execution = `disabled`",
            "- patch_execution = `disabled`",
            "- replay_or_recapture_execution = `disabled`",
            "- cutover_or_pilot_execution = `disabled`",
            "- wp_order = `WP-1 reference pack -> WP-2 canonical topology -> WP-3 legacy/queue normalization -> WP-4 RC-P next phase contract -> WP-5 final reconciliation`",
            "- target_outcome = `single active topology + reserved RC-P perimeter isolation lane`",
        ]
    )
    files[ROOT / "coordination" / f"faz33-steering-decision-table-{DATE}.md"] = "\n".join(
        [
            "# FAZ33 Steering Decision Table",
            "",
            f"- WP-1 = `{wp['WP-1']}`",
            f"- WP-2 = `{wp['WP-2']}`",
            f"- WP-3 = `{wp['WP-3']}`",
            f"- WP-4 = `{wp['WP-4']}`",
            f"- WP-5 = `{wp['WP-5']}`",
            f"- official_decision = `{recon['official_decision']}`",
            f"- next_official_work = `{recon['next_official_work']}`",
            f"- report_hash = `{payload['report_hash']}`",
        ]
    )
    files[ROOT / "coordination" / f"faz33-reference-pack-{DATE}.md"] = "\n".join(
        [
            "# FAZ33 Reference Pack",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
            f"- post_rc_m_steering_ref = `{ref['post_rc_m_steering_ref']}`",
            f"- rc_n_boundary_root_cause_ref = `{ref['rc_n_boundary_root_cause_ref']}`",
            f"- rc_o_repair_truth_ref = `{ref['rc_o_repair_truth_ref']}`",
            f"- rc_o_archival_closure_ref = `{ref['rc_o_archival_closure_ref']}`",
            *contradiction_lines,
        ]
    )
    files[ROOT / "coordination" / f"faz33-canonical-candidate-topology-{DATE}.md"] = "\n".join(
        ["# FAZ33 Canonical Candidate Topology", "", *topology_lines]
    )
    files[ROOT / "coordination" / f"faz33-legacy-queue-normalization-{DATE}.md"] = "\n".join(
        ["# FAZ33 Legacy Queue Normalization", "", *legacy_lines, "", *deny_lines]
    )
    files[ROOT / "coordination" / f"faz33-rc-p-next-phase-contract-{DATE}.md"] = "\n".join(
        ["# FAZ33 RC-P Next Phase Contract", "", *contract_lines]
    )
    files[
        ROOT / "coordination" / f"faz33-release-controls-perimeter-isolation-rules-{DATE}.md"
    ] = "\n".join(
        ["# FAZ33 Release Controls Perimeter Isolation Rules", "", *perimeter_lines]
    )
    files[ROOT / "coordination" / f"faz33-final-reconciliation-summary-{DATE}.md"] = "\n".join(
        [
            "# FAZ33 Final Reconciliation Summary",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in recon.items()),
        ]
    )

    report_text = "\n".join(
        [
            "# FAZ33 POST-RC-O STEERING RE-ENTRY UNDER CANONICAL CURRENT AUTHORITY RAPORU",
            "",
            "## Yonetici Ozeti",
            "",
            "FAZ33, RC-O archival closure sonrasinda steering hattini canonical current authority altinda tek cizgiye indirmek ve bundan sonraki tek uygulama hattini RC-P perimeter isolation modeli olarak rezerve etmek icin yurutuldu. Bu fazda yeni runtime, yeni build, patch, replay, recapture, cutover veya pilot acilmadi.",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- stale_branch_left_active = `{bool_text(legacy['stale_branch_left_active'])}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(legacy['surface_breach_from_history_reintroduced'])}`",
            f"- next_candidate_id = `{contract['next_candidate_id']}`",
            f"- allowed_diff_surface = `{contract['allowed_diff_surface']}`",
            f"- answer_path_delta_allowed = `{bool_text(contract['answer_path_delta_allowed'])}`",
            f"- database_expansion_allowed = `{bool_text(contract['database_expansion_allowed'])}`",
            f"- cutover_authorized_in_next_phase = `{bool_text(contract['cutover_authorized_in_next_phase'])}`",
            f"- pilot_authorized_in_next_phase = `{bool_text(contract['pilot_authorized_in_next_phase'])}`",
            f"- unexplained_count = `{recon['unexplained_count']}`",
            "",
            "## Reference Pack Ozeti",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
            f"- post_rc_m_steering_ref = `{ref['post_rc_m_steering_ref']}`",
            f"- rc_n_boundary_root_cause_ref = `{ref['rc_n_boundary_root_cause_ref']}`",
            f"- rc_o_repair_truth_ref = `{ref['rc_o_repair_truth_ref']}`",
            f"- rc_o_archival_closure_ref = `{ref['rc_o_archival_closure_ref']}`",
            *contradiction_lines,
            "",
            "## Canonical Candidate Topology Ozeti",
            "",
            *topology_lines,
            "",
            "## Legacy / Queue Normalization Ozeti",
            "",
            *legacy_lines,
            *deny_lines,
            "",
            "## RC-P Next Phase Contract Ozeti",
            "",
            *contract_lines,
            *([""] + perimeter_lines),
            "",
            "## WP Sonuclari",
            "",
            "### WP-1",
            f"- status = `{wp['WP-1']}`",
            "- reason = `reference pack contradiction_count=0 ile FAZ21/25/26/27/28/29/30/31/32 zinciri exact kapandi`"
            if wp["WP-1"] == "PASS"
            else "- reason = `reference pack contradiction bulundu`",
            "",
            "### WP-2",
            f"- status = `{wp['WP-2']}`",
            "- reason = `RC-G / RC-J / RC-N / RC-M / RC-O topology rolleri exact ve cakismasiz materialize edildi`"
            if wp["WP-2"] == "PASS"
            else "- reason = `canonical candidate topology eksik veya cakismali`",
            "",
            "### WP-3",
            f"- status = `{wp['WP-3']}`",
            "- reason = `legacy queue state ve RC-M/RC-O denylist satirlari reopening yolu birakmadan normalize edildi`"
            if wp["WP-3"] == "PASS"
            else "- reason = `legacy queue normalization veya denylist state tutarsiz`",
            "",
            "### WP-4",
            f"- status = `{wp['WP-4']}`",
            "- reason = `RC-P perimeter isolation contract'i exact sabitlerle rezerve edildi ve model-gorunur diff tamamen yasaklandi`"
            if wp["WP-4"] == "PASS"
            else "- reason = `RC-P next phase contract exact kurallarla materialize edilemedi`",
            "",
            "### WP-5",
            f"- status = `{wp['WP-5']}`",
            "- reason = `tek resmi karar ve tek sonraki resmi is unexplained_count=0 ile birebir kapandi`"
            if wp["WP-5"] == "PASS"
            else "- reason = `final reconciliation resmi karar kontratini kapatamadi`",
            "",
            "## Resmi Karar",
            "",
            f"- official_decision = `{recon['official_decision']}`",
            f"- unexplained_count = `{recon['unexplained_count']}`",
            "",
            "## Sonraki Resmi Is",
            "",
            f"- next_official_work = `{recon['next_official_work']}`",
            "",
            "## Artefact Listesi",
            "",
            f"- `coordination/faz33-official-implementation-plan-{DATE}.md`",
            f"- `coordination/faz33-steering-decision-table-{DATE}.md`",
            f"- `coordination/faz33-reference-pack-{DATE}.md`",
            f"- `coordination/faz33-canonical-candidate-topology-{DATE}.md`",
            f"- `coordination/faz33-legacy-queue-normalization-{DATE}.md`",
            f"- `coordination/faz33-rc-p-next-phase-contract-{DATE}.md`",
            f"- `coordination/faz33-release-controls-perimeter-isolation-rules-{DATE}.md`",
            f"- `coordination/faz33-final-reconciliation-summary-{DATE}.md`",
            f"- `reports/{RESULT_REPORT_NAME}`",
            f"- `docs/{RESULT_REPORT_NAME}`",
        ]
    )
    files[RESULT_REPORT_DOCS] = report_text
    files[RESULT_REPORT_REPORTS] = report_text
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ33 phase package.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    reference_texts = {key: load_text(path) for key, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)

    if args.dry_run:
        print(f"official_decision={payload['reconciliation']['official_decision']}")
        print(f"next_official_work={payload['reconciliation']['next_official_work']}")
        print(
            f"reference_pack_integrity_pass={payload['reference_pack']['reference_pack_integrity_pass']}"
        )
        print(
            f"reference_pack_contradiction_count={payload['reference_pack']['reference_pack_contradiction_count']}"
        )
        print(f"report_hash={payload['report_hash']}")
        return 0

    files = render_outputs(payload)
    for path, text in files.items():
        write_text(path, text)
    print(f"wrote_files={len(files)}")
    print(f"report={RESULT_REPORT_DOCS.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
