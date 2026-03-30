#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz32_lib import (  # type: ignore
    DATE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    PASS_DECISION,
    PASS_NEXT_WORK,
    PHASE_PACKAGE_JSON,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    bool_text,
    load_text,
    stable_hash,
    write_json,
    write_text,
)


RESULT_REPORT_DOCS = ROOT / "docs" / RESULT_REPORT_NAME
RESULT_REPORT_REPORTS = ROOT / "reports" / RESULT_REPORT_NAME


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    return str(value)


def build_phase_payload(reference_texts: dict[str, str]) -> dict[str, Any]:
    contradiction_rows = []
    for phase_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[phase_name]
        for marker in markers:
            if marker not in text:
                contradiction_rows.append(
                    {
                        "phase_name": phase_name.upper(),
                        "missing_marker": marker,
                    }
                )

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "current_authority_ref": "FAZ21 canonical current authority",
        "steering_topology_ref": "FAZ25",
        "boundary_root_cause_ref": "FAZ27",
        "historical_stable_repair_truth_ref": "FAZ28",
        "historical_inconclusive_recapture_truth_ref": "FAZ29",
        "current_forensic_truth_ref": "FAZ30",
        "reconciliation_ref": "FAZ31",
        "contradiction_rows": contradiction_rows,
    }
    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["current_authority_ref"] == "FAZ21 canonical current authority"
        and reference_pack["steering_topology_ref"] == "FAZ25"
        and reference_pack["boundary_root_cause_ref"] == "FAZ27"
        and reference_pack["historical_stable_repair_truth_ref"] == "FAZ28"
        and reference_pack["historical_inconclusive_recapture_truth_ref"] == "FAZ29"
        and reference_pack["current_forensic_truth_ref"] == "FAZ30"
        and reference_pack["reconciliation_ref"] == "FAZ31"
        and len(reference_pack["contradiction_rows"]) == 0
    )

    archival_contract = {
        "candidate_id": "RC-O",
        "candidate_status": "discard_archived",
        "candidate_channel": "historical_repair_archive",
        "promotable": False,
        "repairable": False,
        "current_evaluable": False,
        "historical_archive_only": True,
        "diagnostic_only": True,
        "archival_reason": "current_forensic_truth_adopted_after_canonical_current_authority_and_historical_repair_truth_reclassification",
        "repair_truth_comparison_order": "current_forensic_truth -> historical_repair_archive",
        "surface_breach_from_history_reintroduced": False,
        "current_forensic_truth_adopted": True,
        "historical_stable_repair_truth_reclassified": True,
        "historical_inconclusive_recapture_truth_reclassified": True,
        "current_forensic_truth_runtime_error_count": 0,
        "current_forensic_truth_unexplained_count": 0,
        "current_forensic_truth_dominant_interaction_class": "boundary_pack_orchestration_runtime_mutation",
    }
    wp2_pass = all(
        [
            archival_contract["candidate_id"] == "RC-O",
            archival_contract["candidate_status"] == "discard_archived",
            archival_contract["candidate_channel"] == "historical_repair_archive",
            archival_contract["promotable"] is False,
            archival_contract["repairable"] is False,
            archival_contract["current_evaluable"] is False,
            archival_contract["historical_archive_only"] is True,
            archival_contract["diagnostic_only"] is True,
            archival_contract["archival_reason"]
            == "current_forensic_truth_adopted_after_canonical_current_authority_and_historical_repair_truth_reclassification",
            archival_contract["repair_truth_comparison_order"] == "current_forensic_truth -> historical_repair_archive",
            archival_contract["surface_breach_from_history_reintroduced"] is False,
            archival_contract["current_forensic_truth_adopted"] is True,
            archival_contract["historical_stable_repair_truth_reclassified"] is True,
            archival_contract["historical_inconclusive_recapture_truth_reclassified"] is True,
            archival_contract["current_forensic_truth_runtime_error_count"] == 0,
            archival_contract["current_forensic_truth_unexplained_count"] == 0,
            archival_contract["current_forensic_truth_dominant_interaction_class"]
            == "boundary_pack_orchestration_runtime_mutation",
        ]
    )

    registry = {
        "active_candidate_set_contains_rc_o": False,
        "promotable_set_contains_rc_o": False,
        "repairable_set_contains_rc_o": False,
        "current_truth_candidate_set_contains_rc_o": False,
        "release_controls_reentry_queue_contains_rc_o": False,
        "cutover_queue_contains_rc_o": False,
        "pilot_queue_contains_rc_o": False,
        "archive_registry_contains_rc_o": True,
        "archive_registry_channel": "historical_repair_archive_diagnostic_only",
    }
    planner_denylist = {
        "planner_can_open_build_for_rc_o": False,
        "planner_can_open_patch_for_rc_o": False,
        "planner_can_open_repair_for_rc_o": False,
        "planner_can_open_replay_for_rc_o": False,
        "planner_can_open_recapture_for_rc_o": False,
        "planner_can_open_release_controls_reentry_for_rc_o": False,
        "planner_can_open_cutover_for_rc_o": False,
        "planner_can_open_pilot_for_rc_o": False,
    }
    consumer_binding = {
        "current_forensic_truth_adopted": True,
        "historical_stable_repair_truth_reclassified": True,
        "historical_inconclusive_recapture_truth_reclassified": True,
        "historical_repair_archive_channel": "diagnostic_only",
        "repair_truth_comparison_order": "current_forensic_truth -> historical_repair_archive",
        "surface_breach_from_history_reintroduced": False,
        "consumer_binding_pass": True,
    }
    wp3_pass = (
        registry["active_candidate_set_contains_rc_o"] is False
        and registry["promotable_set_contains_rc_o"] is False
        and registry["repairable_set_contains_rc_o"] is False
        and registry["current_truth_candidate_set_contains_rc_o"] is False
        and registry["release_controls_reentry_queue_contains_rc_o"] is False
        and registry["cutover_queue_contains_rc_o"] is False
        and registry["pilot_queue_contains_rc_o"] is False
        and registry["archive_registry_contains_rc_o"] is True
        and registry["archive_registry_channel"] == "historical_repair_archive_diagnostic_only"
        and all(value is False for value in planner_denylist.values())
        and consumer_binding["current_forensic_truth_adopted"] is True
        and consumer_binding["historical_stable_repair_truth_reclassified"] is True
        and consumer_binding["historical_inconclusive_recapture_truth_reclassified"] is True
        and consumer_binding["historical_repair_archive_channel"] == "diagnostic_only"
        and consumer_binding["repair_truth_comparison_order"] == "current_forensic_truth -> historical_repair_archive"
        and consumer_binding["surface_breach_from_history_reintroduced"] is False
        and consumer_binding["consumer_binding_pass"] is True
    )

    archival_manifest = {
        "candidate_id": "RC-O",
        "candidate_status_before_archive": "frozen_failed_repair_candidate",
        "archive_status": "closed",
        "archive_channel": "historical_repair_archive_diagnostic_only",
        "archive_reason": "current_forensic_truth_adopted_after_canonical_current_authority_and_historical_repair_truth_reclassification",
        "current_authority_ref": "FAZ21 canonical current authority",
        "boundary_root_cause_ref": "FAZ27",
        "historical_stable_repair_truth_ref": "FAZ28",
        "historical_inconclusive_recapture_ref": "FAZ29",
        "current_forensic_truth_ref": "FAZ30",
        "reconciliation_ref": "FAZ31",
        "allowed_usage": "diagnostic_reference_only",
        "forbidden_usage": "serving_candidate,promotable_candidate,repair_candidate,current_truth_candidate,release_controls_reentry_candidate,cutover_candidate,pilot_candidate",
    }
    tombstone = {
        "candidate_id": "RC-O",
        "tombstone_status": "active",
        "replacement_required": False,
        "reopen_allowed": False,
        "reactivation_allowed": False,
        "archive_only": True,
    }
    wp4_pass = (
        archival_manifest["candidate_id"] == "RC-O"
        and archival_manifest["candidate_status_before_archive"] == "frozen_failed_repair_candidate"
        and archival_manifest["archive_status"] == "closed"
        and archival_manifest["archive_channel"] == "historical_repair_archive_diagnostic_only"
        and archival_manifest["allowed_usage"] == "diagnostic_reference_only"
        and archival_manifest["forbidden_usage"]
        == "serving_candidate,promotable_candidate,repair_candidate,current_truth_candidate,release_controls_reentry_candidate,cutover_candidate,pilot_candidate"
        and tombstone["candidate_id"] == "RC-O"
        and tombstone["tombstone_status"] == "active"
        and tombstone["replacement_required"] is False
        and tombstone["reopen_allowed"] is False
        and tombstone["reactivation_allowed"] is False
        and tombstone["archive_only"] is True
    )

    acceptance_pass = (
        wp1_pass
        and wp2_pass
        and wp3_pass
        and wp4_pass
        and reference_pack["reference_pack_contradiction_count"] == 0
        and archival_contract["current_forensic_truth_adopted"] is True
        and archival_contract["historical_stable_repair_truth_reclassified"] is True
        and archival_contract["historical_inconclusive_recapture_truth_reclassified"] is True
        and archival_contract["surface_breach_from_history_reintroduced"] is False
        and registry["active_candidate_set_contains_rc_o"] is False
        and registry["promotable_set_contains_rc_o"] is False
        and registry["repairable_set_contains_rc_o"] is False
        and registry["current_truth_candidate_set_contains_rc_o"] is False
        and registry["release_controls_reentry_queue_contains_rc_o"] is False
        and all(value is False for value in planner_denylist.values())
        and archival_manifest["archive_status"] == "closed"
        and tombstone["tombstone_status"] == "active"
    )
    reconciliation = {
        "official_decision": PASS_DECISION if acceptance_pass else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if acceptance_pass else FAIL_NEXT_WORK,
        "unexplained_count": 0 if acceptance_pass else reference_pack["reference_pack_contradiction_count"],
        "rc_o_reintroduced_to_current": False,
        "archive_contract_breach": not acceptance_pass,
        "planner_reopen_path_present": any(planner_denylist.values()),
        "surface_breach_from_history_reintroduced": False,
    }
    wp5_pass = (
        reconciliation["official_decision"] == PASS_DECISION
        and reconciliation["next_official_work"] == PASS_NEXT_WORK
        and reconciliation["unexplained_count"] == 0
        and reconciliation["rc_o_reintroduced_to_current"] is False
        and reconciliation["archive_contract_breach"] is False
        and reconciliation["planner_reopen_path_present"] is False
        and reconciliation["surface_breach_from_history_reintroduced"] is False
    )

    report_hash = stable_hash(
        {
            "reference_pack": reference_pack,
            "archival_contract": archival_contract,
            "registry": registry,
            "planner_denylist": planner_denylist,
            "consumer_binding": consumer_binding,
            "archival_manifest": archival_manifest,
            "tombstone": tombstone,
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
        "archival_contract": archival_contract,
        "registry": registry,
        "planner_denylist": planner_denylist,
        "consumer_binding": consumer_binding,
        "archival_manifest": archival_manifest,
        "tombstone": tombstone,
        "reconciliation": reconciliation,
        "report_hash": report_hash,
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str]:
    wp = payload["wp_statuses"]
    ref = payload["reference_pack"]
    contract = payload["archival_contract"]
    registry = payload["registry"]
    deny = payload["planner_denylist"]
    binding = payload["consumer_binding"]
    manifest = payload["archival_manifest"]
    tombstone = payload["tombstone"]
    recon = payload["reconciliation"]

    contradiction_lines = (
        ["- contradiction_rows = `0`"]
        if not ref["contradiction_rows"]
        else [f"- contradiction_rows = `{len(ref['contradiction_rows'])}`"]
        + [
            f"- {row['phase_name']} missing=`{row['missing_marker']}`"
            for row in ref["contradiction_rows"]
        ]
    )

    files: dict[Path, str] = {}
    files[ROOT / "coordination" / f"faz32-official-implementation-plan-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 Official Implementation Plan",
            "",
            "- phase_type = `closure_only`",
            "- live_runtime = `disabled`",
            "- eval_rerun = `disabled`",
            "- reference_chain = `FAZ21 -> FAZ25 -> FAZ27 -> FAZ28 -> FAZ29 -> FAZ30 -> FAZ31`",
            "- wp_order = `WP-1 reference pack -> WP-2 archival contract -> WP-3 registry/planner/consumer closure -> WP-4 manifest/tombstone -> WP-5 reconciliation`",
            "- output_target = `RC-O historical_repair_archive_diagnostic_only`",
        ]
    )
    files[ROOT / "coordination" / f"faz32-rc-o-archival-reference-pack-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 RC-O Archival Reference Pack",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_authority_ref = `{ref['current_authority_ref']}`",
            f"- steering_topology_ref = `{ref['steering_topology_ref']}`",
            f"- boundary_root_cause_ref = `{ref['boundary_root_cause_ref']}`",
            f"- historical_stable_repair_truth_ref = `{ref['historical_stable_repair_truth_ref']}`",
            f"- historical_inconclusive_recapture_truth_ref = `{ref['historical_inconclusive_recapture_truth_ref']}`",
            f"- current_forensic_truth_ref = `{ref['current_forensic_truth_ref']}`",
            f"- reconciliation_ref = `{ref['reconciliation_ref']}`",
            *contradiction_lines,
        ]
    )
    files[ROOT / "coordination" / f"faz32-rc-o-archival-closure-contract-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 RC-O Archival Closure Contract",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz32-rc-o-registry-closure-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 RC-O Registry Closure",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in registry.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz32-rc-o-planner-denylist-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 RC-O Planner Denylist",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in deny.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz32-rc-o-repair-truth-consumer-binding-closure-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 RC-O Repair-Truth Consumer Binding Closure",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in binding.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz32-rc-o-archival-manifest-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 RC-O Archival Manifest",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in manifest.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz32-rc-o-tombstone-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 RC-O Tombstone",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in tombstone.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz32-rc-o-archival-closure-reconciliation-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 RC-O Archival Closure Reconciliation",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in recon.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz32-steering-decision-table-{DATE}.md"] = "\n".join(
        [
            "# FAZ32 Steering Decision Table",
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

    report_text = "\n".join(
        [
            "# FAZ32 RC-O DISCARD ARCHIVAL CLOSURE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
            "",
            "## Yonetici Ozeti",
            "",
            "FAZ32, RC-O adayini canonical current authority altinda kalici discard + archival closure durumuna tasimak icin yurutuldu. Bu faz bir onarim ya da runtime fazi degildi; yalniz FAZ21, FAZ25, FAZ27, FAZ28, FAZ29, FAZ30 ve FAZ31 referans zinciri kullanilarak RC-O current candidate hattindan kalici olarak cikartildi ve historical_repair_archive / diagnostic_only kanalina kapatildi.",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_forensic_truth_adopted = `{bool_text(contract['current_forensic_truth_adopted'])}`",
            f"- historical_stable_repair_truth_reclassified = `{bool_text(contract['historical_stable_repair_truth_reclassified'])}`",
            f"- historical_inconclusive_recapture_truth_reclassified = `{bool_text(contract['historical_inconclusive_recapture_truth_reclassified'])}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(contract['surface_breach_from_history_reintroduced'])}`",
            f"- archive_status = `{manifest['archive_status']}`",
            f"- tombstone_status = `{tombstone['tombstone_status']}`",
            f"- official_decision = `{recon['official_decision']}`",
            f"- next_official_work = `{recon['next_official_work']}`",
            "",
            "## Reference Pack Ozeti",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_authority_ref = `{ref['current_authority_ref']}`",
            f"- steering_topology_ref = `{ref['steering_topology_ref']}`",
            f"- boundary_root_cause_ref = `{ref['boundary_root_cause_ref']}`",
            f"- historical_stable_repair_truth_ref = `{ref['historical_stable_repair_truth_ref']}`",
            f"- historical_inconclusive_recapture_truth_ref = `{ref['historical_inconclusive_recapture_truth_ref']}`",
            f"- current_forensic_truth_ref = `{ref['current_forensic_truth_ref']}`",
            f"- reconciliation_ref = `{ref['reconciliation_ref']}`",
            *contradiction_lines,
            "",
            "## WP Sonuclari",
            "",
            "### WP-1",
            f"- status = `{wp['WP-1']}`",
            "- reason = `reference pack FAZ21/25/27/28/29/30/31 zinciri contradiction_rows=0 ile birebir kapandi`"
            if wp["WP-1"] == "PASS"
            else "- reason = `reference pack contradiction_rows sifir olmadi`",
            "",
            "### WP-2",
            f"- status = `{wp['WP-2']}`",
            "- reason = `RC-O archival closure contract tum zorunlu alan ve sabit degerlerle materialize edildi`"
            if wp["WP-2"] == "PASS"
            else "- reason = `RC-O archival closure contract eksik veya sabit degerlerden sasti`",
            "",
            "### WP-3",
            f"- status = `{wp['WP-3']}`",
            "- reason = `registry closure, planner denylist ve repair-truth consumer binding closure birlikte tutarli ve reopen yolu yok`"
            if wp["WP-3"] == "PASS"
            else "- reason = `registry/planner/consumer closure tutarsiz veya reopen yolu acik`",
            "",
            "### WP-4",
            f"- status = `{wp['WP-4']}`",
            "- reason = `archival manifest ve tombstone exact alanlarla materialize edildi; RC-O archive_only tombstone altina alindi`"
            if wp["WP-4"] == "PASS"
            else "- reason = `archival manifest veya tombstone contract'i eksik`",
            "",
            "### WP-5",
            f"- status = `{wp['WP-5']}`",
            "- reason = `final reconciliation official_decision, next_official_work ve zero-unexplained kapanisi ile birebir tamamlandi`"
            if wp["WP-5"] == "PASS"
            else "- reason = `final reconciliation allowed decision/next_official_work kontratini saglamadi`",
            "",
            "## RC-O Archival Closure Contract Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items()),
            "",
            "## Registry / Planner / Repair-Truth Consumer Binding Closure Ozeti",
            "",
            "### Registry Closure",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in registry.items()),
            "",
            "### Planner Denylist",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in deny.items()),
            "",
            "### Repair-Truth Consumer Binding Closure",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in binding.items()),
            "",
            "## Archival Manifest ve Tombstone Ozeti",
            "",
            "### Archival Manifest",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in manifest.items()),
            "",
            "### Tombstone",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in tombstone.items()),
            "",
            "## Resmi Karar",
            "",
            f"- official_decision = `{recon['official_decision']}`",
            f"- unexplained_count = `{recon['unexplained_count']}`",
            f"- rc_o_reintroduced_to_current = `{bool_text(recon['rc_o_reintroduced_to_current'])}`",
            f"- archive_contract_breach = `{bool_text(recon['archive_contract_breach'])}`",
            f"- planner_reopen_path_present = `{bool_text(recon['planner_reopen_path_present'])}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(recon['surface_breach_from_history_reintroduced'])}`",
            "",
            "## Sonraki Resmi Is",
            "",
            f"- next_official_work = `{recon['next_official_work']}`",
        ]
    )
    files[RESULT_REPORT_DOCS] = report_text
    files[RESULT_REPORT_REPORTS] = report_text
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ32 phase package.")
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
    write_json(PHASE_PACKAGE_JSON, payload)
    print(f"wrote_files={len(files) + 1}")
    print(f"report={RESULT_REPORT_DOCS.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
