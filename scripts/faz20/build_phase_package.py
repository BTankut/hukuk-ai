#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz20_lib import (  # type: ignore
    DECISION_TO_NEXT_WORK,
    FAMILY_SEQUENCE,
    PRIMARY_REASONS,
    bool_text,
    load_json,
    markdown_table,
    stable_hash,
    write_json,
)


def build_phase_payload(
    *,
    reference_packs: dict[str, dict[str, Any]],
    lineage_matrix: dict[str, Any],
    replay_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    reference_pack_integrity_pass = all(payload["reference_pack_integrity_pass"] for payload in reference_packs.values())
    reference_pack_contradiction_count = sum(int(payload["reference_pack_contradiction_count"]) for payload in reference_packs.values())
    wp3_pass = reference_pack_integrity_pass and reference_pack_contradiction_count == 0
    surface_breach_stage_set = sorted({stage for row in lineage_matrix["rows"] for stage in row["surface_breach_stage_set"]})
    recording_only_stage_set = sorted({stage for row in lineage_matrix["rows"] for stage in row["recording_only_stage_set"]})
    wp5_pass = all(
        replay["runtime_error_count"] == 0 and replay["family_metric_delta_zero"] and not replay["breach_in_h0_h9"]
        for replay in replay_payloads.values()
    )

    truth_rows = []
    frontier_rows = []
    for replay_name in ("faz13", "faz18", "faz19"):
        replay_payload = replay_payloads[replay_name]
        reference_payload = reference_packs[replay_name]
        for family_row in replay_payload["families"]:
            reference_row = next(row for row in reference_payload["families"] if row["family_name"] == family_row["family_name"])
            comparison_row = next(row for row in replay_payload["comparison_rows"] if row["family_name"] == family_row["family_name"])
            truth_row = {
                "replay_name": replay_name,
                "reference_name": reference_payload.get("reference_name", replay_name),
                "family_name": family_row["family_name"],
                "match": comparison_row["match"],
                "replay_mismatch_count": family_row["mismatch_count"],
                "reference_mismatch_count": reference_row["mismatch_count"],
                "replay_mismatch_question_ids": family_row["mismatch_question_ids"],
                "reference_mismatch_question_ids": reference_row["mismatch_question_ids"],
                "replay_mismatch_ordinals": family_row["mismatch_ordinals"],
                "reference_mismatch_ordinals": reference_row["mismatch_ordinals"],
                "replay_stage_histogram": family_row["mismatch_stage_histogram"],
                "reference_stage_histogram": reference_row["mismatch_stage_histogram"],
                "replay_reason_histogram": family_row["reason_histogram"],
                "reference_reason_histogram": reference_row["reason_histogram"],
                "first_divergence_stage": replay_payload["first_divergence_stage"] if not comparison_row["match"] else None,
                "primary_reason": replay_payload["primary_reason"] if not comparison_row["match"] else "stable_current_truth_canonical",
            }
            truth_rows.append(truth_row)
            if not comparison_row["match"]:
                frontier_rows.append(truth_row)

    frontier_count = len(frontier_rows)
    first_divergence_assigned_count = sum(1 for row in frontier_rows if row["first_divergence_stage"])
    primary_reason_assigned_count = sum(1 for row in frontier_rows if row["primary_reason"] in PRIMARY_REASONS)
    unexplained_count = sum(1 for row in frontier_rows if row["primary_reason"] == "unexplained_authority_history_conflict")

    reason_set_without_faz19 = {
        replay_payloads[name]["primary_reason"]
        for name in ("faz13", "faz18")
        if not replay_payloads[name]["reference_match"]
    }

    if not wp3_pass:
        official_decision = "NO-GO - Historical Reference Artifact Drift"
    elif surface_breach_stage_set and any(stage in {"H0", "H1", "H2", "H3"} for stage in surface_breach_stage_set):
        official_decision = "NO-GO - Candidate Freeze Identity Drift"
    elif surface_breach_stage_set and any(stage in {"H4", "H5", "H6", "H7", "H8", "H9"} for stage in surface_breach_stage_set):
        official_decision = "NO-GO - Runtime Or Evaluator Surface Drift"
    elif (
        replay_payloads["faz19"]["reference_match"]
        and not surface_breach_stage_set
        and len(reason_set_without_faz19) <= 1
        and unexplained_count == 0
    ):
        official_decision = "PASS - Current Authority Canonicalization Authorized"
    else:
        official_decision = "NO-GO - Unexplained Authority History Conflict"

    payload = {
        "wp3_pass": wp3_pass,
        "wp4_pass": True,
        "wp5_pass": wp5_pass,
        "reference_pack_integrity_pass": reference_pack_integrity_pass,
        "reference_pack_contradiction_count": reference_pack_contradiction_count,
        "surface_breach_stage_set": surface_breach_stage_set,
        "recording_only_stage_set": recording_only_stage_set,
        "replay_19_reference_match": replay_payloads["faz19"]["reference_match"],
        "frontier_count": frontier_count,
        "first_divergence_assigned_count": first_divergence_assigned_count,
        "primary_reason_assigned_count": primary_reason_assigned_count,
        "unexplained_count": unexplained_count,
        "dominant_stage": replay_payloads["faz13"]["first_divergence_stage"]
        if replay_payloads["faz13"]["first_divergence_stage"] == replay_payloads["faz18"]["first_divergence_stage"]
        else (replay_payloads["faz19"]["first_divergence_stage"] or replay_payloads["faz13"]["first_divergence_stage"]),
        "dominant_reason": replay_payloads["faz13"]["primary_reason"]
        if replay_payloads["faz13"]["primary_reason"] == replay_payloads["faz18"]["primary_reason"]
        else replay_payloads["faz19"]["primary_reason"],
        "official_decision": official_decision,
        "next_official_work": DECISION_TO_NEXT_WORK[official_decision],
        "truth_rows": truth_rows,
        "frontier_rows": frontier_rows,
    }
    payload["report_hash"] = stable_hash(payload)
    return payload


def render_truth_matrix(payload: dict[str, Any]) -> str:
    lines = ["# FAZ20 Authority History Truth Matrix", ""]
    lines.extend(
        markdown_table(
            [
                ("replay_name", "replay"),
                ("family_name", "family"),
                ("match", "match"),
                ("replay_mismatch_count", "replay_mismatch_count"),
                ("reference_mismatch_count", "reference_mismatch_count"),
                ("first_divergence_stage", "first_divergence_stage"),
                ("primary_reason", "primary_reason"),
            ],
            payload["truth_rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_frontier_replay(payload: dict[str, Any]) -> str:
    lines = [
        "# FAZ20 Authority History Frontier Replay",
        "",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- first_divergence_assigned_count = `{payload['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{payload['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- dominant_stage = `{payload['dominant_stage']}`",
        f"- dominant_reason = `{payload['dominant_reason']}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("replay_name", "replay"),
                ("family_name", "family"),
                ("replay_mismatch_question_ids", "replay_mismatch_question_ids"),
                ("reference_mismatch_question_ids", "reference_mismatch_question_ids"),
                ("first_divergence_stage", "first_divergence_stage"),
                ("primary_reason", "primary_reason"),
            ],
            payload["frontier_rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_root_cause_table(payload: dict[str, Any]) -> str:
    lines = ["# FAZ20 Authority History Root Cause Table", ""]
    lines.extend(
        markdown_table(
            [
                ("replay_name", "replay"),
                ("family_name", "family"),
                ("first_divergence_stage", "first_divergence_stage"),
                ("primary_reason", "primary_reason"),
            ],
            payload["frontier_rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def render_reconciliation(payload: dict[str, Any]) -> str:
    lines = [
        "# FAZ20 Authority History Reconciliation",
        "",
        f"- wp3_pass = `{bool_text(payload['wp3_pass'])}`",
        f"- wp4_pass = `{bool_text(payload['wp4_pass'])}`",
        f"- wp5_pass = `{bool_text(payload['wp5_pass'])}`",
        f"- replay_19_reference_match = `{bool_text(payload['replay_19_reference_match'])}`",
        f"- surface_breach_stage_set = `{payload['surface_breach_stage_set']}`",
        f"- recording_only_stage_set = `{payload['recording_only_stage_set']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
    ]
    return "\n".join(lines)


def render_steering(payload: dict[str, Any]) -> str:
    rows = [
        {
            "wp": "WP-1",
            "status": "PASS",
            "evidence": "freeze/adoption artefact'lari tamam",
            "decision": "wp2",
        },
        {
            "wp": "WP-2",
            "status": "PASS",
            "evidence": "schema/taxonomy/decision contract tamam",
            "decision": "wp3",
        },
        {
            "wp": "WP-3",
            "status": "PASS" if payload["wp3_pass"] else "FAIL",
            "evidence": f"reference_pack_integrity_pass={bool_text(payload['reference_pack_integrity_pass'])}, contradiction_count={payload['reference_pack_contradiction_count']}",
            "decision": "wp4" if payload["wp3_pass"] else payload["official_decision"],
        },
        {
            "wp": "WP-4",
            "status": "PASS",
            "evidence": "tri-reference lineage matrix hazir",
            "decision": "wp5",
        },
        {
            "wp": "WP-5",
            "status": "PASS" if payload["wp5_pass"] else "FAIL",
            "evidence": f"replay_19_reference_match={bool_text(payload['replay_19_reference_match'])}, surface_breach_stage_set={payload['surface_breach_stage_set']}",
            "decision": "wp6",
        },
        {
            "wp": "WP-6",
            "status": "PASS" if payload["unexplained_count"] == 0 else "FAIL",
            "evidence": f"frontier_count={payload['frontier_count']}, unexplained_count={payload['unexplained_count']}",
            "decision": "wp7",
        },
        {
            "wp": "WP-7",
            "status": "PASS",
            "evidence": payload["official_decision"],
            "decision": payload["next_official_work"],
        },
    ]
    lines = ["# FAZ20 Steering Decision Table", ""]
    lines.extend(
        markdown_table(
            [
                ("wp", "WP"),
                ("status", "Durum"),
                ("evidence", "Kanit"),
                ("decision", "Karar"),
            ],
            rows,
        )
    )
    lines.extend(
        [
            "",
            f"- official_decision = `{payload['official_decision']}`",
            f"- next_official_work = `{payload['next_official_work']}`",
            "",
        ]
    )
    return "\n".join(lines)


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# FAZ20 RC-G vs RC-J Current Authority Drift Forensics Recapture Raporu",
        "",
        "Tarih: 2026-03-26",
        "",
        "## Yonetici Ozeti",
        "",
        "FAZ20 yalniz tri-reference adoption, normalization, lineage matrix, contract-conditioned replay ve authority history reconciliation icin yurutuldu.",
        "",
        f"Resmi karar: `{payload['official_decision']}`",
        "",
        "## Gate Sonucu",
        "",
        f"- `wp3_pass = {bool_text(payload['wp3_pass'])}`",
        f"- `replay_19_reference_match = {bool_text(payload['replay_19_reference_match'])}`",
        f"- `surface_breach_stage_set = {payload['surface_breach_stage_set']}`",
        f"- `recording_only_stage_set = {payload['recording_only_stage_set']}`",
        f"- `frontier_count = {payload['frontier_count']}`",
        f"- `unexplained_count = {payload['unexplained_count']}`",
        f"- `dominant_stage = {payload['dominant_stage']}`",
        f"- `dominant_reason = {payload['dominant_reason']}`",
        "",
        "## Resmi Karar",
        "",
        f"- `{payload['official_decision']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- `{payload['next_official_work']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ20 final package.")
    parser.add_argument("--faz13-reference-json", type=Path, required=True)
    parser.add_argument("--faz18-reference-json", type=Path, required=True)
    parser.add_argument("--faz19-reference-json", type=Path, required=True)
    parser.add_argument("--lineage-json", type=Path, required=True)
    parser.add_argument("--replay-faz13-json", type=Path, required=True)
    parser.add_argument("--replay-faz18-json", type=Path, required=True)
    parser.add_argument("--replay-faz19-json", type=Path, required=True)
    parser.add_argument("--truth-matrix-json", type=Path, required=True)
    parser.add_argument("--truth-matrix-md", type=Path, required=True)
    parser.add_argument("--frontier-json", type=Path, required=True)
    parser.add_argument("--frontier-md", type=Path, required=True)
    parser.add_argument("--root-cause-json", type=Path, required=True)
    parser.add_argument("--root-cause-md", type=Path, required=True)
    parser.add_argument("--reconciliation-json", type=Path, required=True)
    parser.add_argument("--reconciliation-md", type=Path, required=True)
    parser.add_argument("--next-work-json", type=Path, required=True)
    parser.add_argument("--next-work-md", type=Path, required=True)
    parser.add_argument("--steering-md", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    args = parser.parse_args()

    reference_packs = {
        "faz13": load_json(args.faz13_reference_json),
        "faz18": load_json(args.faz18_reference_json),
        "faz19": load_json(args.faz19_reference_json),
    }
    replay_payloads = {
        "faz13": load_json(args.replay_faz13_json),
        "faz18": load_json(args.replay_faz18_json),
        "faz19": load_json(args.replay_faz19_json),
    }
    lineage_matrix = load_json(args.lineage_json)
    payload = build_phase_payload(
        reference_packs=reference_packs,
        lineage_matrix=lineage_matrix,
        replay_payloads=replay_payloads,
    )

    write_json(args.truth_matrix_json, {"rows": payload["truth_rows"], "report_hash": stable_hash(payload["truth_rows"])})
    args.truth_matrix_md.parent.mkdir(parents=True, exist_ok=True)
    args.truth_matrix_md.write_text(render_truth_matrix(payload), encoding="utf-8")

    frontier_payload = {
        "frontier_count": payload["frontier_count"],
        "first_divergence_assigned_count": payload["first_divergence_assigned_count"],
        "primary_reason_assigned_count": payload["primary_reason_assigned_count"],
        "unexplained_count": payload["unexplained_count"],
        "dominant_stage": payload["dominant_stage"],
        "dominant_reason": payload["dominant_reason"],
        "rows": payload["frontier_rows"],
    }
    write_json(args.frontier_json, frontier_payload)
    args.frontier_md.parent.mkdir(parents=True, exist_ok=True)
    args.frontier_md.write_text(render_frontier_replay(payload), encoding="utf-8")

    root_cause_payload = {
        "frontier_count": payload["frontier_count"],
        "dominant_stage": payload["dominant_stage"],
        "dominant_reason": payload["dominant_reason"],
        "rows": payload["frontier_rows"],
    }
    write_json(args.root_cause_json, root_cause_payload)
    args.root_cause_md.parent.mkdir(parents=True, exist_ok=True)
    args.root_cause_md.write_text(render_root_cause_table(payload), encoding="utf-8")

    reconciliation_payload = {
        key: payload[key]
        for key in (
            "wp3_pass",
            "wp4_pass",
            "wp5_pass",
            "reference_pack_integrity_pass",
            "reference_pack_contradiction_count",
            "surface_breach_stage_set",
            "recording_only_stage_set",
            "replay_19_reference_match",
            "frontier_count",
            "first_divergence_assigned_count",
            "primary_reason_assigned_count",
            "unexplained_count",
            "dominant_stage",
            "dominant_reason",
            "official_decision",
            "next_official_work",
        )
    }
    write_json(args.reconciliation_json, reconciliation_payload)
    args.reconciliation_md.parent.mkdir(parents=True, exist_ok=True)
    args.reconciliation_md.write_text(render_reconciliation(payload), encoding="utf-8")

    next_work_payload = {
        "official_decision": payload["official_decision"],
        "next_official_work": payload["next_official_work"],
    }
    write_json(args.next_work_json, next_work_payload)
    args.next_work_md.parent.mkdir(parents=True, exist_ok=True)
    args.next_work_md.write_text(
        "\n".join(
            [
                "# FAZ20 Next Official Work",
                "",
                f"- official_decision = `{payload['official_decision']}`",
                f"- next_official_work = `{payload['next_official_work']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    args.steering_md.parent.mkdir(parents=True, exist_ok=True)
    args.steering_md.write_text(render_steering(payload), encoding="utf-8")
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text(render_report(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
