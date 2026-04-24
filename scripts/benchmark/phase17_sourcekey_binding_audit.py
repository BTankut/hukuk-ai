#!/usr/bin/env python3
"""Build Phase 17A source-key v2 binding audit artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260424T121906Z_phase16_full"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_17a_sourcekey_binding_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_17a_sourcekey_binding_audit.md"
DEFAULT_QIDS = ["CBG-04", "CBKAR-08"]


FIELDS = [
    "qid",
    "expected_family",
    "selected_family",
    "legacy_source_key",
    "selected_canonical_document_key_v2",
    "binding_source_key",
    "binding_source_key_version",
    "legacy_source_key_used_as_alias",
    "canonical_key_binding_applied",
    "canonical_key_binding_reason",
    "source_key_collision_detected",
    "source_key_v2_collision_detected",
    "binding_source_key_collision_detected",
    "canonical_span_materialized",
    "corpus_materialization_required",
    "canonical_span_materialization_reason",
    "score_0_10_proxy",
    "pass_fail_proxy",
    "failure_classes",
    "binding_verdict",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--qids", nargs="*", default=DEFAULT_QIDS)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def is_true(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "evet"}


def expected_family(row: dict[str, str]) -> str:
    return row.get("expected_source_family_canonical") or row.get("primary_type") or "UNKNOWN"


def binding_verdict(row: dict[str, str]) -> str:
    canonical_applied = is_true(row.get("canonical_key_binding_applied"))
    legacy_collision = is_true(row.get("source_key_collision_detected"))
    v2_collision = is_true(row.get("source_key_v2_collision_detected"))
    binding_collision = is_true(row.get("binding_source_key_collision_detected"))
    reason = row.get("canonical_span_materialization_reason") or ""
    if canonical_applied and legacy_collision and not v2_collision and not binding_collision:
        if reason == "source_key_collision_without_family_body_span":
            return "v2_bound_but_materialization_still_legacy_collision_blocked"
        return "v2_binding_removed_legacy_collision_blocker"
    if canonical_applied and not binding_collision:
        return "v2_binding_clean"
    if binding_collision:
        return "binding_collision_open"
    return "binding_not_applied"


def main() -> int:
    args = parse_args()
    answers = {row["qid"]: row for row in read_csv(args.run_dir / "candidate_answers.csv")}
    scored = {row["qid"]: row for row in read_csv(args.run_dir / "scored.csv")}
    qids = [qid for raw in args.qids for qid in str(raw).replace(",", " ").split() if qid]
    rows: list[dict[str, str]] = []
    for qid in qids:
        answer = answers.get(qid, {})
        score = scored.get(qid, {})
        merged = {**answer, **score}
        row = {
            "qid": qid,
            "expected_family": expected_family(score),
            "selected_family": answer.get("source_family_claimed", ""),
            "legacy_source_key": answer.get("legacy_source_key", ""),
            "selected_canonical_document_key_v2": answer.get("selected_canonical_document_key_v2", ""),
            "binding_source_key": answer.get("binding_source_key", ""),
            "binding_source_key_version": answer.get("binding_source_key_version", ""),
            "legacy_source_key_used_as_alias": answer.get("legacy_source_key_used_as_alias", ""),
            "canonical_key_binding_applied": answer.get("canonical_key_binding_applied", ""),
            "canonical_key_binding_reason": answer.get("canonical_key_binding_reason", ""),
            "source_key_collision_detected": answer.get("source_key_collision_detected", ""),
            "source_key_v2_collision_detected": answer.get("source_key_v2_collision_detected", ""),
            "binding_source_key_collision_detected": answer.get("binding_source_key_collision_detected", ""),
            "canonical_span_materialized": answer.get("canonical_span_materialized", ""),
            "corpus_materialization_required": answer.get("corpus_materialization_required", ""),
            "canonical_span_materialization_reason": answer.get("canonical_span_materialization_reason", ""),
            "score_0_10_proxy": score.get("score_0_10_proxy", ""),
            "pass_fail_proxy": score.get("pass_fail_proxy", ""),
            "failure_classes": score.get("failure_classes", ""),
        }
        row["binding_verdict"] = binding_verdict(merged)
        rows.append(row)

    write_csv(args.out_csv, rows)
    verdict_counts = Counter(row["binding_verdict"] for row in rows)
    canonical_applied_count = sum(1 for row in rows if is_true(row["canonical_key_binding_applied"]))
    legacy_collision_count = sum(1 for row in rows if is_true(row["source_key_collision_detected"]))
    v2_collision_count = sum(1 for row in rows if is_true(row["source_key_v2_collision_detected"]))
    binding_collision_count = sum(1 for row in rows if is_true(row["binding_source_key_collision_detected"]))
    legacy_blocker_count = sum(
        1
        for row in rows
        if row["canonical_span_materialization_reason"] == "source_key_collision_without_family_body_span"
    )
    corpus_required_count = sum(1 for row in rows if is_true(row["corpus_materialization_required"]))

    lines = [
        "# Phase 17A Source-Key V2 Binding Audit",
        "",
        f"- source_run_dir: `{args.run_dir}`",
        f"- audited_rows: {len(rows)}",
        f"- canonical_key_binding_applied_rows: {canonical_applied_count}",
        f"- legacy_source_key_collision_rows: {legacy_collision_count}",
        f"- source_key_v2_collision_rows: {v2_collision_count}",
        f"- binding_source_key_collision_rows: {binding_collision_count}",
        f"- legacy_collision_materialization_blocker_rows: {legacy_blocker_count}",
        f"- corpus_materialization_required_rows: {corpus_required_count}",
        "",
        "## Verdict Counts",
    ]
    for verdict, count in verdict_counts.most_common():
        lines.append(f"- {verdict}: {count}")
    lines.extend(["", "## Rows"])
    for row in rows:
        lines.append(
            "- "
            f"{row['qid']}: binding={row['binding_source_key'] or 'missing'}, "
            f"legacy_collision={row['source_key_collision_detected']}, "
            f"v2_collision={row['source_key_v2_collision_detected']}, "
            f"binding_collision={row['binding_source_key_collision_detected']}, "
            f"reason={row['canonical_span_materialization_reason']}, "
            f"verdict={row['binding_verdict']}"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "- Legacy numeric source keys remain observable as aliases.",
            "- Runtime binding must be evaluated with `binding_source_key` and `binding_source_key_collision_detected`.",
            "- A row is no longer considered source-key blocked when canonical v2 binding is applied and binding collision is false.",
        ]
    )
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
