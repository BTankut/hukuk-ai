#!/usr/bin/env python3
"""Build Phase 16A corpus materialization remediation artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260424T081121Z_phase15_full"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_16a_corpus_materialization_remediation.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_16a_corpus_materialization_remediation.md"
DEFAULT_CB_CSV = REPO_ROOT / "reports/benchmark/phase_16a_cb_genelge_body_audit.csv"
DEFAULT_CB_MD = REPO_ROOT / "reports/benchmark/phase_16a_cb_genelge_body_audit.md"


FIELDS = [
    "qid",
    "expected_family",
    "selected_family",
    "selected_identifier",
    "selected_title",
    "title_only_fallback_used",
    "body_text_available",
    "body_text_length",
    "source_key_collision_detected",
    "source_key_v2_collision_detected",
    "binding_source_key",
    "binding_source_key_version",
    "canonical_key_binding_applied",
    "binding_source_key_collision_detected",
    "corpus_materialization_required_reason",
    "official_source_available",
    "ingestion_required",
    "parser_required",
    "reindex_required",
    "owner",
    "status",
    "selected_document_id",
    "selected_article",
    "source_key_collision_pair",
    "score_0_10_proxy",
    "failure_classes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--cb-csv", type=Path, default=DEFAULT_CB_CSV)
    parser.add_argument("--cb-md", type=Path, default=DEFAULT_CB_MD)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def is_true(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "evet"}


def expected_family(row: dict[str, str]) -> str:
    return row.get("expected_source_family_canonical") or row.get("primary_type") or "UNKNOWN"


def classify_remediation(row: dict[str, str]) -> dict[str, str]:
    family = expected_family(row)
    reason = row.get("canonical_span_materialization_reason", "")
    body_available = is_true(row.get("body_text_available"))
    legacy_collision = is_true(row.get("source_key_collision_detected"))
    v2_collision = is_true(row.get("source_key_v2_collision_detected"))
    binding_collision = is_true(row.get("binding_source_key_collision_detected"))
    canonical_binding_applied = is_true(row.get("canonical_key_binding_applied"))
    collision = bool(
        legacy_collision
        and not (canonical_binding_applied and not v2_collision and not binding_collision)
    )

    if collision:
        return {
            "official_source_available": "yes_if_selected_title_is_official_catalog_row",
            "ingestion_required": "False",
            "parser_required": "True",
            "reindex_required": "True",
            "owner": "source_identity+canonical_parser",
            "status": "blocked_by_family_source_key_collision",
        }
    if reason == "title_only_or_unreadable_body":
        return {
            "official_source_available": "yes_catalog_row_present_but_body_unreadable",
            "ingestion_required": "True",
            "parser_required": "True",
            "reindex_required": "True",
            "owner": "corpus_ingestion",
            "status": "text_extraction_repair_required",
        }
    if body_available and reason == "body_span_available_but_title_or_article_zero":
        owner = "canonical_parser"
        if family == "CB_GENELGE":
            owner = "canonical_parser+cb_genelge_body_span"
        return {
            "official_source_available": "True",
            "ingestion_required": "False",
            "parser_required": "True",
            "reindex_required": "True",
            "owner": owner,
            "status": "body_exists_but_article_zero_materialization_required",
        }
    if family == "CB_GENELGE":
        return {
            "official_source_available": "unknown_until_official_text_fetch",
            "ingestion_required": "True",
            "parser_required": "True",
            "reindex_required": "True",
            "owner": "corpus_ingestion+canonical_parser",
            "status": "cb_genelge_official_body_acquisition_required",
        }
    return {
        "official_source_available": "unknown",
        "ingestion_required": "True",
        "parser_required": "True",
        "reindex_required": "True",
        "owner": "canonical_parser",
        "status": "canonical_body_span_materialization_required",
    }


def remediation_row(scored: dict[str, str], answer: dict[str, str]) -> dict[str, str]:
    merged = {**scored, **answer}
    classified = classify_remediation(merged)
    return {
        "qid": scored.get("qid", ""),
        "expected_family": expected_family(scored),
        "selected_family": answer.get("source_family_claimed", ""),
        "selected_identifier": answer.get("source_identifier_claimed", ""),
        "selected_title": answer.get("source_title_claimed", ""),
        "title_only_fallback_used": answer.get("title_only_fallback_used", ""),
        "body_text_available": answer.get("body_text_available", ""),
        "body_text_length": answer.get("body_text_length", ""),
        "source_key_collision_detected": answer.get("source_key_collision_detected", ""),
        "source_key_v2_collision_detected": answer.get("source_key_v2_collision_detected", ""),
        "binding_source_key": answer.get("binding_source_key", ""),
        "binding_source_key_version": answer.get("binding_source_key_version", ""),
        "canonical_key_binding_applied": answer.get("canonical_key_binding_applied", ""),
        "binding_source_key_collision_detected": answer.get("binding_source_key_collision_detected", ""),
        "corpus_materialization_required_reason": answer.get("canonical_span_materialization_reason", ""),
        "selected_document_id": answer.get("selected_document_id", ""),
        "selected_article": answer.get("selected_article", ""),
        "source_key_collision_pair": answer.get("source_key_collision_pair", ""),
        "score_0_10_proxy": scored.get("score_0_10_proxy", ""),
        "failure_classes": scored.get("failure_classes", ""),
        **classified,
    }


def cb_genelge_audit_row(row: dict[str, str]) -> dict[str, str]:
    reason = row["corpus_materialization_required_reason"]
    body_available = is_true(row["body_text_available"])
    legacy_collision = is_true(row["source_key_collision_detected"])
    v2_collision = is_true(row.get("source_key_v2_collision_detected"))
    binding_collision = is_true(row.get("binding_source_key_collision_detected"))
    canonical_binding_applied = is_true(row.get("canonical_key_binding_applied"))
    collision = bool(
        legacy_collision
        and not (canonical_binding_applied and not v2_collision and not binding_collision)
    )
    article_zero = (row.get("selected_article") or "").strip() in {"", "0"}
    if collision:
        root_cause = "family_qualified_source_key_collision"
    elif body_available and article_zero:
        root_cause = "body_text_exists_but_parser_materializes_only_m0_title_span"
    elif not body_available:
        root_cause = "body_text_absent_or_unreadable_for_selected_family"
    else:
        root_cause = "canonical_span_materialization_unresolved"
    return {
        "qid": row["qid"],
        "selected_identifier": row["selected_identifier"],
        "selected_title": row["selected_title"],
        "comes_as_m0_or_title_only": "True" if article_zero else "False",
        "body_text_available": row["body_text_available"],
        "body_text_length": row["body_text_length"],
        "parser_gap": "True" if body_available and article_zero else "False",
        "source_acquisition_required": "False" if body_available else "True",
        "source_key_collision_detected": row["source_key_collision_detected"],
        "source_key_v2_collision_detected": row.get("source_key_v2_collision_detected", ""),
        "binding_source_key_collision_detected": row.get("binding_source_key_collision_detected", ""),
        "root_cause": root_cause,
        "remediation_status": row["status"],
        "reason": reason,
    }


def main() -> int:
    args = parse_args()
    answers = {row["qid"]: row for row in read_csv(args.run_dir / "candidate_answers.csv")}
    scored_rows = read_csv(args.run_dir / "scored.csv")
    rows: list[dict[str, str]] = []
    for scored in scored_rows:
        answer = answers.get(scored.get("qid", ""), {})
        if is_true(answer.get("corpus_materialization_required")):
            rows.append(remediation_row(scored, answer))

    write_csv(args.out_csv, rows, FIELDS)

    cb_rows = [cb_genelge_audit_row(row) for row in rows if row["expected_family"] == "CB_GENELGE"]
    cb_fields = [
        "qid",
        "selected_identifier",
        "selected_title",
        "comes_as_m0_or_title_only",
        "body_text_available",
        "body_text_length",
        "parser_gap",
        "source_acquisition_required",
        "source_key_collision_detected",
        "source_key_v2_collision_detected",
        "binding_source_key_collision_detected",
        "root_cause",
        "remediation_status",
        "reason",
    ]
    write_csv(args.cb_csv, cb_rows, cb_fields)

    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_family[row["expected_family"]].append(row)
    status_counts = Counter(row["status"] for row in rows)
    owner_counts = Counter(row["owner"] for row in rows)
    reason_counts = Counter(row["corpus_materialization_required_reason"] or "unknown" for row in rows)
    body_exists = sum(1 for row in rows if is_true(row["body_text_available"]))
    collision_count = sum(1 for row in rows if is_true(row["source_key_collision_detected"]))
    binding_collision_count = sum(1 for row in rows if is_true(row.get("binding_source_key_collision_detected")))
    article_zero_count = sum(1 for row in rows if (row.get("selected_article") or "").strip() in {"", "0"})

    lines = [
        "# Phase 16A Corpus Materialization Remediation",
        "",
        f"- source_run_dir: `{args.run_dir}`",
        f"- corpus_materialization_required_rows: {len(rows)}",
        f"- body_text_available_rows: {body_exists}",
        f"- selected_article_zero_or_empty_rows: {article_zero_count}",
        f"- legacy_source_key_collision_rows: {collision_count}",
        f"- binding_source_key_collision_rows: {binding_collision_count}",
        "",
        "## By Family",
    ]
    for family in sorted(by_family):
        qids = ", ".join(row["qid"] for row in by_family[family])
        lines.append(f"- {family}: {len(by_family[family])} rows; qids={qids}")
    lines.extend(["", "## Reason Counts"])
    for reason, count in reason_counts.most_common():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Owner Counts"])
    for owner, count in owner_counts.most_common():
        lines.append(f"- {owner}: {count}")
    lines.extend(["", "## Status Counts"])
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Explicit Remediation Rows"])
    for row in rows:
        lines.append(
            "- "
            f"{row['qid']}: expected={row['expected_family']}, selected={row['selected_family']}, "
            f"reason={row['corpus_materialization_required_reason']}, "
            f"body={row['body_text_available']}:{row['body_text_length']}, "
            f"legacy_collision={row['source_key_collision_detected']}, "
            f"binding_collision={row.get('binding_source_key_collision_detected', '')}, "
            f"owner={row['owner']}, "
            f"status={row['status']}"
        )
    lines.extend(
        [
            "",
            "## Phase 16A Decision",
            "- Corpus-required rows are explicitly classified.",
            "- Legacy source-key collision is treated as a blocker only when canonical v2 binding is absent or binding collision remains true.",
            "- Rows with clean v2 binding but unreadable/title-only body remain corpus/parser backlog, not source-key blockers.",
        ]
    )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cb_root_counts = Counter(row["root_cause"] for row in cb_rows)
    cb_lines = [
        "# Phase 16A CB_GENELGE Body Audit",
        "",
        f"- source_run_dir: `{args.run_dir}`",
        f"- cb_genelge_rows: {len(cb_rows)}",
        f"- m0_or_title_only_rows: {sum(1 for row in cb_rows if is_true(row['comes_as_m0_or_title_only']))}",
        f"- body_text_available_rows: {sum(1 for row in cb_rows if is_true(row['body_text_available']))}",
        f"- parser_gap_rows: {sum(1 for row in cb_rows if is_true(row['parser_gap']))}",
        f"- legacy_source_key_collision_rows: {sum(1 for row in cb_rows if is_true(row['source_key_collision_detected']))}",
        f"- binding_source_key_collision_rows: {sum(1 for row in cb_rows if is_true(row.get('binding_source_key_collision_detected')))}",
        "",
        "## Root Cause Counts",
    ]
    for root_cause, count in cb_root_counts.most_common():
        cb_lines.append(f"- {root_cause}: {count}")
    cb_lines.extend(["", "## Rows"])
    for row in cb_rows:
        cb_lines.append(
            "- "
            f"{row['qid']}: identifier={row['selected_identifier']}, "
            f"body={row['body_text_available']}:{row['body_text_length']}, "
            f"parser_gap={row['parser_gap']}, legacy_collision={row['source_key_collision_detected']}, "
            f"binding_collision={row.get('binding_source_key_collision_detected', '')}, "
            f"root_cause={row['root_cause']}"
        )
    cb_lines.extend(
        [
            "",
            "## Conclusion",
            "- CB_GENELGE is not a user-query formatting problem.",
            "- Legacy numeric source-key collisions must be interpreted through binding-source-key status.",
            "- Clean v2 binding removes source-key collision as the blocker; remaining failures are corpus/body-span or answer-slot issues.",
        ]
    )
    args.cb_md.write_text("\n".join(cb_lines) + "\n", encoding="utf-8")

    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.cb_csv}")
    print(f"Wrote {args.cb_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
