#!/usr/bin/env python3
"""Export and audit the Phase 5 canonical source catalog.

The catalog is built from canonical article rows and is source-level rather
than chunk-level. It is intended to feed source identity selection before dense
semantic retrieval dominates the candidate pool.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
API_SRC = REPO_ROOT / "api-gateway/src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from rag.source_catalog import canonical_catalog_audit, load_canonical_source_catalog  # noqa: E402


DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_05_canonical_catalog_audit.md"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_05_canonical_catalog_audit.csv"
DEFAULT_OUT_CATALOG = REPO_ROOT / "reports/benchmark/phase_05_canonical_source_catalog.csv"


CATALOG_FIELDS = [
    "source_key",
    "source_family_canonical",
    "canonical_title",
    "canonical_title_normalized",
    "canonical_identifier",
    "canonical_identifier_display",
    "canonical_identifier_type",
    "issuer",
    "issuer_normalized",
    "official_gazette_no",
    "official_gazette_date",
    "effective_start",
    "effective_end",
    "effective_state",
    "year_signals",
    "alias_titles",
    "cross_refs",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-catalog", type=Path, default=DEFAULT_OUT_CATALOG)
    parser.add_argument("--catalog-limit", type=int, help="Optional export cap for smoke runs.")
    return parser.parse_args()


def _csv_value(value: Any) -> str:
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return "" if value is None else str(value)


def write_catalog_csv(path: Path, catalog: dict[str, dict[str, Any]], limit: int | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(catalog.values(), key=lambda row: (row.get("source_family_canonical") or "", row.get("source_key") or ""))
    if limit is not None:
        rows = rows[:limit]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CATALOG_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in CATALOG_FIELDS})


def write_audit_csv(path: Path, audit: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = audit["fields"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["field", "missing_count", "missing_pct"])
        writer.writeheader()
        total = int(audit["record_count"])
        for field in fields:
            missing = int(audit["missing"].get(field, 0))
            writer.writerow(
                {
                    "field": field,
                    "missing_count": missing,
                    "missing_pct": round(missing / total, 4) if total else 0.0,
                }
            )


def pct(value: int, total: int) -> str:
    return f"{value / total:.1%}" if total else "0.0%"


def write_markdown(path: Path, audit: dict[str, Any], catalog_path: Path) -> None:
    total = int(audit["record_count"])
    try:
        catalog_display = str(catalog_path.relative_to(REPO_ROOT))
    except ValueError:
        catalog_display = str(catalog_path)
    lines = [
        "# Phase 5 Canonical Source Catalog Audit",
        "",
        f"- source_records: {total}",
        f"- catalog_artifact: `{catalog_display}`",
        "",
        "## Field Completeness",
        "| field | missing |",
        "| --- | ---: |",
    ]
    for field in audit["fields"]:
        missing = int(audit["missing"].get(field, 0))
        lines.append(f"| {field} | {missing} ({pct(missing, total)}) |")

    lines.extend(["", "## Source Families"])
    for family, count in audit["family_counts"].items():
        lines.append(f"- {family}: {count}")

    lines.extend(["", "## Identifier Types"])
    for identifier_type, count in audit["identifier_type_counts"].items():
        lines.append(f"- {identifier_type}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- This is a source-level canonical catalog, not a chunk-level retrieval trace.",
            "- It supplies normalized title, identifier, issuer, temporal, alias, and cross-reference signals for metadata-first source identity selection.",
            "- Remaining missing values should be treated as metadata backfill or source acquisition backlog, not prompt tuning work.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    catalog = load_canonical_source_catalog()
    audit = canonical_catalog_audit(catalog)
    write_catalog_csv(args.out_catalog, catalog, args.catalog_limit)
    write_audit_csv(args.out_csv, audit)
    write_markdown(args.out_md, audit, args.out_catalog)
    print(f"Wrote {args.out_catalog}")
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
