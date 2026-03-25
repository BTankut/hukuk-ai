#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz14_lib import ALLOWED_CHANGED_FIELDS, load_json, write_json  # noqa: E402


MISMATCH_TO_FIELD = {
    "final_mode_mapping_hash_mismatch": "final_mode_mapping_hash",
    "blocked_reason_set_mismatch": "blocked_reason_set_hash",
    "response_envelope_hash_mismatch": "response_envelope_hash",
    "serialized_output_hash_mismatch": "serialized_output_hash",
    "normalized_request_hash_mismatch": "normalized_request_hash",
    "model_request_payload_hash_mismatch": "model_request_payload_hash",
    "generation_contract_hash_mismatch": "generation_contract_hash",
    "preprojection_anchor_mismatch": "preprojection_anchor_hash",
    "cited_projection_hash_mismatch": "cited_projection_hash",
    "citation_set_projection_hash_mismatch": "citation_set_projection_hash",
    "final_answer_payload_hash_mismatch": "final_answer_payload_hash",
    "answer_body_hash_mismatch": "answer_body_hash",
    "citation_body_hash_mismatch": "citation_body_hash",
    "refusal_body_hash_mismatch": "refusal_body_hash",
}


def build_gate(*, targeted_report: dict[str, Any], diff_report: dict[str, Any]) -> dict[str, Any]:
    changed_fields: set[str] = set()
    for row in diff_report.get("mismatch_rows", []):
        if not isinstance(row, dict):
            continue
        for mismatch_key, field_name in MISMATCH_TO_FIELD.items():
            if int(row.get(mismatch_key, 0)) == 1:
                changed_fields.add(field_name)

    allowed_changed_field_set = sorted(field for field in changed_fields if field in ALLOWED_CHANGED_FIELDS)
    outside_fields = sorted(field for field in changed_fields if field not in ALLOWED_CHANGED_FIELDS)
    targeted_pass = (
        int(targeted_report.get("normalized_request_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("model_request_payload_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("generation_contract_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("preprojection_anchor_mismatch_count", 0)) == 0
        and int(targeted_report.get("cited_projection_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("citation_set_projection_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("final_mode_mapping_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("blocked_reason_set_mismatch_count", 0)) == 0
        and int(targeted_report.get("final_answer_payload_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("response_envelope_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("serialized_output_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("answer_body_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("citation_body_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("refusal_body_hash_mismatch_count", 0)) == 0
        and int(targeted_report.get("runtime_error_count", 0)) == 0
        and int(targeted_report.get("mismatch_count", 0)) == 0
        and len(outside_fields) == 0
    )
    gate = {
        "family_id": targeted_report.get("family_id"),
        "question_count": int(targeted_report.get("question_count", 0)),
        "runtime_error_count": int(targeted_report.get("runtime_error_count", 0)),
        "mismatch_count": int(targeted_report.get("mismatch_count", 0)),
        "normalized_request_hash_mismatch_count": int(targeted_report.get("normalized_request_hash_mismatch_count", 0)),
        "model_request_payload_hash_mismatch_count": int(targeted_report.get("model_request_payload_hash_mismatch_count", 0)),
        "generation_contract_hash_mismatch_count": int(targeted_report.get("generation_contract_hash_mismatch_count", 0)),
        "preprojection_anchor_mismatch_count": int(targeted_report.get("preprojection_anchor_mismatch_count", 0)),
        "cited_projection_hash_mismatch_count": int(targeted_report.get("cited_projection_hash_mismatch_count", 0)),
        "citation_set_projection_hash_mismatch_count": int(targeted_report.get("citation_set_projection_hash_mismatch_count", 0)),
        "final_mode_mapping_hash_mismatch_count": int(targeted_report.get("final_mode_mapping_hash_mismatch_count", 0)),
        "blocked_reason_set_mismatch_count": int(targeted_report.get("blocked_reason_set_mismatch_count", 0)),
        "final_answer_payload_hash_mismatch_count": int(targeted_report.get("final_answer_payload_hash_mismatch_count", 0)),
        "response_envelope_hash_mismatch_count": int(targeted_report.get("response_envelope_hash_mismatch_count", 0)),
        "serialized_output_hash_mismatch_count": int(targeted_report.get("serialized_output_hash_mismatch_count", 0)),
        "answer_body_hash_mismatch_count": int(targeted_report.get("answer_body_hash_mismatch_count", 0)),
        "citation_body_hash_mismatch_count": int(targeted_report.get("citation_body_hash_mismatch_count", 0)),
        "refusal_body_hash_mismatch_count": int(targeted_report.get("refusal_body_hash_mismatch_count", 0)),
        "allowed_changed_field_set": allowed_changed_field_set,
        "changed_field_outside_contract_count": len(outside_fields),
        "changed_field_outside_contract": outside_fields,
        "targeted_pass": targeted_pass,
    }
    return gate


def render_markdown(gate: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- family_id = `{gate['family_id']}`",
        f"- question_count = `{gate['question_count']}`",
        f"- runtime_error_count = `{gate['runtime_error_count']}`",
        f"- mismatch_count = `{gate['mismatch_count']}`",
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
    ):
        lines.append(f"- `{key}` = `{gate[key]}`")
    if gate["changed_field_outside_contract"]:
        lines.extend(["", "## Outside Contract", ""])
        for field in gate["changed_field_outside_contract"]:
            lines.append(f"- `{field}`")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ14 targeted repair gate.")
    parser.add_argument("--targeted-report", type=Path, required=True)
    parser.add_argument("--diff-report", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--title", default="FAZ14 RC-L Targeted V3 Final-Mode Repair Gate")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    gate = build_gate(
        targeted_report=load_json(args.targeted_report),
        diff_report=load_json(args.diff_report),
    )
    write_json(args.output_json, gate)
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(gate, title=args.title), encoding="utf-8")
    return 0 if gate["targeted_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
