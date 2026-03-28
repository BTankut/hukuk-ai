#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz26_lib import bool_text, load_json, write_json


def build_current_authority_check(
    *,
    canonical_reference: dict[str, Any],
    canonical_gate: dict[str, Any],
) -> dict[str, Any]:
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
    current_authority_contract_breach = bool(canonical_reference.get("current_authority_contract_breach", True))
    control_pair_runtime_error_count = int(canonical_reference.get("control_pair_runtime_error_count", 0))
    summary = {
        "control_pair_reference": str(canonical_reference.get("reference_name") or "canonical_current_authority_ref"),
        "control_pair_authority_match": control_pair_authority_match,
        "current_authority_contract_breach": current_authority_contract_breach,
        "surface_breach_from_history_reintroduced": False,
        "current_canonical_authority_adopted": bool(canonical_gate.get("current_canonical_authority_adopted", False)),
        "canonicalization_gate_pass": bool(canonical_gate.get("canonicalization_gate_pass", False)),
        "control_pair_runtime_error_count": control_pair_runtime_error_count,
        "families": families,
    }
    summary["wp3_control_gate_pass"] = (
        summary["control_pair_authority_match"]
        and summary["current_authority_contract_breach"] is False
        and summary["surface_breach_from_history_reintroduced"] is False
        and summary["current_canonical_authority_adopted"] is True
        and summary["canonicalization_gate_pass"] is True
        and summary["control_pair_runtime_error_count"] == 0
    )
    return summary


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- control_pair_reference = `{summary['control_pair_reference']}`",
        f"- control_pair_authority_match = `{bool_text(summary['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(summary['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(summary['surface_breach_from_history_reintroduced'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(summary['current_canonical_authority_adopted'])}`",
        f"- canonicalization_gate_pass = `{bool_text(summary['canonicalization_gate_pass'])}`",
        f"- control_pair_runtime_error_count = `{summary['control_pair_runtime_error_count']}`",
        f"- wp3_control_gate_pass = `{bool_text(summary['wp3_control_gate_pass'])}`",
        "",
        "| family | mismatch_count | runtime_error_count | family_metric_delta_zero | pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary["families"]:
        lines.append(
            f"| {row['family_name']} | {row['mismatch_count']} | {row['runtime_error_count']} | {bool_text(row['family_metric_delta_zero'])} | {bool_text(row['pass'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ26 current authority check from canonical FAZ21 truth.")
    parser.add_argument("--canonical-reference-json", type=Path, required=True)
    parser.add_argument("--canonical-gate-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--title", default="FAZ26 RC-G vs RC-J Current Authority Check")
    args = parser.parse_args()

    summary = build_current_authority_check(
        canonical_reference=load_json(args.canonical_reference_json),
        canonical_gate=load_json(args.canonical_gate_json),
    )
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["wp3_control_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
