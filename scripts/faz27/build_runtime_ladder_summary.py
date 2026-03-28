#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz27_lib import BIND_ORDER_ROWS, load_json, markdown_table, write_json, write_text  # type: ignore


COUNT_KEYS = [
    "model_request_payload_hash_mismatch_count",
    "retrieval_request_hash_mismatch_count",
    "assembled_context_hash_mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "runtime_error_count",
]

STAGE_COUNT_KEYS = [
    ("retrieval_input_payload", "retrieval_request_hash_mismatch_count"),
    ("assembly_payload", "assembled_context_hash_mismatch_count"),
    ("model_request_payload", "model_request_payload_hash_mismatch_count"),
    ("preprojection_hash", "preprojection_hash_mismatch_count"),
    ("raw_answer_object", "raw_answer_hash_mismatch_count"),
    ("response_envelope", "response_envelope_hash_mismatch_count"),
]


def _parse_mapping(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep:
            raise ValueError(f"expected KEY=VALUE mapping, got {item}")
        mapping[key] = value
    return mapping


def _stage_for_report(report: dict[str, Any]) -> tuple[str | None, int]:
    for stage_name, key in STAGE_COUNT_KEYS:
        value = int(report.get(key, 0))
        if value > 0:
            return stage_name, value
    return None, 0


def build_ladder_payload(
    *,
    step_reports: dict[str, dict[str, Any]],
    inherited_steps: dict[str, str],
) -> dict[str, Any]:
    bind_index = {row["step_id"]: row for row in BIND_ORDER_ROWS}
    rows: list[dict[str, Any]] = []
    last_report: dict[str, Any] | None = None
    effective_control_set: list[str] = []

    for step_id in [row["step_id"] for row in BIND_ORDER_ROWS]:
        bind_row = bind_index[step_id]
        if step_id == "B0":
            row = {
                "step_id": step_id,
                "bound_control_set": bind_row["bound_control_set"],
                "source": "authoritative_rc_g_reference",
                "inherited_from_step": None,
            }
            for key in COUNT_KEYS:
                row[key] = 0
            row["first_break_stage"] = None
            row["first_break_count"] = 0
            rows.append(row)
            last_report = row
            continue

        source = "live_pair_report"
        inherited_from = None
        report = step_reports.get(step_id)
        if report is None:
            inherited_from = inherited_steps.get(step_id)
            if inherited_from is None:
                raise KeyError(f"missing step report for {step_id}")
            report = dict(step_reports[inherited_from])
            source = "inherited_runtime_surface"
        row = {
            "step_id": step_id,
            "bound_control_set": bind_row["bound_control_set"],
            "source": source,
            "inherited_from_step": inherited_from,
        }
        for key in COUNT_KEYS:
            row[key] = int(report.get(key, 0))
        stage_name, stage_count = _stage_for_report(report)
        row["first_break_stage"] = stage_name
        row["first_break_count"] = stage_count
        rows.append(row)

        previous_total = 0 if last_report is None else sum(int(last_report.get(key, 0)) for key in COUNT_KEYS[:-1])
        current_total = sum(int(row.get(key, 0)) for key in COUNT_KEYS[:-1])
        if current_total > previous_total and bind_row["bound_control_set"]:
            newly_effective = bind_row["bound_control_set"][-1]
            if newly_effective not in effective_control_set:
                effective_control_set.append(newly_effective)
        last_report = row

    first_break_control = None
    first_break_step = None
    first_break_stage = None
    first_break_count = 0
    for row in rows:
        if row["step_id"] == "B0":
            continue
        if row["first_break_stage"]:
            first_break_step = row["step_id"]
            first_break_stage = row["first_break_stage"]
            first_break_count = int(row["first_break_count"])
            first_break_control = row["bound_control_set"][-1] if row["bound_control_set"] else None
            break

    dominant_row = max(rows[1:], key=lambda item: (int(item["first_break_count"]), sum(int(item[key]) for key in COUNT_KEYS[:-1])))
    dominant_control = dominant_row["bound_control_set"][-1] if dominant_row["bound_control_set"] else None
    dominant_stage = dominant_row["first_break_stage"]

    unexplained_count = 0 if first_break_control and first_break_stage else 1
    return {
        "rows": rows,
        "first_break_control": first_break_control,
        "first_break_step": first_break_step,
        "first_break_stage": first_break_stage,
        "first_break_count": first_break_count,
        "dominant_control": dominant_control,
        "dominant_stage": dominant_stage,
        "effective_control_set": effective_control_set,
        "single_control_root_cause_found": len(effective_control_set) == 1,
        "interaction_root_cause_found": False,
        "unexplained_count": unexplained_count,
    }


def render_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- first_break_control = `{payload['first_break_control']}`",
        f"- first_break_step = `{payload['first_break_step']}`",
        f"- first_break_stage = `{payload['first_break_stage']}`",
        f"- first_break_count = `{payload['first_break_count']}`",
        f"- dominant_control = `{payload['dominant_control']}`",
        f"- dominant_stage = `{payload['dominant_stage']}`",
        f"- effective_control_set = `{', '.join(payload['effective_control_set'])}`",
        f"- single_control_root_cause_found = `{'true' if payload['single_control_root_cause_found'] else 'false'}`",
        f"- interaction_root_cause_found = `{'true' if payload['interaction_root_cause_found'] else 'false'}`",
        f"- unexplained_count = `{payload['unexplained_count']}`",
        "",
        *markdown_table(
            [
                ("step_id", "step_id"),
                ("bound_control_set", "bound_control_set"),
                ("source", "source"),
                ("inherited_from_step", "inherited_from_step"),
                ("preprojection_hash_mismatch_count", "preprojection"),
                ("raw_answer_hash_mismatch_count", "raw_answer"),
                ("response_envelope_hash_mismatch_count", "response_envelope"),
                ("first_break_stage", "first_break_stage"),
                ("first_break_count", "first_break_count"),
            ],
            payload["rows"],
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ27 runtime ladder summary.")
    parser.add_argument("--step-report", action="append", default=[], help="STEP_ID=/abs/path.json")
    parser.add_argument("--inherit-step", action="append", default=[], help="STEP_ID=OTHER_STEP_ID")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    report_paths = _parse_mapping(args.step_report)
    inherited_steps = _parse_mapping(args.inherit_step)
    step_reports = {step_id: load_json(Path(path)) for step_id, path in report_paths.items()}
    payload = build_ladder_payload(step_reports=step_reports, inherited_steps=inherited_steps)
    write_json(args.output_json, payload)
    write_text(args.output_md, render_markdown(payload, title=args.title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
