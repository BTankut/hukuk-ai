#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAZ5 delta proof between RC-D and RC-F.")
    parser.add_argument("--divergence-baseline-jsonl", required=True, type=Path)
    parser.add_argument("--legacy-baseline-jsonl", required=True, type=Path)
    parser.add_argument("--faz1-rc-d", required=True, type=Path)
    parser.add_argument("--v2-rc-d", required=True, type=Path)
    parser.add_argument("--v3-rc-d", required=True, type=Path)
    parser.add_argument("--faz1-rc-f", required=True, type=Path)
    parser.add_argument("--v2-rc-f", required=True, type=Path)
    parser.add_argument("--v3-rc-f", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# FAZ 5 Delta Proof",
        "",
        f"- tracked_record_count: `{payload['tracked_record_count']}`",
        f"- changed_output_count: `{payload['changed_output_count']}`",
        f"- beneficial_change_count: `{payload['beneficial_change_count']}`",
        f"- overall_pass: `{str(payload['overall_pass']).lower()}`",
        "",
        "## Sample",
        "",
    ]
    for item in payload["sample"]:
        lines.append(
            f"- {item['family']} {item['question_id']}: `{item['rc_d_mode']} -> {item['rc_f_mode']}` "
            f"(citation `{item['rc_d_citation']} -> {item['rc_f_citation']}`, correct_source `{item['rc_d_correct_source']} -> {item['rc_f_correct_source']}`)"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    tracked_ids = {
        (str(row["family"]), str(row["question_id"]))
        for row in [*load_jsonl(args.divergence_baseline_jsonl), *load_jsonl(args.legacy_baseline_jsonl)]
    }
    rc_d_reports = {
        "faz1-50": load_json(args.faz1_rc_d),
        "v2-95": load_json(args.v2_rc_d),
        "v3-170": load_json(args.v3_rc_d),
    }
    rc_f_reports = {
        "faz1-50": load_json(args.faz1_rc_f),
        "v2-95": load_json(args.v2_rc_f),
        "v3-170": load_json(args.v3_rc_f),
    }
    rc_d_rows = {
        family: {row["question_id"]: row for row in payload["per_question"]}
        for family, payload in rc_d_reports.items()
    }
    rc_f_rows = {
        family: {row["question_id"]: row for row in payload["per_question"]}
        for family, payload in rc_f_reports.items()
    }

    changed_output_count = 0
    beneficial_change_count = 0
    sample: list[dict[str, object]] = []
    for family, question_id in sorted(tracked_ids):
        rc_d_row = rc_d_rows[family][question_id]
        rc_f_row = rc_f_rows[family][question_id]
        changed = any(
            [
                (rc_d_row.get("final_mode") != rc_f_row.get("final_mode")),
                (str(rc_d_row.get("answer_text") or "") != str(rc_f_row.get("answer_text") or "")),
                (list(rc_d_row.get("cited_sources") or []) != list(rc_f_row.get("cited_sources") or [])),
            ]
        )
        if not changed:
            continue
        changed_output_count += 1

        beneficial = any(
            [
                float(rc_f_row.get("correct_source_rate") or 0.0) > float(rc_d_row.get("correct_source_rate") or 0.0),
                bool(rc_f_row.get("has_citation")) and not bool(rc_d_row.get("has_citation")),
                bool(rc_f_row.get("refusal_correct")) and not bool(rc_d_row.get("refusal_correct")),
                rc_d_row.get("final_mode") in {"refusal", "partial"} and rc_f_row.get("final_mode") == "answer",
            ]
        )
        if beneficial:
            beneficial_change_count += 1
        if len(sample) < 15:
            sample.append(
                {
                    "family": family,
                    "question_id": question_id,
                    "rc_d_mode": rc_d_row.get("final_mode"),
                    "rc_f_mode": rc_f_row.get("final_mode"),
                    "rc_d_citation": bool(rc_d_row.get("has_citation")),
                    "rc_f_citation": bool(rc_f_row.get("has_citation")),
                    "rc_d_correct_source": float(rc_d_row.get("correct_source_rate") or 0.0),
                    "rc_f_correct_source": float(rc_f_row.get("correct_source_rate") or 0.0),
                }
            )

    payload = {
        "tracked_record_count": len(tracked_ids),
        "changed_output_count": changed_output_count,
        "beneficial_change_count": beneficial_change_count,
        "overall_pass": changed_output_count >= 25 and beneficial_change_count >= 20,
        "sample": sample,
    }
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
