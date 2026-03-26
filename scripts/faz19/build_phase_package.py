#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz19_lib import (  # type: ignore
    CANDIDATE_SEQUENCE,
    DATE_TAG,
    DECISION_TO_NEXT_WORK,
    FAMILY_SEQUENCE,
    PRIMARY_REASONS,
    STAGE_LADDER,
    UPSTREAM_STAGES,
    bool_text,
    candidate_rows_from_report,
    compare_capture_reports,
    dominant_counter_value,
    family_report_row,
    family_sort_key,
    first_divergence_stage_for_rows,
    load_json,
    markdown_table,
    primary_reason_for_stage,
    stable_hash,
    write_json,
)


def _reference_payload(reference_name: str, report_paths: list[Path]) -> dict[str, Any]:
    reports = [(path, load_json(path)) for path in report_paths]
    families = [
        family_report_row(report, report_path=str(path))
        for path, report in sorted(reports, key=lambda item: family_sort_key(str(item[1]["family_id"])))
    ]
    payload = {
        "reference_name": reference_name,
        "families": families,
        "control_pair_runtime_error_count": sum(item["runtime_error_count"] for item in families),
        "control_pair_breach_in_o0_o5": any(item["breach_in_o0_o5"] for item in families),
        "control_pair_breach_in_f0_f12": any(item["breach_in_f0_f12"] for item in families),
        "family_metric_delta_zero": all(item["family_metric_delta_zero"] for item in families),
    }
    payload["report_hash"] = stable_hash(payload)
    return payload


