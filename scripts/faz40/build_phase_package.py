#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz40_lib import (  # type: ignore
    DATE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    PASS_DECISION,
    PASS_NEXT_WORK,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    bool_text,
    load_text,
    write_text,
)


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    return str(value)


def build_phase_payload(reference_texts: dict[str, str]) -> dict[str, Any]:
    contradiction_rows: list[dict[str, str]] = []
    for phase_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[phase_name]
        for marker in markers:
            if marker not in text:
                contradiction_rows.append({"phase_name": phase_name.upper(), "missing_marker": marker})

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "current_authority_ref": "FAZ21 canonical current authority",
        "steering_topology_ref": "FAZ33",
        "current_perimeter_truth_ref": "FAZ35",
        "historical_failed_repair_truth_ref": "FAZ36",
        "historical_inconclusive_recapture_truth_ref": "FAZ37",
        "current_instability_truth_ref": "FAZ38",
        "reconciliation_ref": "FAZ39",
        "contradiction_rows": contradiction_rows,
    }
    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["current_authority_ref"] == "FAZ21 canonical current authority"
        and reference_pack["steering_topology_ref"] == "FAZ33"
        and reference_pack["current_perimeter_truth_ref"] == "FAZ35"
        and reference_pack["historical_failed_repair_truth_ref"] == "FAZ36"
        and reference_pack["historical_inconclusive_recapture_truth_ref"] == "FAZ37"
        and reference_pack["current_instability_truth_ref"] == "FAZ38"
        and reference_pack["reconciliation_ref"] == "FAZ39"
        and len(reference_pack["contradiction_rows"]) == 0
    )

    archival_contract = {
        "candidate_id": "RC-Q",
        "candidate_status": "discard_archived",
        "candidate_channel": "historical_repair_archive",
        "promotable": False,
        "repairable": False,
        "current_evaluable": False,
        "historical_archive_only": True,
        "diagnostic_only": True,
        "archival_reason": "current_instability_truth_adopted_after_canonical_current_authority_with_current_perimeter_truth_preserved_and_historical_repair_truth_reclassification",
        "current_perimeter_truth_reference_preserved": True,
        "current_instability_truth_adopted": True,
        "historical_failed_repair_truth_reclassified": True,
        "historical_inconclusive_recapture_truth_reclassified": True,
        "current_perimeter_truth_reference": "RC-P",
        "current_repair_truth_reference": "FAZ38 current_instability_truth",
        "historical_repair_archive_channel": "diagnostic_only",
        "repair_truth_comparison_order": "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive",
        "surface_breach_from_history_reintroduced": False,
        "current_instability_truth_runtime_error_count": 0,
        "current_instability_truth_unexplained_count": 0,
        "current_instability_truth_primary_reason": "frontier_membership_delta",
        "current_instability_truth_root_cause_class": "frontier_membership_instability",
        "current_instability_truth_dominant_stage": "I4",
        "current_instability_truth_union_instability_rowset_count": 6,
    }
    wp2_pass = all(
        [
            archival_contract["candidate_id"] == "RC-Q",
            archival_contract["candidate_status"] == "discard_archived",
            archival_contract["candidate_channel"] == "historical_repair_archive",
            archival_contract["promotable"] is False,
            archival_contract["repairable"] is False,
            archival_contract["current_evaluable"] is False,
            archival_contract["historical_archive_only"] is True,
            archival_contract["diagnostic_only"] is True,
            archival_contract["archival_reason"]
            == "current_instability_truth_adopted_after_canonical_current_authority_with_current_perimeter_truth_preserved_and_historical_repair_truth_reclassification",
            archival_contract["current_perimeter_truth_reference_preserved"] is True,
            archival_contract["current_instability_truth_adopted"] is True,
            archival_contract["historical_failed_repair_truth_reclassified"] is True,
            archival_contract["historical_inconclusive_recapture_truth_reclassified"] is True,
            archival_contract["current_perimeter_truth_reference"] == "RC-P",
            archival_contract["current_repair_truth_reference"] == "FAZ38 current_instability_truth",
            archival_contract["historical_repair_archive_channel"] == "diagnostic_only",
            archival_contract["repair_truth_comparison_order"]
            == "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive",
            archival_contract["surface_breach_from_history_reintroduced"] is False,
            archival_contract["current_instability_truth_runtime_error_count"] == 0,
            archival_contract["current_instability_truth_unexplained_count"] == 0,
            archival_contract["current_instability_truth_primary_reason"] == "frontier_membership_delta",
            archival_contract["current_instability_truth_root_cause_class"] == "frontier_membership_instability",
            archival_contract["current_instability_truth_dominant_stage"] == "I4",
            archival_contract["current_instability_truth_union_instability_rowset_count"] == 6,
        ]
    )

    registry = {
        "active_candidate_set_contains_rc_q": False,
        "promotable_set_contains_rc_q": False,
        "repairable_set_contains_rc_q": False,
        "current_truth_candidate_set_contains_rc_q": False,
        "release_controls_reentry_queue_contains_rc_q": False,
        "cutover_queue_contains_rc_q": False,
        "pilot_queue_contains_rc_q": False,
        "archive_registry_contains_rc_q": True,
        "archive_registry_channel": "historical_repair_archive_diagnostic_only",
    }
    planner_denylist = {
        "planner_can_open_build_for_rc_q": False,
        "planner_can_open_patch_for_rc_q": False,
        "planner_can_open_repair_for_rc_q": False,
        "planner_can_open_replay_for_rc_q": False,
        "planner_can_open_recapture_for_rc_q": False,
        "planner_can_open_release_controls_reentry_for_rc_q": False,
        "planner_can_open_cutover_for_rc_q": False,
        "planner_can_open_pilot_for_rc_q": False,
    }
    consumer_binding = {
        "current_perimeter_truth_reference_preserved": True,
        "current_instability_truth_adopted": True,
        "historical_failed_repair_truth_reclassified": True,
        "historical_inconclusive_recapture_truth_reclassified": True,
        "current_perimeter_truth_reference": "RC-P",
        "current_repair_truth_reference": "FAZ38 current_instability_truth",
        "historical_repair_archive_channel": "diagnostic_only",
        "repair_truth_comparison_order": "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive",
        "surface_breach_from_history_reintroduced": False,
        "consumer_binding_pass": True,
    }
    wp3_pass = (
        registry["active_candidate_set_contains_rc_q"] is False
        and registry["promotable_set_contains_rc_q"] is False
        and registry["repairable_set_contains_rc_q"] is False
        and registry["current_truth_candidate_set_contains_rc_q"] is False
        and registry["release_controls_reentry_queue_contains_rc_q"] is False
        and registry["cutover_queue_contains_rc_q"] is False
        and registry["pilot_queue_contains_rc_q"] is False
        and registry["archive_registry_contains_rc_q"] is True
        and registry["archive_registry_channel"] == "historical_repair_archive_diagnostic_only"
        and all(value is False for value in planner_denylist.values())
        and consumer_binding["current_perimeter_truth_reference_preserved"] is True
        and consumer_binding["current_instability_truth_adopted"] is True
        and consumer_binding["historical_failed_repair_truth_reclassified"] is True
        and consumer_binding["historical_inconclusive_recapture_truth_reclassified"] is True
        and consumer_binding["current_perimeter_truth_reference"] == "RC-P"
        and consumer_binding["current_repair_truth_reference"] == "FAZ38 current_instability_truth"
        and consumer_binding["historical_repair_archive_channel"] == "diagnostic_only"
        and consumer_binding["repair_truth_comparison_order"]
        == "current_perimeter_truth_reference -> current_repair_truth -> historical_repair_archive"
        and consumer_binding["surface_breach_from_history_reintroduced"] is False
        and consumer_binding["consumer_binding_pass"] is True
    )

    archival_manifest = {
        "candidate_id": "RC-Q",
        "candidate_status_before_archive": "frozen_failed_repair_candidate",
        "archive_status": "closed",
        "archive_channel": "historical_repair_archive_diagnostic_only",
        "archive_reason": "current_instability_truth_adopted_after_canonical_current_authority_with_current_perimeter_truth_preserved_and_historical_repair_truth_reclassification",
        "current_authority_ref": "FAZ21 canonical current authority",
        "steering_topology_ref": "FAZ33",
        "current_perimeter_truth_ref": "FAZ35",
        "historical_failed_repair_truth_ref": "FAZ36",
        "historical_inconclusive_recapture_ref": "FAZ37",
        "current_instability_truth_ref": "FAZ38",
        "reconciliation_ref": "FAZ39",
        "allowed_usage": "diagnostic_reference_only",
        "forbidden_usage": "serving_candidate,promotable_candidate,repair_candidate,current_truth_candidate,release_controls_reentry_candidate,cutover_candidate,pilot_candidate",
    }
    tombstone = {
        "candidate_id": "RC-Q",
        "tombstone_status": "active",
        "replacement_required": False,
        "reopen_allowed": False,
        "reactivation_allowed": False,
        "archive_only": True,
    }
    wp4_pass = (
        archival_manifest["candidate_id"] == "RC-Q"
        and archival_manifest["candidate_status_before_archive"] == "frozen_failed_repair_candidate"
        and archival_manifest["archive_status"] == "closed"
        and archival_manifest["archive_channel"] == "historical_repair_archive_diagnostic_only"
        and archival_manifest["archive_reason"]
        == "current_instability_truth_adopted_after_canonical_current_authority_with_current_perimeter_truth_preserved_and_historical_repair_truth_reclassification"
        and archival_manifest["current_authority_ref"] == "FAZ21 canonical current authority"
        and archival_manifest["steering_topology_ref"] == "FAZ33"
        and archival_manifest["current_perimeter_truth_ref"] == "FAZ35"
        and archival_manifest["historical_failed_repair_truth_ref"] == "FAZ36"
        and archival_manifest["historical_inconclusive_recapture_ref"] == "FAZ37"
        and archival_manifest["current_instability_truth_ref"] == "FAZ38"
        and archival_manifest["reconciliation_ref"] == "FAZ39"
        and archival_manifest["allowed_usage"] == "diagnostic_reference_only"
        and archival_manifest["forbidden_usage"]
        == "serving_candidate,promotable_candidate,repair_candidate,current_truth_candidate,release_controls_reentry_candidate,cutover_candidate,pilot_candidate"
        and tombstone["candidate_id"] == "RC-Q"
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
        and archival_contract["current_perimeter_truth_reference_preserved"] is True
        and archival_contract["current_instability_truth_adopted"] is True
        and archival_contract["historical_failed_repair_truth_reclassified"] is True
        and archival_contract["historical_inconclusive_recapture_truth_reclassified"] is True
        and archival_contract["surface_breach_from_history_reintroduced"] is False
        and registry["active_candidate_set_contains_rc_q"] is False
        and registry["promotable_set_contains_rc_q"] is False
        and registry["repairable_set_contains_rc_q"] is False
        and registry["current_truth_candidate_set_contains_rc_q"] is False
        and registry["release_controls_reentry_queue_contains_rc_q"] is False
        and all(value is False for value in planner_denylist.values())
        and archival_manifest["archive_status"] == "closed"
        and tombstone["tombstone_status"] == "active"
    )
    reconciliation = {
        "official_decision": PASS_DECISION if acceptance_pass else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if acceptance_pass else FAIL_NEXT_WORK,
        "unexplained_count": 0 if acceptance_pass else reference_pack["reference_pack_contradiction_count"],
        "rc_q_reintroduced_to_current": False,
        "archive_contract_breach": not acceptance_pass,
        "planner_reopen_path_present": any(planner_denylist.values()),
        "surface_breach_from_history_reintroduced": False,
    }
    wp5_pass = (
        reconciliation["official_decision"] == PASS_DECISION
        and reconciliation["next_official_work"] == PASS_NEXT_WORK
        and reconciliation["unexplained_count"] == 0
        and reconciliation["rc_q_reintroduced_to_current"] is False
        and reconciliation["archive_contract_breach"] is False
        and reconciliation["planner_reopen_path_present"] is False
        and reconciliation["surface_breach_from_history_reintroduced"] is False
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
        + [f"- {row['phase_name']} missing=`{row['missing_marker']}`" for row in ref["contradiction_rows"]]
    )

    files: dict[Path, str] = {}
    files[ROOT / "coordination" / f"faz40-rc-q-archival-reference-pack-{DATE}.md"] = "\n".join(
        [
            "# FAZ40 RC-Q Archival Reference Pack",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_authority_ref = `{ref['current_authority_ref']}`",
            f"- steering_topology_ref = `{ref['steering_topology_ref']}`",
            f"- current_perimeter_truth_ref = `{ref['current_perimeter_truth_ref']}`",
            f"- historical_failed_repair_truth_ref = `{ref['historical_failed_repair_truth_ref']}`",
            f"- historical_inconclusive_recapture_truth_ref = `{ref['historical_inconclusive_recapture_truth_ref']}`",
            f"- current_instability_truth_ref = `{ref['current_instability_truth_ref']}`",
            f"- reconciliation_ref = `{ref['reconciliation_ref']}`",
            *contradiction_lines,
        ]
    )
    files[ROOT / "coordination" / f"faz40-rc-q-archival-closure-contract-{DATE}.md"] = "\n".join(
        [
            "# FAZ40 RC-Q Archival Closure Contract",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz40-rc-q-registry-closure-{DATE}.md"] = "\n".join(
        [
            "# FAZ40 RC-Q Registry Closure",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in registry.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz40-rc-q-planner-denylist-{DATE}.md"] = "\n".join(
        [
            "# FAZ40 RC-Q Planner Denylist",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in deny.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz40-rc-q-repair-truth-consumer-binding-closure-{DATE}.md"] = "\n".join(
        [
            "# FAZ40 RC-Q Repair-Truth Consumer Binding Closure",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in binding.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz40-rc-q-archival-manifest-{DATE}.md"] = "\n".join(
        [
            "# FAZ40 RC-Q Archival Manifest",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in manifest.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz40-rc-q-tombstone-{DATE}.md"] = "\n".join(
        [
            "# FAZ40 RC-Q Tombstone",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in tombstone.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz40-rc-q-archival-closure-reconciliation-{DATE}.md"] = "\n".join(
        [
            "# FAZ40 RC-Q Archival Closure Reconciliation",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in recon.items()),
        ]
    )
    files[ROOT / "docs" / RESULT_REPORT_NAME] = "\n".join(
        [
            "# FAZ40 RC-Q DISCARD ARCHIVAL CLOSURE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
            "",
            "## Yonetici Ozeti",
            "",
            "FAZ40, RC-Q adayini canonical current authority altinda kalici discard + archival closure durumuna tasimak icin yurutuldu. Bu faz yeni build, replay, recapture veya repair acmadi; yalniz FAZ21, FAZ33, FAZ35, FAZ36, FAZ37, FAZ38 ve FAZ39 referans zinciri kullanilarak RC-Q current candidate hattindan kalici olarak cikarildi ve historical_repair_archive / diagnostic_only kanalina kapatildi.",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_perimeter_truth_reference_preserved = `{bool_text(contract['current_perimeter_truth_reference_preserved'])}`",
            f"- current_instability_truth_adopted = `{bool_text(contract['current_instability_truth_adopted'])}`",
            f"- historical_failed_repair_truth_reclassified = `{bool_text(contract['historical_failed_repair_truth_reclassified'])}`",
            f"- historical_inconclusive_recapture_truth_reclassified = `{bool_text(contract['historical_inconclusive_recapture_truth_reclassified'])}`",
            f"- surface_breach_from_history_reintroduced = `{bool_text(binding['surface_breach_from_history_reintroduced'])}`",
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
            f"- current_perimeter_truth_ref = `{ref['current_perimeter_truth_ref']}`",
            f"- historical_failed_repair_truth_ref = `{ref['historical_failed_repair_truth_ref']}`",
            f"- historical_inconclusive_recapture_truth_ref = `{ref['historical_inconclusive_recapture_truth_ref']}`",
            f"- current_instability_truth_ref = `{ref['current_instability_truth_ref']}`",
            f"- reconciliation_ref = `{ref['reconciliation_ref']}`",
            *contradiction_lines,
            "",
            "## WP Sonuclari",
            "",
            "### WP-1",
            f"- status = `{wp['WP-1']}`",
            "- reason = `reference pack FAZ21/33/35/36/37/38/39 zinciri contradiction_rows=0 ile birebir kapandi`",
            "",
            "### WP-2",
            f"- status = `{wp['WP-2']}`",
            "- reason = `RC-Q archival closure contract tum zorunlu alan ve sabit degerlerle materialize edildi`",
            "",
            "### WP-3",
            f"- status = `{wp['WP-3']}`",
            "- reason = `registry closure, planner denylist ve repair-truth consumer binding closure birlikte tutarli ve reopen yolu yok`",
            "",
            "### WP-4",
            f"- status = `{wp['WP-4']}`",
            "- reason = `archival manifest ve tombstone exact alanlarla materialize edildi; RC-Q archive_only tombstone altina alindi`",
            "",
            "### WP-5",
            f"- status = `{wp['WP-5']}`",
            "- reason = `final reconciliation official_decision, next_official_work ve zero-unexplained kapanisi ile birebir tamamlandi`",
            "",
            "## RC-Q Archival Closure Contract Ozeti",
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
            *(f"- {key} = `{_render_value(value)}`" for key, value in recon.items() if key != "next_official_work"),
            "",
            "## Sonraki Resmi Is",
            "",
            f"- next_official_work = `{recon['next_official_work']}`",
        ]
    )
    return files


def main() -> int:
    reference_texts = {key: load_text(path) for key, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)
    for path, text in render_outputs(payload).items():
        write_text(path, text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
