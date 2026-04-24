#!/usr/bin/env python3
"""Build Phase 15C corpus materialization backlog artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_15c_corpus_materialization_backlog.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_15c_corpus_materialization_backlog.md"
DEFAULT_COLLISION_MD = REPO_ROOT / "reports/benchmark/phase_15c_source_key_collision_remediation_plan.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--collision-md", type=Path, default=DEFAULT_COLLISION_MD)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def is_true(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "evet"}


def expected_family(row: dict[str, str]) -> str:
    return row.get("expected_source_family_canonical") or row.get("primary_type") or "UNKNOWN"


def classify_fix(row: dict[str, str]) -> tuple[str, str, str]:
    family = expected_family(row)
    reason = row.get("canonical_span_materialization_reason", "")
    collision = is_true(row.get("source_key_collision_detected"))
    if collision:
        return (
            "family_aware_source_key_materialization",
            "source_identity+canonical_parser",
            "Create family-qualified source keys and rematerialize the selected document body under the family-specific key.",
        )
    if family == "CB_GENELGE":
        return (
            "official_genelge_body_acquisition",
            "corpus_ingestion",
            "Acquire full circular text from official source and parse body spans beyond title/m.0.",
        )
    if reason == "body_span_available_but_title_or_article_zero":
        return (
            "article_zero_reparse_or_body_span_link",
            "canonical_parser",
            "Body exists but selector landed on title/article-zero span; remap canonical body span and article metadata.",
        )
    if reason == "title_only_or_unreadable_body":
        return (
            "text_extraction_repair",
            "corpus_ingestion",
            "Re-extract readable article text from source PDF/HTML and reject unreadable control-character body spans.",
        )
    return (
        "canonical_body_span_materialization",
        "canonical_parser",
        "Materialize non-title body span and attach article/section metadata.",
    )


def ingestion_source_needed(row: dict[str, str]) -> str:
    family = expected_family(row)
    if family in {"CB_GENELGE", "CB_KARAR", "CB_KARARNAME"}:
        return "resmigazete_or_presidency_official_text"
    if family == "TEBLIGLER":
        return "resmigazete_teblig_full_text"
    if family == "TUZUK":
        return "mevzuat_tuzuk_full_text"
    return "canonical_mevzuat_full_text"


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    answers = {row["qid"]: row for row in read_csv(args.run_dir / "candidate_answers.csv")}
    scored = read_csv(args.run_dir / "scored.csv")
    rows: list[dict[str, str]] = []
    for scored_row in scored:
        answer = answers.get(scored_row["qid"], {})
        if not is_true(answer.get("corpus_materialization_required")):
            continue
        fix_type, owner, note = classify_fix({**scored_row, **answer})
        row = {
            "qid": scored_row.get("qid", ""),
            "expected_family": expected_family(scored_row),
            "selected_title": answer.get("source_title_claimed", ""),
            "selected_identifier": answer.get("source_identifier_claimed", ""),
            "selected_document_id": answer.get("selected_document_id", ""),
            "selected_article": answer.get("selected_article", ""),
            "title_only_fallback_reason": answer.get("canonical_span_materialization_reason", ""),
            "body_text_available": answer.get("body_text_available", ""),
            "body_text_length": answer.get("body_text_length", ""),
            "source_key_collision": answer.get("source_key_collision_detected", ""),
            "source_key_collision_pair": answer.get("source_key_collision_pair", ""),
            "ingestion_source_needed": ingestion_source_needed(scored_row),
            "owner": owner,
            "fix_type": fix_type,
            "fix_note": note,
            "score_0_10_proxy": scored_row.get("score_0_10_proxy", ""),
        }
        rows.append(row)

    fields = [
        "qid",
        "expected_family",
        "selected_title",
        "selected_identifier",
        "selected_document_id",
        "selected_article",
        "title_only_fallback_reason",
        "body_text_available",
        "body_text_length",
        "source_key_collision",
        "source_key_collision_pair",
        "ingestion_source_needed",
        "owner",
        "fix_type",
        "fix_note",
        "score_0_10_proxy",
    ]
    write_csv(args.out_csv, rows, fields)

    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_family[row["expected_family"]].append(row)
    reason_counts = Counter(row["title_only_fallback_reason"] or "unknown" for row in rows)
    fix_counts = Counter(row["fix_type"] for row in rows)
    owner_counts = Counter(row["owner"] for row in rows)

    lines = [
        "# Phase 15C Corpus Materialization Backlog",
        "",
        f"- source_run_dir: `{args.run_dir}`",
        f"- corpus_materialization_required_rows: {len(rows)}",
        f"- source_key_collision_rows: {sum(1 for row in rows if is_true(row['source_key_collision']))}",
        "",
        "## By Family",
    ]
    for family in sorted(by_family):
        qids = ", ".join(row["qid"] for row in by_family[family])
        lines.append(f"- {family}: {len(by_family[family])} rows; qids={qids}")
    lines.extend(["", "## Reason Counts"])
    for reason, count in reason_counts.most_common():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Fix Type Counts"])
    for fix_type, count in fix_counts.most_common():
        lines.append(f"- {fix_type}: {count}")
    lines.extend(["", "## Owner Counts"])
    for owner, count in owner_counts.most_common():
        lines.append(f"- {owner}: {count}")
    lines.extend(["", "## Rows"])
    for row in rows:
        lines.append(
            "- "
            f"{row['qid']}: family={row['expected_family']}, fix={row['fix_type']}, "
            f"owner={row['owner']}, reason={row['title_only_fallback_reason']}, "
            f"collision={row['source_key_collision_pair'] or 'none'}"
        )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    collision_rows = [row for row in rows if is_true(row["source_key_collision"])]
    collision_lines = [
        "# Phase 15C Source-Key Collision Remediation Plan",
        "",
        f"- collision_rows_in_corpus_backlog: {len(collision_rows)}",
        "- permanent_fix: replace numeric-only runtime source-key joins with family-qualified canonical source keys.",
        "- required_key_shape: `{source_family}:{canonical_identifier}:{canonical_title_hash_or_doc_uuid}` plus article/span ids.",
        "- migration_rule: keep numeric `belge_no` as alias only; never use it alone for cross-family body materialization.",
        "- validation_rule: fail corpus materialization when one numeric key resolves to multiple source families and the selected family has no non-title body span.",
        "",
        "## Collision Rows",
    ]
    if not collision_rows:
        collision_lines.append("- none")
    for row in collision_rows:
        collision_lines.append(
            "- "
            f"{row['qid']}: family={row['expected_family']}, pair={row['source_key_collision_pair']}, "
            f"fix={row['fix_type']}"
        )
    args.collision_md.write_text("\n".join(collision_lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.collision_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