def _reference_match_rows(stable_families: list[dict[str, Any]], reference_families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ref_index = {row["family_id"]: row for row in reference_families}
    rows = []
    for family_id in FAMILY_SEQUENCE:
        stable_row = next(row for row in stable_families if row["family_id"] == family_id)
        ref_row = ref_index[family_id]
        mismatched_fields = []
        for key in (
            "mismatch_count",
            "mismatch_stage_histogram",
            "mismatch_question_ids",
            "mismatch_ordinals",
            "family_metric_delta_zero",
        ):
            if stable_row.get(key) != ref_row.get(key):
                mismatched_fields.append(key)
        rows.append(
            {
                "family_id": family_id,
                "match": not mismatched_fields,
                "mismatched_fields": mismatched_fields,
                "stable_mismatch_count": stable_row["mismatch_count"],
                "reference_mismatch_count": ref_row["mismatch_count"],
                "stable_stage_histogram": stable_row["mismatch_stage_histogram"],
                "reference_stage_histogram": ref_row["mismatch_stage_histogram"],
                "stable_question_ids": stable_row["mismatch_question_ids"],
                "reference_question_ids": ref_row["mismatch_question_ids"],
            }
        )
    return rows


def _capture_frontier_rows(
    capture_a_payload: dict[str, Any],
    capture_b_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    capture_a_paths = {row["family_id"]: Path(row["report_path"]) for row in capture_a_payload["families"]}
    capture_b_paths = {row["family_id"]: Path(row["report_path"]) for row in capture_b_payload["families"]}

    for family_id in FAMILY_SEQUENCE:
        report_a = load_json(capture_a_paths[family_id])
        report_b = load_json(capture_b_paths[family_id])
        for candidate_kind in CANDIDATE_SEQUENCE:
            rows_a = {row["question_id"]: row for row in candidate_rows_from_report(report_a, candidate_kind)}
            rows_b = {row["question_id"]: row for row in candidate_rows_from_report(report_b, candidate_kind)}
            for question_id in sorted(set(rows_a) | set(rows_b)):
                left = rows_a.get(question_id)
                right = rows_b.get(question_id)
                if left is None or right is None:
                    stage = "normalized_request_hash"
                    reason = "effective_view_accounting_delta"
                    ordinal_index = int((left or right or {}).get("ordinal_index", 0))
                else:
                    if all(
                        left.get(field) == right.get(field)
                        for field in (
                            "runtime_error",
                            "error_type",
                            "error_rerun_used",
                            "effective_view_member",
                            *STAGE_LADDER,
                            "answer_body_hash",
                            "citation_body_hash",
                            "refusal_body_hash",
                        )
                    ):
                        continue
                    stage = first_divergence_stage_for_rows(left, right)
                    reason = primary_reason_for_stage(
                        stage,
                        runtime_mismatch=bool(left["runtime_error"] != right["runtime_error"] or left["error_rerun_used"] != right["error_rerun_used"] or left["effective_view_member"] != right["effective_view_member"]),
                        capture_compare=True,
                    )
                    ordinal_index = int(left["ordinal_index"])
                rows.append(
                    {
                        "frontier_key": f"{family_id}/{candidate_kind}/{ordinal_index:03d}",
                        "family_id": family_id,
                        "candidate_kind": candidate_kind,
                        "question_id": question_id,
                        "ordinal_index": ordinal_index,
                        "first_divergence_stage": stage,
                        "primary_reason": reason,
                    }
                )
    rows.sort(key=lambda item: (item["family_id"], item["candidate_kind"], item["ordinal_index"]))
    return rows


def _reference_frontier_rows(stable_payload: dict[str, Any], reference_payload: dict[str, Any]) -> list[dict[str, Any]]:
    stable_index = {row["family_id"]: row for row in stable_payload["families"]}
    reference_index = {row["family_id"]: row for row in reference_payload["families"]}
    rows: list[dict[str, Any]] = []
    for family_id in FAMILY_SEQUENCE:
        stable_row = stable_index[family_id]
        ref_row = reference_index[family_id]
        stable_mismatch_index = {
            question_id: {
                "ordinal_index": ordinal_index,
                "stage": stage,
            }
            for question_id, ordinal_index, stage in zip(
                stable_row["mismatch_question_ids"],
                stable_row["mismatch_ordinals"],
                [
                    next(
                        (
                            stage_name
                            for stage_name, count in stable_row["mismatch_stage_histogram"].items()
                            if count
                        ),
                        None,
                    )
                ]
                * len(stable_row["mismatch_question_ids"]),
            )
        }
        ref_mismatch_index = {
            question_id: {
                "ordinal_index": ordinal_index,
                "stage": stage,
            }
            for question_id, ordinal_index, stage in zip(
                ref_row["mismatch_question_ids"],
                ref_row["mismatch_ordinals"],
                [
                    next(
                        (
                            stage_name
                            for stage_name, count in ref_row["mismatch_stage_histogram"].items()
                            if count
                        ),
                        None,
                    )
                ]
                * len(ref_row["mismatch_question_ids"]),
            )
        }
        for question_id in sorted(set(stable_mismatch_index) | set(ref_mismatch_index)):
            left = stable_mismatch_index.get(question_id)
            right = ref_mismatch_index.get(question_id)
            if left == right:
                continue
            source = left or right or {}
            stage = str(source.get("stage") or "serialized_output_hash")
            reason = primary_reason_for_stage(stage, runtime_mismatch=False, capture_compare=False)
            if reason not in PRIMARY_REASONS:
                reason = "unexplained_current_authority_drift"
            rows.append(
                {
                    "frontier_key": f"{family_id}/control_pair/{int(source.get('ordinal_index', 0)):03d}",
                    "family_id": family_id,
                    "candidate_kind": "control_pair",
                    "question_id": question_id,
                    "ordinal_index": int(source.get("ordinal_index", 0)),
                    "first_divergence_stage": stage,
                    "primary_reason": reason,
                }
            )
    rows.sort(key=lambda item: (item["family_id"], item["ordinal_index"]))
    return rows


def _render_frontier_md(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- status = `{payload['status']}`",
        f"- frontier_count = `{payload['frontier_count']}`",
        f"- first_divergence_assigned_count = `{payload['first_divergence_assigned_count']}`",
        f"- primary_reason_assigned_count = `{payload['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        f"- dominant_stage = `{payload.get('dominant_stage')}`",
        f"- dominant_reason = `{payload.get('dominant_reason')}`",
        "",
    ]
    if payload.get("rows"):
        lines.extend(
            markdown_table(
                [
                    ("family_id", "family"),
                    ("candidate_kind", "candidate"),
                    ("question_id", "question_id"),
                    ("ordinal_index", "ordinal"),
                    ("first_divergence_stage", "first_divergence_stage"),
                    ("primary_reason", "primary_reason"),
                ],
                payload["rows"],
            )
        )
        lines.append("")
    return "\n".join(lines)


def _render_reference_contrast_md(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- historical_authority_restored = `{bool_text(payload['historical_authority_restored'])}`",
        f"- current_instability_snapshot_confirmed = `{bool_text(payload['current_instability_snapshot_confirmed'])}`",
        f"- current_authority_contract_breach = `{bool_text(payload['current_authority_contract_breach'])}`",
        "",
        "## Historical Contrast",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("match", "match"),
                ("mismatched_fields", "mismatched_fields"),
                ("stable_mismatch_count", "stable_mismatch_count"),
                ("reference_mismatch_count", "reference_mismatch_count"),
            ],
            payload["historical_rows"],
        )
    )
    lines.extend(["", "## Current Instability Snapshot Contrast", ""])
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("match", "match"),
                ("mismatched_fields", "mismatched_fields"),
                ("stable_mismatch_count", "stable_mismatch_count"),
                ("reference_mismatch_count", "reference_mismatch_count"),
            ],
            payload["snapshot_rows"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def _render_candidate_fingerprint_md(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", "",]
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("candidate_kind", "candidate"),
                ("match", "match"),
                ("row_count_a", "row_count_a"),
                ("row_count_b", "row_count_b"),
                ("fingerprint_hash_a", "fingerprint_hash_a"),
                ("fingerprint_hash_b", "fingerprint_hash_b"),
            ],
            rows,
        )
    )
    lines.append("")
    return "\n".join(lines)


