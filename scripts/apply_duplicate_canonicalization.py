#!/usr/bin/env python3
"""Apply duplicate-question canonicalization selections to a train JSONL file."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


def _extract_question(record: dict) -> str:
    raw = record.get("input") or record.get("question") or ""
    if not isinstance(raw, str):
        return ""
    if "\n\nSORU:" in raw:
        return raw.split("\n\nSORU:", 1)[1].strip()
    if "SORU:" in raw:
        return raw.split("SORU:", 1)[1].strip()
    return raw.strip()


def _duplicate_summary(records: list[dict]) -> dict[str, int]:
    questions = [_extract_question(record) for record in records]
    counts = Counter(question for question in questions if question)
    duplicate_groups = sum(1 for count in counts.values() if count > 1)
    duplicate_excess_rows = sum(count - 1 for count in counts.values() if count > 1)
    return {
        "total_records": len(records),
        "unique_questions": len(counts),
        "duplicate_question_groups": duplicate_groups,
        "duplicate_excess_rows": duplicate_excess_rows,
    }


def apply_manifest(records: list[dict], packet: dict, manifest: dict) -> tuple[list[dict], dict]:
    packet_by_cluster = {cluster["cluster_id"]: cluster for cluster in packet["clusters"]}
    selection_by_question: dict[str, dict] = {}

    for selection in manifest["selections"]:
        cluster = packet_by_cluster[selection["cluster_id"]]
        question = selection["question"]
        selected_variant_id = selection["selected_variant_id"]

        selected_output = None
        for variant in cluster["variants"]:
            if variant["variant_id"] == selected_variant_id:
                selected_output = variant["output"]
                break
        if selected_output is None:
            raise ValueError(f"Selected variant not found: {selected_variant_id}")

        selection_by_question[question] = {
            "cluster_id": selection["cluster_id"],
            "selected_variant_id": selected_variant_id,
            "selected_output": selected_output,
        }

    grouped: dict[str, list[dict]] = {}
    for record in records:
        grouped.setdefault(_extract_question(record), []).append(record)

    rewritten: list[dict] = []
    applied_clusters = 0

    for question, rows in grouped.items():
        selection = selection_by_question.get(question)
        if selection is None:
            rewritten.extend(rows)
            continue

        applied_clusters += 1
        chosen = None
        for row in rows:
            if row.get("output", "").strip() == selection["selected_output"]:
                chosen = dict(row)
                break
        if chosen is None:
            raise ValueError(f"No row matched selected output for question: {question}")

        meta = dict(chosen.get("_meta") or {})
        meta["canonicalized_duplicate_cluster"] = selection["cluster_id"]
        meta["selected_variant_id"] = selection["selected_variant_id"]
        meta["collapsed_from_rows"] = len(rows)
        chosen["_meta"] = meta
        rewritten.append(chosen)

    stats = {
        "clusters_requested": len(selection_by_question),
        "clusters_applied": applied_clusters,
        "before": _duplicate_summary(records),
        "after": _duplicate_summary(rewritten),
    }
    return rewritten, stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply duplicate canonicalization manifest.")
    parser.add_argument("--train-file", required=True)
    parser.add_argument("--packet-file", required=True)
    parser.add_argument("--manifest-file", required=True)
    parser.add_argument("--output-file")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    records = _load_jsonl(Path(args.train_file))
    packet = _load_json(Path(args.packet_file))
    manifest = _load_json(Path(args.manifest_file))

    rewritten, stats = apply_manifest(records, packet, manifest)

    if not args.dry_run:
        if not args.output_file:
            raise SystemExit("--output-file is required unless --dry-run is used")
        _write_jsonl(Path(args.output_file), rewritten)
        print(f"Wrote {args.output_file}")

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
