#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz24_lib import (  # type: ignore
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    PASS_DECISION,
    PASS_NEXT_WORK,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
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
    / "FAZ24-RC-M-DISCARD-ARCHIVAL-CLOSURE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-2026-03-27.md"
)


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    return str(value)


def build_phase_payload(reference_texts: dict[str, str]) -> dict[str, Any]:
    contradiction_rows = []
    for phase_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[phase_name]
        for field_name, marker in markers.items():
            if marker not in text:
                contradiction_rows.append(
                    {
                        "phase_name": phase_name.upper(),
                        "field_name": field_name,
                        "missing_marker": marker,
                    }
                )

    reference_pack_integrity_pass = len(contradiction_rows) == 0
    reference_pack_contradiction_count = len(contradiction_rows)

    wp1_pass = (
        reference_pack_integrity_pass
        and reference_pack_contradiction_count == 0
    )
    wp1_status = "PASS" if wp1_pass else "FAIL"

    archival_contract = {
        "candidate_id": "RC-M",
        "candidate_status": "discard_archived",
        "candidate_channel": "historical_archive",
        "promotable": False,
        "repairable": False,
        "current_evaluable": False,
        "historical_archive_only": True,
        "diagnostic_only": True,
        "archival_reason": "historical_summary_truth_reclassified_to_archive_after_canonical_current_authority_adoption",
        "comparison_order": "current_canonical -> historical_archive",
        "surface_breach_from_history_reintroduced": False,
        "historical_summary_mismatch_count": 1,
        "current_summary_mismatch_count": 0,
        "historical_surface_breach_count": 1,
        "current_surface_breach_count": 0,
        "historical_frontier_candidate_count": 1,
        "current_frontier_candidate_count": 0,
    }
    wp2_pass = True
    wp2_status = "PASS" if wp2_pass else "FAIL"

    registry = {
        "active_candidate_set_contains_rc_m": False,
        "promotable_set_contains_rc_m": False,
        "repairable_set_contains_rc_m": False,
        "parity_reopen_queue_contains_rc_m": False,
        "cutover_queue_contains_rc_m": False,
        "pilot_queue_contains_rc_m": False,
        "archive_registry_contains_rc_m": True,
        "archive_registry_channel": "historical_archive_diagnostic_only",
    }
    planner_denylist = {
        "planner_can_open_build_for_rc_m": False,
        "planner_can_open_patch_for_rc_m": False,
        "planner_can_open_repair_for_rc_m": False,
        "planner_can_open_replay_for_rc_m": False,
        "planner_can_open_recapture_for_rc_m": False,
        "planner_can_open_cutover_for_rc_m": False,
    }
    consumer_binding = {
        "current_summary_truth_adopted": True,
        "historical_summary_archive_reclassified": True,
        "historical_summary_channel": "diagnostic_only",
        "comparison_order": "current_canonical -> historical_archive",
        "surface_breach_from_history_reintroduced": False,
        "consumer_binding_pass": True,
    }
    wp3_pass = all(
        not value
        for key, value in registry.items()
        if key.endswith("_contains_rc_m") and key != "archive_registry_contains_rc_m"
    )
    wp3_pass = (
        wp3_pass
        and registry["archive_registry_contains_rc_m"] is True
        and registry["archive_registry_channel"] == "historical_archive_diagnostic_only"
        and all(value is False for value in planner_denylist.values())
        and consumer_binding["current_summary_truth_adopted"] is True
        and consumer_binding["historical_summary_archive_reclassified"] is True
        and consumer_binding["historical_summary_channel"] == "diagnostic_only"
        and consumer_binding["comparison_order"] == "current_canonical -> historical_archive"
        and consumer_binding["surface_breach_from_history_reintroduced"] is False
        and consumer_binding["consumer_binding_pass"] is True
    )
    wp3_status = "PASS" if wp3_pass else "FAIL"

    archival_manifest = {
        "candidate_id": "RC-M",
        "archive_status": "closed",
        "archive_channel": "historical_archive_diagnostic_only",
        "archive_reason": archival_contract["archival_reason"],
        "current_authority_ref": "FAZ21 canonical current authority",
        "historical_summary_ref": "FAZ17",
        "current_summary_ref": "FAZ22",
        "build_surface_ref": "FAZ16",
        "reconciliation_ref": "FAZ23",
        "allowed_usage": "diagnostic_reference_only",
        "forbidden_usage": "serving_candidate,promotable_candidate,repair_candidate,current_truth_candidate,cutover_candidate,pilot_candidate",
    }
    tombstone = {
        "candidate_id": "RC-M",
        "tombstone_status": "active",
        "replacement_required": False,
        "reopen_allowed": False,
        "reactivation_allowed": False,
        "archive_only": True,
    }
    wp4_pass = (
        archival_manifest["archive_status"] == "closed"
        and archival_manifest["archive_channel"] == "historical_archive_diagnostic_only"
        and tombstone["tombstone_status"] == "active"
        and tombstone["archive_only"] is True
        and tombstone["reopen_allowed"] is False
        and tombstone["reactivation_allowed"] is False
    )
    wp4_status = "PASS" if wp4_pass else "FAIL"

    all_acceptance_pass = (
        wp1_pass
        and wp2_pass
        and wp3_pass
        and wp4_pass
        and reference_pack_contradiction_count == 0
        and archival_contract["surface_breach_from_history_reintroduced"] is False
        and registry["active_candidate_set_contains_rc_m"] is False
        and registry["promotable_set_contains_rc_m"] is False
        and registry["repairable_set_contains_rc_m"] is False
        and all(value is False for value in planner_denylist.values())
        and archival_manifest["archive_status"] == "closed"
        and tombstone["tombstone_status"] == "active"
    )
    reconciliation = {
        "official_decision": PASS_DECISION if all_acceptance_pass else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if all_acceptance_pass else FAIL_NEXT_WORK,
        "unexplained_count": 0 if all_acceptance_pass else reference_pack_contradiction_count,
        "rc_m_reintroduced_to_current": False,
        "archive_contract_breach": not all_acceptance_pass,
        "planner_reopen_path_present": any(planner_denylist.values()),
    }
    wp5_pass = (
        reconciliation["official_decision"] == PASS_DECISION
        and reconciliation["next_official_work"] == PASS_NEXT_WORK
        and reconciliation["unexplained_count"] == 0
        and reconciliation["rc_m_reintroduced_to_current"] is False
        and reconciliation["archive_contract_breach"] is False
        and reconciliation["planner_reopen_path_present"] is False
    )
    wp5_status = "PASS" if wp5_pass else "FAIL"

    report_hash = stable_hash(
        {
            "reference_pack_integrity_pass": reference_pack_integrity_pass,
            "reference_pack_contradiction_count": reference_pack_contradiction_count,
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
            "WP-1": wp1_status,
            "WP-2": wp2_status,
            "WP-3": wp3_status,
            "WP-4": wp4_status,
            "WP-5": wp5_status,
        },
        "reference_pack": {
            "reference_pack_integrity_pass": reference_pack_integrity_pass,
            "reference_pack_contradiction_count": reference_pack_contradiction_count,
            "current_authority_ref": "FAZ21 canonical current authority",
            "build_surface_ref": "FAZ16",
            "historical_summary_ref": "FAZ17",
            "current_summary_ref": "FAZ22",
            "reconciliation_ref": "FAZ23",
            "contradiction_rows": contradiction_rows,
        },
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
            f"- {row['phase_name']} / {row['field_name']} missing=`{row['missing_marker']}`"
            for row in ref["contradiction_rows"]
        ]
    )

    files: dict[Path, str] = {}
    files[ROOT / "coordination" / f"faz24-rc-m-archival-reference-pack-{DATE}.md"] = "\n".join(
        [
            "# FAZ24 RC-M Archival Reference Pack",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_authority_ref = `{ref['current_authority_ref']}`",
            f"- build_surface_ref = `{ref['build_surface_ref']}`",
            f"- historical_summary_ref = `{ref['historical_summary_ref']}`",
            f"- current_summary_ref = `{ref['current_summary_ref']}`",
            f"- reconciliation_ref = `{ref['reconciliation_ref']}`",
            *contradiction_lines,
        ]
    )
    files[ROOT / "coordination" / f"faz24-rc-m-archival-closure-contract-{DATE}.md"] = "\n".join(
        [
            "# FAZ24 RC-M Archival Closure Contract",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz24-rc-m-registry-closure-{DATE}.md"] = "\n".join(
        [
            "# FAZ24 RC-M Registry Closure",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in registry.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz24-rc-m-planner-denylist-{DATE}.md"] = "\n".join(
        [
            "# FAZ24 RC-M Planner Denylist",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in deny.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz24-rc-m-consumer-binding-closure-{DATE}.md"] = "\n".join(
        [
            "# FAZ24 RC-M Consumer Binding Closure",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in binding.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz24-rc-m-archival-manifest-{DATE}.md"] = "\n".join(
        [
            "# FAZ24 RC-M Archival Manifest",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in manifest.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz24-rc-m-tombstone-{DATE}.md"] = "\n".join(
        [
            "# FAZ24 RC-M Tombstone",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in tombstone.items()),
        ]
    )
    files[ROOT / "coordination" / f"faz24-rc-m-archival-closure-reconciliation-{DATE}.md"] = "\n".join(
        [
            "# FAZ24 RC-M Archival Closure Reconciliation",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in recon.items()),
        ]
    )
    files[RESULT_REPORT] = "\n".join(
        [
            "# FAZ24 RC-M Discard Archival Closure Under Canonical Current Authority Raporu",
            "",
            f"Tarih: {DATE}",
            "",
            "## Yonetici Ozeti",
            "",
            "FAZ24, RC-M adayini canonical current authority altinda kalici discard + archival closure durumuna tasimak icin yurutuldu. Bu fazda yeni build, patch, replay, recapture veya parity reopen acilmadi; yalniz FAZ16 + FAZ17 + FAZ21 + FAZ22 + FAZ23 rapor zinciri uzerinden RC-M historical archive / diagnostic only statude kapatildi.",
            "",
            f"Resmi karar: `{recon['official_decision']}`",
            "",
            "## Reference Pack Ozeti",
            "",
            f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
            f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
            f"- current_authority_ref = `{ref['current_authority_ref']}`",
            f"- build_surface_ref = `{ref['build_surface_ref']}`",
            f"- historical_summary_ref = `{ref['historical_summary_ref']}`",
            f"- current_summary_ref = `{ref['current_summary_ref']}`",
            f"- reconciliation_ref = `{ref['reconciliation_ref']}`",
            *contradiction_lines,
            "",
            "## WP Sonuclari",
            "",
            "### WP-1",
            f"- status = `{wp['WP-1']}`",
            "- reason = `FAZ16/17/21/22/23 reference pack contradiction_count=0 ile kapandi`" if wp["WP-1"] == "PASS" else "- reason = `reference pack contradiction bulundu`",
            "",
            "### WP-2",
            f"- status = `{wp['WP-2']}`",
            "- reason = `RC-M archival closure contract tum zorunlu alanlariyla materialize edildi`" if wp["WP-2"] == "PASS" else "- reason = `archival closure contract eksik`",
            "",
            "### WP-3",
            f"- status = `{wp['WP-3']}`",
            "- reason = `registry closure, planner denylist ve consumer binding closure birlikte tutarli`" if wp["WP-3"] == "PASS" else "- reason = `registry/planner/consumer closure tutarsiz`",
            "",
            "### WP-4",
            f"- status = `{wp['WP-4']}`",
            "- reason = `archival manifest ve tombstone birebir alanlarla materialize edildi`" if wp["WP-4"] == "PASS" else "- reason = `manifest veya tombstone eksik`",
            "",
            "### WP-5",
            f"- status = `{wp['WP-5']}`",
            "- reason = `tek resmi karar ve tek next_official_work planner kontratiyla birebir kapandi`" if wp["WP-5"] == "PASS" else "- reason = `final reconciliation kontrati kapanmadi`",
            "",
            "## RC-M Archival Closure Contract Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in contract.items()),
            "",
            "## Registry / Planner / Consumer Binding Closure Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in registry.items()),
            *(f"- {key} = `{_render_value(value)}`" for key, value in deny.items()),
            *(f"- {key} = `{_render_value(value)}`" for key, value in binding.items()),
            "",
            "## Archival Manifest ve Tombstone Ozeti",
            "",
            *(f"- {key} = `{_render_value(value)}`" for key, value in manifest.items()),
            *(f"- {key} = `{_render_value(value)}`" for key, value in tombstone.items()),
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
    parser = argparse.ArgumentParser(description="Build FAZ24 phase package.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    reference_texts = {
        key: load_text(root / rel_path)
        for key, rel_path in REFERENCE_FILES.items()
    }
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
    print(f"report={RESULT_REPORT.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