def _render_current_summary_md(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- capture_stability_match = `{bool_text(payload['capture_stability_match'])}`",
        f"- capture_a_vs_capture_b_mismatch_count = `{payload['capture_a_vs_capture_b_mismatch_count']}`",
        f"- capture_a_vs_capture_b_runtime_error_count = `{payload['capture_a_vs_capture_b_runtime_error_count']}`",
        f"- control_pair_breach_in_o0_o5 = `{bool_text(payload['control_pair_breach_in_o0_o5'])}`",
        f"- control_pair_breach_in_f0_f12 = `{bool_text(payload['control_pair_breach_in_f0_f12'])}`",
        f"- family_metric_delta_zero = `{bool_text(payload['family_metric_delta_zero'])}`",
        f"- historical_authority_restored = `{bool_text(payload['historical_authority_restored'])}`",
        f"- current_instability_snapshot_confirmed = `{bool_text(payload['current_instability_snapshot_confirmed'])}`",
        f"- current_authority_contract_breach = `{bool_text(payload['current_authority_contract_breach'])}`",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                ("family_id", "family"),
                ("mismatch_count", "mismatch_count"),
                ("runtime_error_count", "runtime_error_count"),
                ("family_metric_delta_zero", "family_metric_delta_zero"),
                ("mismatch_stage_histogram", "mismatch_stage_histogram"),
                ("mismatch_question_ids", "mismatch_question_ids"),
            ],
            payload["stable_families"],
        )
    )
    lines.append("")
    return "\n".join(lines)


def _render_reconciliation_md(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- wp1_status = `PASS`",
        f"- wp2_status = `PASS`",
        f"- wp3_status = `{payload['wp3_status']}`",
        f"- wp4_status = `{payload['wp4_status']}`",
        f"- wp5_status = `{payload['wp5_status']}`",
        f"- wp6_status = `{payload['wp6_status']}`",
        f"- wp7_status = `PASS`",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
    ]
    return "\n".join(lines)


