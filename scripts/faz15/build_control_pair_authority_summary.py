#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz15_lib import load_json, stable_hash, write_json  # noqa: E402


EXPECTED_BY_FAMILY = {
    "faz1-50": {
        "mismatch_count": 0,
        "family_metric_delta_zero": True,
    },
    "v2-95": {
        "mismatch_count": 0,
        "family_metric_delta_zero": True,
    },
    "v3-170": {
        "mismatch_count": 6,
        "family_metric_delta_zero": True,
        "final_mode_mapping_hash_mismatch_count": 6,
        "blocked_reason_set_mismatch_count": 6,
        "response_envelope_hash_mismatch_count": 6,
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "cited_projection_hash_mismatch_count": 0,
        "citation_set_projection_hash_mismatch_count": 0,
        "final_answer_payload_hash_mismatch_count": 0,
        "serialized_output_hash_mismatch_count": 0,
    },
}


def family_pass(report: dict[str, Any]) -> tuple[bool, list[str]]:
    family_id = str(report["family_id"])
    expected = EXPECTED_BY_FAMILY[family_id]
    failures: list[str] = []
    for key, expected_value in expected.items():
        actual = report.get(key)
        if actual != expected_value:
            failures.append(f"{key}: expected={expected_value!r} actual={actual!r}")
    return not failures, failures


def build_outputs(reports: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    family_rows = []
    for report in sorted(reports, key=lambda item: item["family_id"]):
        passed, failures = family_pass(report)
        family_rows.append(
            {
                "family_id": report["family_id"],
                "mismatch_count": int(report["mismatch_count"]),
                "family_metric_delta_zero": bool(report["family_metric_delta_zero"]),
                "actual": {
                    key: report.get(key)
                    for key in EXPECTED_BY_FAMILY[str(report["family_id"])].keys()
                },
                "pass": passed,
                "failures": failures,
            }
        )
    summary = {
        "family_count": len(family_rows),
        "families": family_rows,
        "control_pair_authority_match": all(row["pass"] for row in family_rows),
    }
    summary["report_hash"] = stable_hash(summary)
    reconciliation = {
        "control_pair_authority_match": summary["control_pair_authority_match"],
        "families": family_rows,
    }
    reconciliation["report_hash"] = stable_hash(reconciliation)
    return summary, reconciliation


def render_summary_md(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_count = `{summary['family_count']}`",
        f"- control_pair_authority_match = `{str(summary['control_pair_authority_match']).lower()}`",
        "",
        "| family | pass | mismatch_count | family_metric_delta_zero |",
        "| --- | --- | ---: | --- |",
    ]
    for row in summary["families"]:
        lines.append(
            f"| {row['family_id']} | {str(row['pass']).lower()} | {row['mismatch_count']} | "
            f"{str(row['family_metric_delta_zero']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_reconciliation_md(reconciliation: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- control_pair_authority_match = `{str(reconciliation['control_pair_authority_match']).lower()}`",
        "",
    ]
    for row in reconciliation["families"]:
        lines.append(f"## {row['family_id']}")
        lines.append("")
        if row["pass"]:
            lines.append("- durum = `pass`")
        else:
            lines.append("- durum = `fail`")
            for failure in row["failures"]:
                lines.append(f"- `{failure}`")
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ15 RC-G vs RC-J control authority summary.")
    parser.add_argument("--report-json", type=Path, action="append", required=True)
    parser.add_argument("--summary-output-json", type=Path, required=True)
    parser.add_argument("--summary-output-md", type=Path, required=True)
    parser.add_argument("--reconciliation-output-json", type=Path, required=True)
    parser.add_argument("--reconciliation-output-md", type=Path, required=True)
    parser.add_argument("--summary-title", required=True)
    parser.add_argument("--reconciliation-title", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reports = [load_json(path) for path in args.report_json]
    summary, reconciliation = build_outputs(reports)
    write_json(args.summary_output_json, summary)
    write_json(args.reconciliation_output_json, reconciliation)
    args.summary_output_md.write_text(render_summary_md(summary, title=args.summary_title), encoding="utf-8")
    args.reconciliation_output_md.write_text(
        render_reconciliation_md(reconciliation, title=args.reconciliation_title),
        encoding="utf-8",
    )
    return 0 if summary["control_pair_authority_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
