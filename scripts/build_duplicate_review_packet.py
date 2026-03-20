#!/usr/bin/env python3
"""Build a review packet for the highest-volume duplicate train questions."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRAIN_FILE = PROJECT_ROOT / "data/finetune/sft/final_train.jsonl"
DEFAULT_INVENTORY_FILE = PROJECT_ROOT / "coordination/training-duplicate-inventory-2026-03-20.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def build_packet(
    train_records: list[dict],
    inventory: dict,
    start_cluster: int,
    cluster_count: int,
    source_inventory: str,
) -> dict:
    grouped_records: dict[str, list[dict]] = defaultdict(list)
    for record in train_records:
        question = _extract_question(record)
        if question:
            grouped_records[question].append(record)

    selected_entries = inventory["groups"][start_cluster - 1:start_cluster - 1 + cluster_count]

    packet_clusters: list[dict] = []
    for cluster_index, entry in enumerate(selected_entries, start=start_cluster):
        question = entry["question"]
        rows = grouped_records[question]

        variants: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            variants[row.get("output", "").strip()].append(row)

        variant_entries = []
        for idx, (output, variant_rows) in enumerate(
            sorted(variants.items(), key=lambda item: (-len(item[1]), -len(item[0]), item[0])),
            start=1,
        ):
            buckets = Counter((row.get("_meta") or {}).get("bucket", "unknown") for row in variant_rows)
            variant_entries.append(
                {
                    "variant_id": f"cluster-{cluster_index:02d}-variant-{idx:02d}",
                    "occurrence_count": len(variant_rows),
                    "citations": _extract_citations(output),
                    "bucket_counts": dict(sorted(buckets.items())),
                    "output": output,
                }
            )

        packet_clusters.append(
            {
                "cluster_id": f"cluster-{cluster_index:02d}",
                "question": question,
                "row_count": entry["count"],
                "distinct_outputs": entry["distinct_outputs"],
                "classification": entry["classification"],
                "variants": variant_entries,
            }
        )

    return {
        "summary": {
            "start_cluster": start_cluster,
            "cluster_count": len(packet_clusters),
            "end_cluster": start_cluster + len(packet_clusters) - 1 if packet_clusters else start_cluster - 1,
            "source_inventory": source_inventory,
            "review_rule": "Select or merge a canonical answer per cluster; do not blind-delete by row.",
        },
        "clusters": packet_clusters,
    }


def _render_markdown(packet: dict) -> str:
    lines = [
        "# Training Duplicate Review Packet",
        "",
        f"- Start cluster: `{packet['summary']['start_cluster']}`",
        f"- End cluster: `{packet['summary']['end_cluster']}`",
        f"- Cluster count: `{packet['summary']['cluster_count']}`",
        f"- Source inventory: `{packet['summary']['source_inventory']}`",
        f"- Rule: {packet['summary']['review_rule']}",
        "",
    ]

    for idx, cluster in enumerate(packet["clusters"], start=1):
        lines.extend(
            [
                f"## Cluster {idx}",
                "",
                f"- Cluster id: `{cluster['cluster_id']}`",
                f"- Question: {cluster['question']}",
                f"- Rows: `{cluster['row_count']}`",
                f"- Distinct outputs: `{cluster['distinct_outputs']}`",
                f"- Classification: `{cluster['classification']}`",
                "",
            ]
        )

        for variant in cluster["variants"]:
            citations = ", ".join(variant["citations"]) if variant["citations"] else "(none)"
            lines.extend(
                [
                    f"### Variant `{variant['variant_id']}`",
                    "",
                    f"- Occurrence count: `{variant['occurrence_count']}`",
                    f"- Citations: {citations}",
                    "",
                    "```text",
                    variant["output"],
                    "```",
                    "",
                ]
            )

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build duplicate review packet from train set.")
    parser.add_argument("--train-file", default=str(DEFAULT_TRAIN_FILE))
    parser.add_argument("--inventory-file", default=str(DEFAULT_INVENTORY_FILE))
    parser.add_argument("--start-cluster", type=int, default=1)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--md-out", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    train_file = Path(args.train_file)
    inventory_file = Path(args.inventory_file)

    packet = build_packet(
        train_records=_load_jsonl(train_file),
        inventory=_load_json(inventory_file),
        start_cluster=args.start_cluster,
        cluster_count=args.count,
        source_inventory=str(inventory_file.relative_to(PROJECT_ROOT)),
    )

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(_render_markdown(packet), encoding="utf-8")

    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    print(json.dumps(packet["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
