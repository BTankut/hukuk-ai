#!/usr/bin/env python3
"""Audit question-level duplicates inside the active SFT train set."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRAIN_FILE = PROJECT_ROOT / "data/finetune/sft/final_train.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _extract_question(record: dict) -> str:
    raw = record.get("input") or record.get("question") or ""
    if not isinstance(raw, str):
        return ""
    if "\n\nSORU:" in raw:
        return raw.split("\n\nSORU:", 1)[1].strip()
    if "SORU:" in raw:
        return raw.split("SORU:", 1)[1].strip()
    return raw.strip()


def _extract_citations(answer: str) -> list[str]:
    citations: list[str] = []
    marker = "[Kaynak:"
    for part in answer.split(marker)[1:]:
        citation = part.split("]", 1)[0].strip()
        if citation and citation not in citations:
            citations.append(citation)
    return citations


def _classify_group(count: int, distinct_outputs: int) -> str:
    if distinct_outputs == 1:
        return "exact_answer_repeats_only"
    if distinct_outputs == count:
        return "all_rows_unique_outputs"
    return "mixed_repeat_and_variant_outputs"


def build_inventory(records: list[dict], sample_size: int) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        question = _extract_question(record)
        if question:
            groups[question].append(record)

    entries: list[dict] = []
    class_counts: Counter[str] = Counter()

    for question, rows in groups.items():
        if len(rows) <= 1:
            continue

        outputs = [row.get("output", "").strip() for row in rows]
        distinct_outputs = len(set(outputs))
        classification = _classify_group(len(rows), distinct_outputs)
        class_counts[classification] += 1

        bucket_counts = Counter((row.get("_meta") or {}).get("bucket", "unknown") for row in rows)
        sample_rows = []
        for row in rows[:sample_size]:
            output = row.get("output", "").strip()
            sample_rows.append(
                {
                    "output_preview": output.replace("\n", " ")[:280],
                    "citations": _extract_citations(output),
                    "bucket": (row.get("_meta") or {}).get("bucket", "unknown"),
                }
            )

        entries.append(
            {
                "question": question,
                "count": len(rows),
                "distinct_outputs": distinct_outputs,
                "duplicate_excess_rows": len(rows) - 1,
                "classification": classification,
                "bucket_counts": dict(sorted(bucket_counts.items())),
                "sample_rows": sample_rows,
            }
        )

    entries.sort(key=lambda item: (-item["count"], -item["distinct_outputs"], item["question"]))
    duplicate_excess_rows = sum(entry["duplicate_excess_rows"] for entry in entries)

    return {
        "summary": {
            "total_records": len(records),
            "unique_questions": len(groups),
            "duplicate_question_groups": len(entries),
            "duplicate_excess_rows": duplicate_excess_rows,
            "classification_counts": dict(sorted(class_counts.items())),
        },
        "groups": entries,
    }


def _render_markdown(report: dict) -> str:
    summary = report["summary"]
    groups = report["groups"]

    lines = [
        "# Training Duplicate Inventory",
        "",
        f"- Total records: `{summary['total_records']}`",
        f"- Unique questions: `{summary['unique_questions']}`",
        f"- Duplicate question groups: `{summary['duplicate_question_groups']}`",
        f"- Duplicate excess rows: `{summary['duplicate_excess_rows']}`",
        "",
        "## Classification",
        "",
    ]

    for name, count in summary["classification_counts"].items():
        lines.append(f"- `{name}`: `{count}`")

    if summary["classification_counts"].get("exact_answer_repeats_only", 0) == 0:
        lines.extend(
            [
                "",
                "No duplicate group is a pure exact-answer repeat. Cleanup requires canonicalization, not only blind row deletion.",
            ]
        )

    lines.extend(["", "## Top Groups", ""])
    for entry in groups[:15]:
        lines.append(
            f"- `{entry['count']}x` / `{entry['distinct_outputs']}` outputs / `{entry['classification']}`: {entry['question']}"
        )

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit duplicate questions in the train set.")
    parser.add_argument("--train-file", default=str(DEFAULT_TRAIN_FILE))
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--md-out", required=True)
    parser.add_argument("--sample-size", type=int, default=3)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    train_file = Path(args.train_file)
    report = build_inventory(_load_jsonl(train_file), sample_size=args.sample_size)

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(_render_markdown(report), encoding="utf-8")

    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
