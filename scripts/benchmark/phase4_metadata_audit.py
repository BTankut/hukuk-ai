#!/usr/bin/env python3
"""Audit Phase 4 canonical metadata enrichment coverage.

This script compares raw Milvus metadata with the runtime enrichment layer used
by the gateway. It does not mutate Milvus; it reports which gaps can be closed
from the canonical article_rows catalog and which remain corpus/backlog work.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
API_SRC = REPO_ROOT / "api-gateway/src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from rag.source_catalog import enrich_metadata_with_source_title  # noqa: E402


DEFAULT_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_04_metadata_audit.md"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_04_metadata_audit.csv"

CANONICAL_FIELDS = {
    "full_title": ("full_title", "source_title", "belge_adi", "kanun_adi", "law_name", "title"),
    "issuer": ("issuer", "kurum", "kurum_adi", "duzenleyen_kurum", "bakanlik", "ilgili_kurum"),
    "official_gazette_no": ("official_gazette_no", "official_gazette_number", "resmi_gazete_sayi"),
    "official_gazette_date": ("official_gazette_date", "resmi_gazete_tarih"),
    "effective_start": ("effective_start", "yururluk_baslangic"),
    "effective_end": ("effective_end", "yururluk_bitis"),
    "canonical_identifier_display": ("canonical_identifier_display", "display_citation", "source_id"),
    "source_family_canonical": ("source_family_canonical", "belge_turu", "source_type"),
    "effective_state": ("effective_state", "source_validity"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", "http://127.0.0.1:19530"))
    parser.add_argument("--collection", default=os.getenv("MILVUS_COLLECTION", DEFAULT_COLLECTION))
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--max-rows", type=int, help="Optional cap for quick smoke runs.")
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    return parser.parse_args()


def has_any(metadata: dict[str, Any], aliases: tuple[str, ...]) -> bool:
    for key in aliases:
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def family_value(metadata: dict[str, Any]) -> str:
    value = (
        metadata.get("source_family_canonical")
        or metadata.get("belge_turu")
        or metadata.get("source_type")
        or "UNKNOWN"
    )
    return str(value or "UNKNOWN").strip().lower() or "UNKNOWN"


def iter_metadata_rows(client: Any, collection: str, batch_size: int, max_rows: int | None) -> Any:
    iterator = client.query_iterator(
        collection_name=collection,
        batch_size=batch_size,
        output_fields=["id", "metadata"],
    )
    seen = 0
    try:
        while True:
            batch = iterator.next()
            if not batch:
                break
            for row in batch:
                metadata = row.get("metadata") if isinstance(row, dict) else None
                if not isinstance(metadata, dict):
                    metadata = {}
                yield row.get("id") if isinstance(row, dict) else None, metadata
                seen += 1
                if max_rows is not None and seen >= max_rows:
                    return
    finally:
        iterator.close()


def scan(args: argparse.Namespace) -> dict[str, Any]:
    from pymilvus import MilvusClient

    client = MilvusClient(uri=args.milvus_uri)
    stats = client.get_collection_stats(collection_name=args.collection)
    collection_row_count = int(stats.get("row_count", stats.get("num_entities", -1)))

    rows = 0
    raw_missing: dict[str, Counter[str]] = defaultdict(Counter)
    enriched_missing: dict[str, Counter[str]] = defaultdict(Counter)
    recovered: dict[str, Counter[str]] = defaultdict(Counter)
    family_counts: Counter[str] = Counter()
    global_raw_missing: Counter[str] = Counter()
    global_enriched_missing: Counter[str] = Counter()
    global_recovered: Counter[str] = Counter()

    for _row_id, raw_metadata in iter_metadata_rows(client, args.collection, args.batch_size, args.max_rows):
        rows += 1
        enriched = enrich_metadata_with_source_title(raw_metadata)
        family = family_value(enriched)
        family_counts[family] += 1
        for field, aliases in CANONICAL_FIELDS.items():
            raw_has = has_any(raw_metadata, aliases)
            enriched_has = has_any(enriched, (field, *aliases))
            if not raw_has:
                raw_missing[family][field] += 1
                global_raw_missing[field] += 1
            if not enriched_has:
                enriched_missing[family][field] += 1
                global_enriched_missing[field] += 1
            if not raw_has and enriched_has:
                recovered[family][field] += 1
                global_recovered[field] += 1

    family_rows: list[dict[str, Any]] = []
    for family in sorted(family_counts):
        total = family_counts[family]
        row: dict[str, Any] = {"family": family, "rows": total}
        for field in CANONICAL_FIELDS:
            row[f"raw_missing_{field}"] = raw_missing[family][field]
            row[f"raw_missing_{field}_pct"] = round(raw_missing[family][field] / total, 4) if total else 0.0
            row[f"enriched_missing_{field}"] = enriched_missing[family][field]
            row[f"enriched_missing_{field}_pct"] = round(enriched_missing[family][field] / total, 4) if total else 0.0
            row[f"recovered_{field}"] = recovered[family][field]
        family_rows.append(row)

    return {
        "milvus_uri": args.milvus_uri,
        "collection": args.collection,
        "collection_row_count": collection_row_count,
        "scanned_rows": rows,
        "max_rows": args.max_rows,
        "family_counts": dict(family_counts.most_common()),
        "raw_missing": dict(global_raw_missing),
        "enriched_missing": dict(global_enriched_missing),
        "recovered": dict(global_recovered),
        "rows": family_rows,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["family", "rows"]
    for field in CANONICAL_FIELDS:
        fieldnames.extend(
            [
                f"raw_missing_{field}",
                f"raw_missing_{field}_pct",
                f"enriched_missing_{field}",
                f"enriched_missing_{field}_pct",
                f"recovered_{field}",
            ]
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pct(value: int, total: int) -> str:
    return f"{value / total:.1%}" if total else "0.0%"


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    total = int(summary["scanned_rows"])
    lines = [
        "# Phase 4 Metadata Enrichment Audit",
        "",
        f"- milvus_uri: `{summary['milvus_uri']}`",
        f"- collection: `{summary['collection']}`",
        f"- collection_row_count: {summary['collection_row_count']}",
        f"- scanned_rows: {summary['scanned_rows']}",
        f"- max_rows: {summary['max_rows']}",
        "",
        "## Global Raw vs Enriched Coverage",
        "| field | raw missing | enriched missing | recovered by runtime catalog |",
        "| --- | ---: | ---: | ---: |",
    ]
    for field in CANONICAL_FIELDS:
        raw = int(summary["raw_missing"].get(field, 0))
        enriched = int(summary["enriched_missing"].get(field, 0))
        recovered = int(summary["recovered"].get(field, 0))
        lines.append(
            f"| {field} | {raw} ({pct(raw, total)}) | {enriched} ({pct(enriched, total)}) | {recovered} |"
        )

    lines.extend(["", "## Family Row Counts"])
    for family, count in summary["family_counts"].items():
        lines.append(f"- {family}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- This report measures runtime enrichment, not a destructive Milvus reindex.",
            "- Fields still missing after enrichment are corpus/source-acquisition or deeper canonical metadata backlog.",
            "- Retrieval and verification code should prefer enriched canonical fields before raw aliases.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    summary = scan(args)
    write_csv(args.out_csv, summary["rows"])
    write_markdown(args.out_md, summary)
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