def _render_steering_md(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        "| WP | Durum | Kanit | Karar |",
        "| --- | --- | --- | --- |",
        f"| `WP-1` freeze ve referans adoption | PASS | freeze/adoption artefact'lari tamam | sonraki pakete gec |",
        f"| `WP-2` schema/taxonomy/equivalence contract | PASS | FAZ19 contract dosyalari tamam | capture ac |",
        f"| `WP-3` capture_a | {payload['wp3_status']} | capture_a raporu uretildi | capture_b yetkisi |",
        f"| `WP-4` capture_b | {payload['wp4_status']} | capture_b raporu uretildi | stability gate |",
        f"| `WP-5` stable current authority gate | {payload['wp5_status']} | capture_a_vs_capture_b_mismatch_count={payload['capture_a_vs_capture_b_mismatch_count']}, runtime_error_count={payload['capture_a_vs_capture_b_runtime_error_count']} | stable truth karari kayda gecti |",
        f"| `WP-6` reference contrast / localization | {payload['wp6_status']} | historical_restored={bool_text(payload['historical_authority_restored'])}, snapshot_confirmed={bool_text(payload['current_instability_snapshot_confirmed'])}, unexplained_count={payload['unexplained_count']} | localization veya reference contrast kapandi |",
        f"| `WP-7` resmi reconciliation | PASS | tek karar ve next work uretildi | faz kapandi |",
        "",
        f"- official_decision = `{payload['official_decision']}`",
        f"- next_official_work = `{payload['next_official_work']}`",
        "",
    ]
    return "\n".join(lines)


