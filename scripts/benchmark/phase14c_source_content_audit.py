#!/usr/bin/env python3
"""Audit canonical source/span materialization for a single mevzuat identifier.

The audit is intentionally data-driven: it reads the article rows corpus and
optionally confirms the same rows in Milvus. It does not special-case benchmark
questions; the identifier is a parameter.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import string
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTICLE_ROWS_CANDIDATES = (
    Path(os.getenv("MEVZUAT_ARTICLE_ROWS_PATH", "")).expanduser()
    if os.getenv("MEVZUAT_ARTICLE_ROWS_PATH", "").strip()
    else None,
    Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl"),
    REPO_ROOT / "data" / "mevzuat_db" / "article_rows.jsonl",
)
DEFAULT_OUT_DIR = REPO_ROOT / "reports" / "benchmark"


TR_ASCII = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)
ACTIVE_END_SENTINELS = {"", "9999-12-31", "9999-12-31T00:00:00", "9999-12-31 00:00:00"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifier", default="9903")
    parser.add_argument("--article-rows", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", "http://localhost:19530"))
    parser.add_argument(
        "--milvus-collection",
        default=os.getenv("MILVUS_COLLECTION", "mevzuat_faz1_shadow_20260418_compat1024"),
    )
    parser.add_argument("--skip-milvus", action="store_true")
    return parser.parse_args()


def resolve_article_rows(path: Path | None) -> Path:
    candidates = (path,) if path else DEFAULT_ARTICLE_ROWS_CANDIDATES
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    raise FileNotFoundError("article_rows.jsonl not found")


def normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower().translate(TR_ASCII)
    text = re.sub(r"\s+", " ", text)
    return text


def effective_state(row: dict[str, Any]) -> str:
    if row.get("mulga") is True or normalize_text(row.get("mulga")) in {"true", "1", "evet"}:
        return "repealed"
    end = str(row.get("yururluk_bitis") or row.get("effective_end") or "").strip()
    if end not in ACTIVE_END_SENTINELS:
        return "repealed"
    if row.get("yururluk_baslangic") or row.get("effective_start"):
        return "active"
    return "unknown"


def is_matching_row(row: dict[str, Any], identifier: str) -> bool:
    source_id = str(row.get("source_id") or "")
    values = {
        str(row.get("belge_no") or "").strip(),
        str(row.get("kanun_no") or "").strip(),
        str(row.get("law_no") or "").strip(),
        str(row.get("belge_kisa_adi") or "").strip(),
        str(row.get("kanun_kisa_adi") or "").strip(),
        str(row.get("canonical_identifier") or "").strip(),
    }
    return identifier in values or source_id.startswith(f"{identifier}:") or source_id.startswith(identifier)


def body_quality(body: str) -> dict[str, Any]:
    body = body or ""
    stripped = body.strip()
    if not stripped:
        return {
            "body_text_length": 0,
            "body_printable_ratio": 0.0,
            "body_alpha_count": 0,
            "body_control_count": 0,
            "body_text_available": False,
        }
    printable = set(string.printable)
    printable_or_tr = sum(1 for char in stripped if char in printable or char.isprintable())
    control_count = sum(1 for char in stripped if not char.isprintable() and char not in "\n\r\t")
    alpha_count = sum(1 for char in stripped if char.isalpha())
    ratio = printable_or_tr / len(stripped)
    available = bool(len(stripped) >= 40 and ratio >= 0.85 and alpha_count >= 20 and control_count <= 3)
    return {
        "body_text_length": len(stripped),
        "body_printable_ratio": round(ratio, 4),
        "body_alpha_count": alpha_count,
        "body_control_count": control_count,
        "body_text_available": available,
    }


def safe_preview(value: str, *, limit: int = 240) -> str:
    chars: list[str] = []
    for char in (value or "")[:limit]:
        if char in "\n\r\t":
            chars.append(" ")
        elif not char.isprintable():
            chars.append(f"\\x{ord(char):02x}")
        else:
            chars.append(char)
    return re.sub(r"\s+", " ", "".join(chars)).strip()


def markdown_cell(value: Any, *, limit: int = 90) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text.replace("|", "\\|")[:limit]


def row_record(row: dict[str, Any], *, source: str) -> dict[str, Any]:
    body = str(row.get("body") if row.get("body") is not None else row.get("text") or "")
    quality = body_quality(body)
    article = str(row.get("madde_no") or row.get("article_no") or "")
    title = str(row.get("belge_adi") or row.get("kanun_adi") or row.get("source_title") or "")
    family = str(row.get("belge_turu") or row.get("source_type") or row.get("source_family_canonical") or "")
    is_title_only = article in {"", "0"} or not quality["body_text_available"]
    return {
        "audit_source": source,
        "raw_source_key": row.get("source_id") or "",
        "canonical_identifier": row.get("canonical_identifier")
        or row.get("belge_no")
        or row.get("kanun_no")
        or row.get("law_no")
        or "",
        "raw_family": family,
        "canonical_family": normalize_text(family),
        "article_number": article,
        "paragraph_or_fikra": row.get("fikra_no") or row.get("paragraph_no") or "",
        "title_text": title,
        "heading": row.get("heading") or row.get("article_heading") or "",
        "body_text_length": quality["body_text_length"],
        "body_printable_ratio": quality["body_printable_ratio"],
        "body_alpha_count": quality["body_alpha_count"],
        "body_control_count": quality["body_control_count"],
        "body_text_available": quality["body_text_available"],
        "title_only": is_title_only,
        "effective_state": effective_state(row),
        "effective_start": row.get("yururluk_baslangic") or row.get("effective_start") or "",
        "effective_end": row.get("yururluk_bitis") or row.get("effective_end") or "",
        "source_url": row.get("kaynak_url") or row.get("source_url") or "",
        "official_gazette_date": row.get("resmi_gazete_tarih") or row.get("official_gazette_date") or "",
        "official_gazette_no": row.get("resmi_gazete_sayi") or row.get("official_gazette_no") or "",
        "body_preview": safe_preview(body),
    }


def read_article_rows(path: Path, identifier: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if identifier not in line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if is_matching_row(row, identifier):
                rows.append(row_record(row, source="article_rows"))
    return rows


def read_milvus_rows(uri: str, collection: str, identifier: str) -> tuple[list[dict[str, Any]], str]:
    try:
        from pymilvus import MilvusClient
    except ImportError:
        return [], "pymilvus_not_installed"

    try:
        client = MilvusClient(uri=uri)
        if not client.has_collection(collection):
            return [], "collection_not_found"
        expr = (
            f'metadata["belge_no"] == "{identifier}" || '
            f'metadata["kanun_no"] == "{identifier}" || '
            f'metadata["law_no"] == "{identifier}" || '
            f'metadata["source_id"] like "{identifier}%"'
        )
        hits = client.query(
            collection_name=collection,
            filter=expr,
            output_fields=["id", "text", "metadata"],
            limit=200,
        )
    except Exception as exc:
        return [], f"milvus_error:{type(exc).__name__}:{exc}"

    records: list[dict[str, Any]] = []
    for hit in hits:
        metadata = hit.get("metadata") if isinstance(hit, dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}
        row = dict(metadata)
        text = str(hit.get("text") or "") if isinstance(hit, dict) else ""
        if text:
            row.setdefault("body", text.split("\n", 1)[1] if "\n" in text else text)
        records.append(row_record(row, source="milvus"))
    return records, "ok"


def collision_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["audit_source"] != "article_rows":
            continue
        grouped[str(record["canonical_identifier"])].append(record)

    collisions: list[dict[str, Any]] = []
    for source_key, rows in grouped.items():
        family_title_pairs = {
            (str(row["canonical_family"]), normalize_text(row["title_text"]))
            for row in rows
        }
        collision = len(family_title_pairs) > 1
        for row in rows:
            collisions.append(
                {
                    "source_key": source_key,
                    "source_key_collision_detected": collision,
                    "raw_source_key": row["raw_source_key"],
                    "canonical_family": row["canonical_family"],
                    "article_number": row["article_number"],
                    "title_text": row["title_text"],
                    "body_text_available": row["body_text_available"],
                    "title_only": row["title_only"],
                    "effective_start": row["effective_start"],
                    "effective_end": row["effective_end"],
                    "source_url": row["source_url"],
                }
            )
    return collisions


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summary: dict[str, Any], records: list[dict[str, Any]], collisions: list[dict[str, Any]]) -> None:
    article_rows = [row for row in records if row["audit_source"] == "article_rows"]
    cb_rows = [row for row in article_rows if row["canonical_family"] == "cb_karar"]
    selectable_cb_rows = [
        row for row in cb_rows
        if row["article_number"] not in {"", "0"} and bool(row["body_text_available"])
    ]
    lines = [
        "# Phase 14C-A Source Content Audit: 9903",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- identifier: `{summary['identifier']}`",
        f"- article_rows_path: `{summary['article_rows_path']}`",
        f"- article_rows_hit_count: `{summary['article_rows_hit_count']}`",
        f"- milvus_status: `{summary['milvus_status']}`",
        f"- milvus_hit_count: `{summary['milvus_hit_count']}`",
        f"- source_key_collision_detected: `{summary['source_key_collision_detected']}`",
        f"- cb_karar_real_body_span_count: `{len(selectable_cb_rows)}`",
        f"- corpus_materialization_required: `{summary['corpus_materialization_required']}`",
        "",
        "## Corpus Truth Table",
        "",
        "| source | family | article | title_only | body_available | body_len | control_count | effective | title |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in article_rows:
        title = markdown_cell(row["title_text"])
        lines.append(
            "| {source} | {family} | {article} | {title_only} | {body} | {body_len} | {ctrl} | {state} | {title} |".format(
                source=row["raw_source_key"],
                family=row["canonical_family"],
                article=row["article_number"],
                title_only=row["title_only"],
                body=row["body_text_available"],
                body_len=row["body_text_length"],
                ctrl=row["body_control_count"],
                state=row["effective_state"],
                title=title,
            )
        )
    lines.extend(
        [
            "",
            "## Source-Key Collision",
            "",
            "| source_key | collision | family | article | body_available | title |",
            "|---|---:|---|---:|---:|---|",
        ]
    )
    for row in collisions:
        title = markdown_cell(row["title_text"])
        lines.append(
            f"| {row['source_key']} | {row['source_key_collision_detected']} | "
            f"{row['canonical_family']} | {row['article_number']} | {row['body_text_available']} | {title} |"
        )
    lines.extend(
        [
            "",
            "## Finding",
            "",
            "The selected source identity is present, but the canonical `cb_karar` source has no selectable non-title body span in the current corpus/index. "
            "The only `cb_karar` row for `9903` is `m.0`; its body is non-text/control-character content from the PDF extraction path. "
            "Rows `m.1`-`m.3` under the same numeric key are a different `teblig`, so they must not be materialized as `CB_KARAR 9903` support.",
            "",
            "Runtime implication: Phase 14C-B/C should expose this as `corpus_materialization_required` and degrade title-only answers instead of treating `m.0` as sufficient legal support.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    article_rows_path = resolve_article_rows(args.article_rows)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    article_records = read_article_rows(article_rows_path, args.identifier)
    milvus_records: list[dict[str, Any]] = []
    milvus_status = "skipped"
    if not args.skip_milvus:
        milvus_records, milvus_status = read_milvus_rows(args.milvus_uri, args.milvus_collection, args.identifier)

    records = [*article_records, *milvus_records]
    collisions = collision_records(records)
    article_families = Counter(row["canonical_family"] for row in article_records)
    source_key_collision_detected = any(bool(row["source_key_collision_detected"]) for row in collisions)
    cb_real_body_spans = [
        row
        for row in article_records
        if row["canonical_family"] == "cb_karar"
        and row["article_number"] not in {"", "0"}
        and bool(row["body_text_available"])
    ]
    cb_title_only_rows = [
        row for row in article_records
        if row["canonical_family"] == "cb_karar" and bool(row["title_only"])
    ]
    corpus_materialization_required = bool(not cb_real_body_spans and cb_title_only_rows)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "identifier": args.identifier,
        "article_rows_path": str(article_rows_path),
        "article_rows_hit_count": len(article_records),
        "milvus_uri": args.milvus_uri,
        "milvus_collection": args.milvus_collection,
        "milvus_status": milvus_status,
        "milvus_hit_count": len(milvus_records),
        "article_family_counts": dict(sorted(article_families.items())),
        "source_key_collision_detected": source_key_collision_detected,
        "cb_karar_real_body_span_count": len(cb_real_body_spans),
        "cb_karar_title_only_count": len(cb_title_only_rows),
        "corpus_materialization_required": corpus_materialization_required,
    }

    truth_path = out_dir / f"phase_14c_{args.identifier}_corpus_truth_table.csv"
    collision_path = out_dir / f"phase_14c_{args.identifier}_source_key_collision_report.csv"
    json_path = out_dir / f"phase_14c_{args.identifier}_source_content_audit.json"
    md_path = out_dir / f"phase_14c_{args.identifier}_source_content_audit.md"
    write_csv(truth_path, records)
    write_csv(collision_path, collisions)
    json_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "records": records,
                "source_key_collisions": collisions,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_markdown(md_path, summary, records, collisions)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"truth_table={truth_path}")
    print(f"collision_report={collision_path}")
    print(f"audit_json={json_path}")
    print(f"audit_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
