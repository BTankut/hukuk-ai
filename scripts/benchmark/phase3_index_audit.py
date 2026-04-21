#!/usr/bin/env python3
"""Audit Milvus index metadata coverage for Phase 3 retrieval hardening."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_03_index_audit.md"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_03_index_audit.csv"

FIELD_ALIASES = {
    "family": ("belge_turu", "source_type", "family"),
    "title": ("source_title", "belge_adi", "kanun_adi", "law_name", "title", "official_title"),
    "short_title": ("belge_kisa_adi", "kanun_kisa_adi", "law_short_name"),
    "issuer": ("issuer", "kurum", "kurum_adi", "duzenleyen_kurum", "bakanlik", "ilgili_kurum"),
    "identifier": ("source_id", "belge_no", "kanun_no", "law_no", "display_citation"),
    "official_gazette_date": ("resmi_gazete_tarih", "official_gazette_date"),
    "official_gazette_number": ("resmi_gazete_sayi", "official_gazette_number"),
    "effective_start": ("yururluk_baslangic", "effective_start"),
    "effective_end": ("yururluk_bitis", "effective_end"),
    "article": ("madde_no", "article_no", "section_no"),
    "section": ("fikra_no", "paragraph_no", "section"),
}

KNOWN_FAMILIES = {
    "kanun",
    "mulga_kanun",
    "khk",
    "cb_karar",
    "cb_kararname",
    "cb_genelge",
    "cb_yonetmelik",
    "yonetmelik",
    "tuzuk",
    "teblig",
    "kky",
    "uy",
}

ACTIVE_END_SENTINELS = {"", "9999-12-31", "9999-01-01", "none", "null"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", "http://127.0.0.1:19530"))
    parser.add_argument("--collection", default=os.getenv("MILVUS_COLLECTION", DEFAULT_COLLECTION))
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--max-rows", type=int, help="Optional cap for quick smoke runs.")
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    return parser.parse_args()


def first_present(metadata: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def is_present(metadata: dict[str, Any], logical_field: str) -> bool:
    return first_present(metadata, FIELD_ALIASES[logical_field]) is not None


def family_value(metadata: dict[str, Any]) -> str:
    value = first_present(metadata, FIELD_ALIASES["family"])
    return str(value or "UNKNOWN").strip().lower() or "UNKNOWN"


def is_effectively_active(metadata: dict[str, Any]) -> bool:
    if metadata.get("mulga") is True:
        return False
    end = str(first_present(metadata, FIELD_ALIASES["effective_end"]) or "").strip().lower()
    return end in ACTIVE_END_SENTINELS


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


def empty_field_counter() -> Counter[str]:
    return Counter({field: 0 for field in FIELD_ALIASES})


def scan_index(args: argparse.Namespace) -> dict[str, Any]:
    from pymilvus import MilvusClient

    client = MilvusClient(uri=args.milvus_uri)
    stats = client.get_collection_stats(collection_name=args.collection)
    collection_row_count = int(stats.get("row_count", stats.get("num_entities", -1)))

    per_family: dict[str, Counter[str]] = defaultdict(Counter)
    missing_per_family: dict[str, Counter[str]] = defaultdict(empty_field_counter)
    noisy_per_family: dict[str, Counter[str]] = defaultdict(Counter)
    metadata_keys: Counter[str] = Counter()
    family_values: Counter[str] = Counter()

    scanned = 0
    for _row_id, metadata in iter_metadata_rows(client, args.collection, args.batch_size, args.max_rows):
        scanned += 1
        family = family_value(metadata)
        family_values[family] += 1
        per_family[family]["rows"] += 1
        metadata_keys.update(metadata.keys())

        for logical_field in FIELD_ALIASES:
            if not is_present(metadata, logical_field):
                missing_per_family[family][logical_field] += 1

        if family not in KNOWN_FAMILIES:
            noisy_per_family[family]["unknown_family_value"] += 1
        if not is_present(metadata, "title") and is_present(metadata, "short_title"):
            noisy_per_family[family]["title_missing_but_short_title_present"] += 1
        if metadata.get("mulga") is True and is_effectively_active(metadata):
            noisy_per_family[family]["mulga_true_active_end"] += 1
        if metadata.get("mulga") is False and not is_effectively_active(metadata):
            noisy_per_family[family]["mulga_false_inactive_end"] += 1
        if not is_present(metadata, "article"):
            noisy_per_family[family]["missing_article_granularity"] += 1

    rows: list[dict[str, Any]] = []
    for family in sorted(per_family):
        total = per_family[family]["rows"]
        row: dict[str, Any] = {
            "family": family,
            "rows": total,
        }
        for field in FIELD_ALIASES:
            missing = missing_per_family[family][field]
            row[f"missing_{field}"] = missing
            row[f"missing_{field}_pct"] = round(missing / total, 4) if total else 0.0
        row["unknown_family_value"] = noisy_per_family[family]["unknown_family_value"]
        row["title_missing_but_short_title_present"] = noisy_per_family[family][
            "title_missing_but_short_title_present"
        ]
        row["mulga_true_active_end"] = noisy_per_family[family]["mulga_true_active_end"]
        row["mulga_false_inactive_end"] = noisy_per_family[family]["mulga_false_inactive_end"]
        row["missing_article_granularity"] = noisy_per_family[family]["missing_article_granularity"]
        rows.append(row)

    return {
        "collection": args.collection,
        "milvus_uri": args.milvus_uri,
        "collection_row_count": collection_row_count,
        "scanned_rows": scanned,
        "max_rows": args.max_rows,
        "metadata_keys": dict(metadata_keys.most_common()),
        "family_values": dict(family_values.most_common()),
        "rows": rows,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "family",
        "rows",
        "missing_family",
        "missing_family_pct",
        "missing_title",
        "missing_title_pct",
        "missing_short_title",
        "missing_short_title_pct",
        "missing_issuer",
        "missing_issuer_pct",
        "missing_identifier",
        "missing_identifier_pct",
        "missing_official_gazette_date",
        "missing_official_gazette_date_pct",
        "missing_official_gazette_number",
        "missing_official_gazette_number_pct",
        "missing_effective_start",
        "missing_effective_start_pct",
        "missing_effective_end",
        "missing_effective_end_pct",
        "missing_article",
        "missing_article_pct",
        "missing_section",
        "missing_section_pct",
        "unknown_family_value",
        "title_missing_but_short_title_present",
        "mulga_true_active_end",
        "mulga_false_inactive_end",
        "missing_article_granularity",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    rows = summary["rows"]
    total_scanned = summary["scanned_rows"]
    global_missing: Counter[str] = Counter()
    for row in rows:
        for field in FIELD_ALIASES:
            global_missing[field] += int(row[f"missing_{field}"])

    lines = [
        "# Phase 3 Index Metadata Audit",
        "",
        f"- milvus_uri: `{summary['milvus_uri']}`",
        f"- collection: `{summary['collection']}`",
        f"- collection_row_count: {summary['collection_row_count']}",
        f"- scanned_rows: {total_scanned}",
        f"- max_rows: {summary['max_rows']}",
        "",
        "## Global Missing Field Coverage",
    ]
    for field, missing in global_missing.most_common():
        pct = missing / total_scanned if total_scanned else 0.0
        lines.append(f"- {field}: missing {missing} ({pct:.1%})")

    lines.extend(["", "## Family Row Counts"])
    for family, count in summary["family_values"].items():
        lines.append(f"- {family}: {count}")

    lines.extend(["", "## Highest Risk Metadata Gaps"])
    high_risk = []
    for row in rows:
        if row["missing_title_pct"] >= 0.5:
            high_risk.append(f"{row['family']}: title missing {row['missing_title_pct']:.1%}")
        if row["missing_issuer_pct"] >= 0.5:
            high_risk.append(f"{row['family']}: issuer missing {row['missing_issuer_pct']:.1%}")
        if row["missing_official_gazette_date_pct"] >= 0.5:
            high_risk.append(
                f"{row['family']}: official_gazette_date missing {row['missing_official_gazette_date_pct']:.1%}"
            )
    for item in high_risk[:30]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Retrieval Hardening Implications",
            "- Family and identifier metadata are broadly usable for source-family routing and exact identifier boosts.",
            "- Missing full title/issuer fields limit issuer-aware tie-breakers for university/agency regulations until canonical enrichment is added.",
            "- Active/repealed control should use `mulga` plus `yururluk_bitis`; rows with conflicting state are listed in the CSV.",
            "",
            "## Metadata Keys Seen",
            "```json",
            json.dumps(summary["metadata_keys"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    summary = scan_index(args)
    write_csv(args.out_csv, summary["rows"])
    write_markdown(args.out_md, summary)
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