def _render_report_md(title: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        "Tarih: 2026-03-25",
        "",
        "## Yonetici Ozeti",
        "",
        f"FAZ19 yalniz `RC-G vs RC-J current authority recapture` amaciyla yurutuldu. Iki bagimsiz capture ayni aile ve candidate sirasi ile alindi, stability gate calistirildi, stable current truth cikiyorsa FAZ13 tarihsel authority ve FAZ18 current instability snapshot referanslari ile karsilastirildi.",
        "",
        f"Resmi karar: `{payload['official_decision']}`",
        "",
        "## Gate Sonucu",
        "",
        f"- `capture_stability_match = {bool_text(payload['capture_stability_match'])}`",
        f"- `capture_a_vs_capture_b_mismatch_count = {payload['capture_a_vs_capture_b_mismatch_count']}`",
        f"- `capture_a_vs_capture_b_runtime_error_count = {payload['capture_a_vs_capture_b_runtime_error_count']}`",
        f"- `historical_authority_restored = {bool_text(payload['historical_authority_restored'])}`",
        f"- `current_instability_snapshot_confirmed = {bool_text(payload['current_instability_snapshot_confirmed'])}`",
        f"- `current_authority_contract_breach = {bool_text(payload['current_authority_contract_breach'])}`",
        f"- `unexplained_count = {payload['unexplained_count']}`",
        "",
        "## Stable Current Truth",
        "",
    ]
    for row in payload["stable_families"]:
        lines.append(
            f"- `{row['family_id']}` -> `mismatch_count={row['mismatch_count']}`, `runtime_error_count={row['runtime_error_count']}`, `family_metric_delta_zero={bool_text(row['family_metric_delta_zero'])}`, `mismatch_stage_histogram={row['mismatch_stage_histogram']}`, `mismatch_question_ids={row['mismatch_question_ids']}`"
        )
    lines.extend(
        [
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
    )
    return "\n".join(lines)


def build_phase_outputs(
    *,
    capture_a_payload: dict[str, Any],
    capture_b_payload: dict[str, Any],
    historical_payload: dict[str, Any],
    snapshot_payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    family_comparisons, fingerprint_comparisons = compare_capture_reports(capture_a_payload, capture_b_payload)
    fingerprint_mismatch_count = sum(1 for row in fingerprint_comparisons if not row["match"])
    summary_mismatch_count = sum(1 for row in family_comparisons if not row["match"])
    capture_runtime_error_count = int(capture_a_payload["control_pair_runtime_error_count"]) + int(
        capture_b_payload["control_pair_runtime_error_count"]
    )
    capture_stability_match = (
        fingerprint_mismatch_count == 0
        and summary_mismatch_count == 0
        and capture_runtime_error_count == 0
        and not capture_a_payload["control_pair_breach_in_o0_o5"]
        and not capture_b_payload["control_pair_breach_in_o0_o5"]
        and capture_a_payload["family_metric_delta_zero"]
        and capture_b_payload["family_metric_delta_zero"]
    )

    stable_payload = capture_a_payload if capture_stability_match else capture_a_payload
    historical_rows = _reference_match_rows(stable_payload["families"], historical_payload["families"])
    snapshot_rows = _reference_match_rows(stable_payload["families"], snapshot_payload["families"])
    historical_authority_restored = capture_stability_match and all(row["match"] for row in historical_rows)
    current_instability_snapshot_confirmed = capture_stability_match and all(row["match"] for row in snapshot_rows)
    current_authority_contract_breach = bool(stable_payload["control_pair_breach_in_o0_o5"]) or not bool(
        stable_payload["family_metric_delta_zero"]
    )

    reference_contrast = {
        "historical_authority_restored": historical_authority_restored,
        "current_instability_snapshot_confirmed": current_instability_snapshot_confirmed,
        "current_authority_contract_breach": current_authority_contract_breach,
        "historical_rows": historical_rows,
        "snapshot_rows": snapshot_rows,
    }
    reference_contrast["report_hash"] = stable_hash(reference_contrast)

    if not capture_stability_match:
        frontier_rows = _capture_frontier_rows(capture_a_payload, capture_b_payload)
    elif historical_authority_restored or (current_instability_snapshot_confirmed and not current_authority_contract_breach):
        frontier_rows = []
    else:
        contrast_reference = historical_payload if not current_instability_snapshot_confirmed else snapshot_payload
        frontier_rows = _reference_frontier_rows(stable_payload, contrast_reference)

    stage_histogram = dict(Counter(str(row["first_divergence_stage"]) for row in frontier_rows if row.get("first_divergence_stage")))
    reason_histogram = dict(Counter(str(row["primary_reason"]) for row in frontier_rows if row.get("primary_reason")))
    unexplained_count = sum(
        1 for row in frontier_rows if not row.get("first_divergence_stage") or not row.get("primary_reason")
    )
    frontier_payload = {
        "status": "PASS" if capture_stability_match else "FAIL",
        "frontier_count": len(frontier_rows),
        "first_divergence_assigned_count": len([row for row in frontier_rows if row.get("first_divergence_stage")]),
        "primary_reason_assigned_count": len([row for row in frontier_rows if row.get("primary_reason")]),
        "unexplained_count": unexplained_count,
        "dominant_stage": dominant_counter_value(frontier_rows, "first_divergence_stage"),
        "dominant_reason": dominant_counter_value(frontier_rows, "primary_reason"),
        "stage_histogram": stage_histogram,
        "reason_histogram": reason_histogram,
        "rows": frontier_rows,
    }
    frontier_payload["report_hash"] = stable_hash(frontier_payload)

    wp3_status = "PASS" if capture_a_payload["control_pair_runtime_error_count"] == 0 else "FAIL"
    wp4_status = "PASS" if capture_b_payload["control_pair_runtime_error_count"] == 0 else "FAIL"
    wp5_status = "PASS" if capture_stability_match else "FAIL"
    wp6_status = "PASS" if frontier_payload["unexplained_count"] == 0 else "FAIL"

    if wp5_status == "PASS" and historical_authority_restored:
        decision = "PASS - Historical Authority Restored"
    elif wp5_status == "PASS" and (not historical_authority_restored) and current_instability_snapshot_confirmed and not current_authority_contract_breach:
        decision = "PASS - Stable Current Authority Re-Captured"
    elif wp5_status == "FAIL" and frontier_payload["unexplained_count"] == 0:
        decision = "NO-GO - Current Authority Non-Reproducible"
    elif wp5_status == "PASS" and current_authority_contract_breach and frontier_payload["unexplained_count"] == 0:
        decision = "NO-GO - Current Authority Contract Breach"
    else:
        decision = "NO-GO - Unexplained Current Authority Drift"

    current_summary = {
        "capture_stability_match": capture_stability_match,
        "capture_a_vs_capture_b_mismatch_count": int(frontier_payload["frontier_count"] if not capture_stability_match else fingerprint_mismatch_count + summary_mismatch_count),
        "capture_a_vs_capture_b_runtime_error_count": capture_runtime_error_count,
        "control_pair_breach_in_o0_o5": bool(stable_payload["control_pair_breach_in_o0_o5"]),
        "control_pair_breach_in_f0_f12": bool(stable_payload["control_pair_breach_in_f0_f12"]),
        "family_metric_delta_zero": bool(stable_payload["family_metric_delta_zero"]),
        "historical_authority_restored": historical_authority_restored,
        "current_instability_snapshot_confirmed": current_instability_snapshot_confirmed,
        "current_authority_contract_breach": current_authority_contract_breach,
        "stable_families": stable_payload["families"],
        "capture_a_family_comparisons": family_comparisons,
        "capture_a_b_fingerprint_comparisons": fingerprint_comparisons,
    }
    current_summary["report_hash"] = stable_hash(current_summary)

    reconciliation = {
        "wp3_status": wp3_status,
        "wp4_status": wp4_status,
        "wp5_status": wp5_status,
        "wp6_status": wp6_status,
        "capture_stability_match": capture_stability_match,
        "capture_a_vs_capture_b_mismatch_count": current_summary["capture_a_vs_capture_b_mismatch_count"],
        "capture_a_vs_capture_b_runtime_error_count": capture_runtime_error_count,
        "historical_authority_restored": historical_authority_restored,
        "current_instability_snapshot_confirmed": current_instability_snapshot_confirmed,
        "current_authority_contract_breach": current_authority_contract_breach,
        "unexplained_count": frontier_payload["unexplained_count"],
        "official_decision": decision,
        "next_official_work": DECISION_TO_NEXT_WORK[decision],
    }
    reconciliation["report_hash"] = stable_hash(reconciliation)

    return {
        "current_summary": current_summary,
        "candidate_fingerprint_table": {
            "rows": fingerprint_comparisons,
            "report_hash": stable_hash(fingerprint_comparisons),
        },
        "reference_contrast": reference_contrast,
        "frontier": frontier_payload,
        "root_cause_table": {
            "frontier_count": frontier_payload["frontier_count"],
            "dominant_stage": frontier_payload["dominant_stage"],
            "dominant_reason": frontier_payload["dominant_reason"],
            "rows": frontier_rows,
            "report_hash": stable_hash(frontier_rows),
        },
        "reconciliation": reconciliation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ19 phase outputs.")
    parser.add_argument("--capture-a-json", type=Path, required=True)
    parser.add_argument("--capture-b-json", type=Path, required=True)
    parser.add_argument("--historical-report-json", type=Path, action="append", required=True)
    parser.add_argument("--snapshot-report-json", type=Path, action="append", required=True)
    parser.add_argument("--current-summary-output-json", type=Path, required=True)
    parser.add_argument("--current-summary-output-md", type=Path, required=True)
    parser.add_argument("--fingerprint-output-json", type=Path, required=True)
    parser.add_argument("--fingerprint-output-md", type=Path, required=True)
    parser.add_argument("--reference-contrast-output-json", type=Path, required=True)
    parser.add_argument("--reference-contrast-output-md", type=Path, required=True)
    parser.add_argument("--frontier-pack-output-json", type=Path, required=True)
    parser.add_argument("--frontier-pack-output-md", type=Path, required=True)
    parser.add_argument("--frontier-replay-output-json", type=Path, required=True)
    parser.add_argument("--frontier-replay-output-md", type=Path, required=True)
    parser.add_argument("--root-cause-output-json", type=Path, required=True)
    parser.add_argument("--root-cause-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path, required=True)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--next-work-output-json", type=Path, required=True)
    parser.add_argument("--next-work-output-md", type=Path, required=True)
    parser.add_argument("--steering-output-md", type=Path, required=True)
    parser.add_argument("--report-output-md", type=Path, required=True)
    args = parser.parse_args()

    capture_a_payload = load_json(args.capture_a_json)
    capture_b_payload = load_json(args.capture_b_json)
    historical_payload = _reference_payload("historical_authority", args.historical_report_json)
    snapshot_payload = _reference_payload("current_instability_snapshot", args.snapshot_report_json)
    outputs = build_phase_outputs(
        capture_a_payload=capture_a_payload,
        capture_b_payload=capture_b_payload,
        historical_payload=historical_payload,
        snapshot_payload=snapshot_payload,
    )

    current_summary = outputs["current_summary"]
    fingerprint_table = outputs["candidate_fingerprint_table"]
    reference_contrast = outputs["reference_contrast"]
    frontier = outputs["frontier"]
    root_cause = outputs["root_cause_table"]
    reconciliation = outputs["reconciliation"]

    write_json(args.current_summary_output_json, current_summary)
    write_json(args.fingerprint_output_json, fingerprint_table)
    write_json(args.reference_contrast_output_json, reference_contrast)
    write_json(args.frontier_pack_output_json, frontier)
    write_json(args.frontier_replay_output_json, frontier)
    write_json(args.root_cause_output_json, root_cause)
    write_json(args.reconciliation_output_json, reconciliation)
    write_json(args.next_work_output_json, {"next_official_work": reconciliation["next_official_work"]})

    args.current_summary_output_md.write_text(
        _render_current_summary_md("FAZ19 Current Authority Summary", current_summary),
        encoding="utf-8",
    )
    args.fingerprint_output_md.write_text(
        _render_candidate_fingerprint_md("FAZ19 Current Authority Candidate Fingerprint Table", fingerprint_table["rows"]),
        encoding="utf-8",
    )
    args.reference_contrast_output_md.write_text(
        _render_reference_contrast_md("FAZ19 Current Authority Reference Contrast", reference_contrast),
        encoding="utf-8",
    )
    args.frontier_pack_output_md.write_text(
        _render_frontier_md("FAZ19 Current Authority Frontier Pack", frontier),
        encoding="utf-8",
    )
    args.frontier_replay_output_md.write_text(
        _render_frontier_md("FAZ19 Current Authority Frontier Replay", frontier),
        encoding="utf-8",
    )
    args.root_cause_output_md.write_text(
        _render_frontier_md("FAZ19 Current Authority Root Cause Table", {**frontier, **root_cause}),
        encoding="utf-8",
    )
    args.reconciliation_output_md.write_text(
        _render_reconciliation_md("FAZ19 Current Authority Reconciliation", reconciliation),
        encoding="utf-8",
    )
    args.next_work_output_md.write_text(
        "\n".join(
            [
                "# FAZ19 Next Official Work",
                "",
                f"- next_official_work = `{reconciliation['next_official_work']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    args.steering_output_md.write_text(
        _render_steering_md("FAZ19 Steering Decision Table", reconciliation),
        encoding="utf-8",
    )
    args.report_output_md.write_text(
        _render_report_md("FAZ19 RC-G vs RC-J Current Authority Recapture Raporu", reconciliation | current_summary),
        encoding="utf-8",
    )
    return 0 if reconciliation["official_decision"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
