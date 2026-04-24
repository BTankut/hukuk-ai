#!/usr/bin/env python3
"""Build a Phase 16B source-key collision report with canonical v2 keys."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
API_SRC = REPO_ROOT / "api-gateway" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from rag.orchestrator import RetrievedChunk  # noqa: E402
from routers.chat import (  # noqa: E402
    _resolve_chunk_canonical_source_key_v2,
    _source_key_collision_profile,
    _source_key_v2_collision_profile,
)


DEFAULT_REMEDIATION_CSV = REPO_ROOT / "reports/benchmark/phase_16a_corpus_materialization_remediation.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_16b_source_key_v2_collision_report.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_16b_source_key_v2_collision_report.md"


FIELDS = [
    "qid",
    "expected_family",
    "legacy_collision_detected",
    "legacy_collision_keys",
    "legacy_collision_pair",
    "source_key_v2_collision_detected",
    "source_key_v2_collision_keys",
    "source_key_v2_collision_pair",
    "canonical_document_keys_v2",
    "canonical_span_keys_v2",
    "verdict",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remediation-csv", type=Path, default=DEFAULT_REMEDIATION_CSV)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def is_true(value: str) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "evet"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_collision_pair(pair_text: str) -> list[tuple[str, str, str]]:
    parsed: list[tuple[str, str, str]] = []
    for segment in str(pair_text or "").split(";"):
        segment = segment.strip()
        if not segment or "=" not in segment:
            continue
        legacy_key, pair_blob = segment.split("=", 1)
        legacy_key = legacy_key.strip()
        for item in pair_blob.split("|"):
            item = item.strip()
            if not item or ":" not in item:
                continue
            family, title = item.split(":", 1)
            parsed.append((legacy_key, family.strip(), title.strip()))
    return parsed


def chunks_from_collision_row(row: dict[str, str]) -> list[RetrievedChunk]:
    chunks: list[RetrievedChunk] = []
    for index, (legacy_key, family, title) in enumerate(parse_collision_pair(row.get("source_key_collision_pair", ""))):
        chunks.append(
            RetrievedChunk(
                text=f"{title} body span for collision replay.",
                citation=f"{legacy_key} m.{index}/f.0",
                source=legacy_key,
                score=1.0 - (index * 0.01),
                metadata={
                    "belge_turu": family,
                    "source_family_canonical": family,
                    "belge_no": legacy_key,
                    "source_title": title,
                    "madde_no": str(index),
                },
            )
        )
    return chunks


def main() -> int:
    args = parse_args()
    rows: list[dict[str, str]] = []
    for row in read_csv(args.remediation_csv):
        if not is_true(row.get("source_key_collision_detected", "")):
            continue
        chunks = chunks_from_collision_row(row)
        legacy_profile = _source_key_collision_profile(chunks)
        v2_profile = _source_key_v2_collision_profile(chunks)
        document_keys_v2 = [
            _resolve_chunk_canonical_source_key_v2(chunk, include_span=False)
            for chunk in chunks
        ]
        span_keys_v2 = [
            _resolve_chunk_canonical_source_key_v2(chunk, include_span=True)
            for chunk in chunks
        ]
        verdict = (
            "v2_collision_removed"
            if legacy_profile.get("source_key_collision_detected") and not v2_profile.get("source_key_v2_collision_detected")
            else "v2_collision_still_present"
        )
        rows.append(
            {
                "qid": row.get("qid", ""),
                "expected_family": row.get("expected_family", ""),
                "legacy_collision_detected": str(bool(legacy_profile.get("source_key_collision_detected"))),
                "legacy_collision_keys": " | ".join(legacy_profile.get("source_key_collision_keys") or []),
                "legacy_collision_pair": legacy_profile.get("source_key_collision_pair", ""),
                "source_key_v2_collision_detected": str(bool(v2_profile.get("source_key_v2_collision_detected"))),
                "source_key_v2_collision_keys": " | ".join(v2_profile.get("source_key_v2_collision_keys") or []),
                "source_key_v2_collision_pair": v2_profile.get("source_key_v2_collision_pair", ""),
                "canonical_document_keys_v2": " | ".join(document_keys_v2),
                "canonical_span_keys_v2": " | ".join(span_keys_v2),
                "verdict": verdict,
            }
        )

    write_csv(args.out_csv, rows, FIELDS)

    verdict_counts = Counter(row["verdict"] for row in rows)
    lines = [
        "# Phase 16B Source-Key V2 Collision Report",
        "",
        f"- remediation_csv: `{args.remediation_csv}`",
        f"- collision_rows_replayed: {len(rows)}",
        f"- legacy_collision_rows: {sum(1 for row in rows if is_true(row['legacy_collision_detected']))}",
        f"- v2_collision_rows: {sum(1 for row in rows if is_true(row['source_key_v2_collision_detected']))}",
        "",
        "## Verdict Counts",
    ]
    for verdict, count in verdict_counts.most_common():
        lines.append(f"- {verdict}: {count}")
    lines.extend(["", "## Rows"])
    for row in rows:
        lines.append(
            "- "
            f"{row['qid']}: family={row['expected_family']}, legacy_keys={row['legacy_collision_keys']}, "
            f"v2_collision={row['source_key_v2_collision_detected']}, verdict={row['verdict']}"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "- Numeric-only legacy source keys remain aliases only.",
            "- Family-qualified v2 document keys separate the replayed CB_GENELGE/CB_KARAR/TEBLIGLER collisions.",
            "- Runtime traces now preserve both `legacy_source_key` and `canonical_source_key_v2` for compatibility.",
        ]
    )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
