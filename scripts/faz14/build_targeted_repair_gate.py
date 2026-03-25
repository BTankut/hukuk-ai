#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz14_lib import ALLOWED_CHANGED_FIELDS, IMMUTABLE_FIELDS, load_json, write_json  # noqa: E402


def _changed_fields(row: dict[str, Any]) -> set[str]:
    mapping = {
        "normalized_request_hash_mismatch": "normalized_request_hash",
        "model_request_payload_hash_mismatch": "model_request_payload_hash",
        "generation_contract_hash_mismatch": "generation_contract_hash",
        "preprojection_anchor_mismatch": "preprojection_anchor_hash",
        "cited_projection_hash_mismatch": "cited_projection_hash",
        "citation_set_projection_hash_mismatch": "citation_set_projection_hash",
        "final_mode_mapping_hash_mismatch": "final_mode_mapping_hash",
        "blocked_reason_set_mismatch": "blocked_reason_set_hash",
        "final_answer_payload_hash_mismatch": "final_answer_payload_hash",
        "response_envelope_hash_mismatch": "response_envelope_hash",
        "serialized_output_hash_mismatch": "serialized_output_hash",
        "answer_body_hash_mismatch": "answer_body_hash",
        "citation_body_hash_mismatch": "citation_body_hash",
        "refusal_body_hash_mismatch": "refusal_body_hash",
    }
    return {
        field
        for key, field in mapping.items()
        if int(row.get(key, 0)) == 1
    }


def build_gate(*, targeted_report: dict[str, Any], diff_report: dict[str, Any]) -> dict[str, Any]:
    allowed_changed_field_set = sorted(
        {
            field
            for row in diff_report.get("mismatch_rows", [])
            if isinstance(row, dict)
            for field in _changed_fields(row)
        }
    )
    changed_field_outside_contract_count = sum(
        1 for field in allowed_changed_field_set if field not in ALLOWED_CHANGED_FIELDS
    )

    gate = {
        "family_id": targeted_report["family_id"],
        "normalized_request_hash_mismatch_count": int(targeted_report["normalized_request_hash_mismatch_count"]),
        "model_request_payload_hash_mismatch_count": int(targeted_report["model_request_payload_hash_mismatch_count"]),
        "generation_contract_hash_mismatch_count": int(targeted_report["generation_contract_hash_mismatch_count"]),
        "preprojection_anchor_mismatch_count": int(targeted_report["preprojection_anchor_mismatch_count"]),
        "cited_projection_hash_mismatch_count": int(targeted_report["cited_projection_hash_mismatch_count"]),
        "citation_set_projection_hash_mismatch_count": int(targeted_report["citation_set_projection_hash_mismatch_count"]),
        "final_mode_mapping_hash_mismatch_count": int(targeted_report["final_mode_mapping_hash_mismatch_count"]),
        "blocked_reason_set_mismatch_count": int(targeted_report["blocked_reason_set_mismatch_count"]),
        "final_answer_payload_hash_mismatch_count": int(targeted_report["final_answer_payload_hash_mismatch_count"]),
        "response_envelope_hash_mismatch_count": int(targeted_report["response_envelope_hash_mismatch_count"]),
        "serialized_output_hash_mismatch_count": int(targeted_report["serialized_output_hash_mismatch_count"]),
        "answer_body_hash_mismatch_count": int(targeted_report["answer_body_hash_mismatch_count"]),
        "citation_body_hash_mismatch_count": int(targeted_report["citation_body_hash_mismatch_count"]),
        "refusal_body_hash_mismatch_count": int(targeted_report["refusal_body_hash_mismatch_count"]),
        "runtime_error_count": int(targeted_report["runtime_error_count"]),
        "mismatch_count": int(targeted_report["mismatch_count"]),
        "allowed_changed_field_set": allowed_changed_field_set,
        "changed_field_outside_contract_count": changed_field_outside_contract_count,
        "immutable_field_set": sorted(IMMUTABLE_FIELDS),
    }
    gate["targeted_pass"] = all(
        gate[key] == 0
        for key in (
            "normalized_request_hash_mismatch_count",
            "model_request_payload_hash_mismatch_count",
            "generation_contract_hash_mismatch_count",
            "preprojection_anchor_mismatch_count",
            "cited_projection_hash_mismatch_count",
            "citation_set_projection_hash_mismatch_count",
            "final_mode_mapping_hash_mismatch_count",
            "blocked_reason_set_mismatch_count",
            "final_answer_payload_hash_mismatch_count",
            "response_envelope_hash_mismatch_count",
            "serialized_output_hash_mismatch_count",
            "answer_body_hash_mismatch_count",
            "citation_body_hash_mismatch_count",
            "refusal_body_hash_mismatch_count",
            "runtime_error_count",
            "mismatch_count",
            "changed_field_outside_contract_count",
        )
    )
    return gate


def render_markdown(gate: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_id = `{gate['family_id']}`",
        f"- targeted_pass = `{str(gate['targeted_pass']).lower()}`",
        f"- allowed_changed_field_set = `{gate['allowed_changed_field_set']}`",
        f"- changed_field_outside_contract_count = `{gate['changed_field_outside_contract_count']}`",
        "",
    ]
    for key in (
        "normalized_request_hash_mismatch_count",
        "model_request_payload_hash_mismatch_count",
        "generation_contract_hash_mismatch_count",
        "preprojection_anchor_mismatch_count",
        "cited_projection_hash_mismatch_count",
        "citation_set_projection_hash_mismatch_count",
        "final_mode_mapping_hash_mismatch_count",
        "blocked_reason_set_mismatch_count",
        "final_answer_payload_hash_mismatch_count",
        "response_envelope_hash_mismatch_count",
        "serialized_output_hash_mismatch_count",
        "answer_body_hash_mismatch_count",
        "citation_body_hash_mismatch_count",
        "refusal_body_hash_mismatch_count",
        "runtime_error_count",
        "mismatch_count",
    ):
        lines.append(f"- `{key}` = `{gate[key]}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ14 targeted repair gate.")
    parser.add_argument("--targeted-report", type=Path, required=True)
    parser.add_argument("--diff-report", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", default="FAZ14 RC-L Targeted V3 Final-Mode Repair Gate")
    args = parser.parse_args()

    gate = build_gate(targeted_report=load_json(args.targeted_report), diff_report=load_json(args.diff_report))
    if args.output_json:
        write_json(args.output_json, gate)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(gate, title=args.title), encoding="utf-8")
    return 0 if gate["targeted_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
