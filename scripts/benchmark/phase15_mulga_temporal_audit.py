#!/usr/bin/env python3
"""Build Phase 15D MULGA temporal/rubric audit artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_15d_mulga_temporal_rubric_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_15d_mulga_temporal_rubric_audit.md"
DEFAULT_TEMPLATE_MD = REPO_ROOT / "reports/benchmark/phase_15d_mulga_answer_template.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--template-md", type=Path, default=DEFAULT_TEMPLATE_MD)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def bool_text(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "evet", "pass"}


def expected_family(row: dict[str, str]) -> str:
    return row.get("expected_source_family_canonical") or row.get("primary_type") or "UNKNOWN"


def split_classes(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def classify_mulga_row(row: dict[str, str]) -> tuple[str, str]:
    if bool_text(row.get("pass_fail_proxy")):
        return "candidate_passable", "No targeted MULGA remediation needed beyond full rerun validation."
    failures = set(split_classes(row.get("failure_classes", "")))
    source_family = (row.get("source_family_claimed") or "").strip().upper()
    effective_state = (row.get("effective_state_claimed") or "").strip().lower()
    if "wrong_family" in failures or source_family not in {"MULGA", "MULGA_KANUN"}:
        return "wrong_family_or_active_family_selection", "Route historical/repealed-risk questions to MULGA family before active family fallback."
    if "repealed_source_used_as_active" in failures or effective_state == "active":
        return "temporal_state_answered_as_active", "Force answer synthesis to state repealed/historical status before any current-law conclusion."
    if "missing_temporal_qualification" in failures or row.get("temporal_validity_score") == "0.00":
        return "missing_temporal_qualification", "Require period/date, transition effect, and current applicability qualification."
    if "missing_required_content_signal" in failures or row.get("required_fact_coverage_score") not in {"1.00", "1.0"}:
        return "rubric_slot_gap", "Bind answer to temporal_validity, governing_source, result, and article/span slots."
    return "candidate_passable", "No targeted MULGA remediation needed beyond full rerun validation."


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    answers = {row["qid"]: row for row in read_csv(args.run_dir / "candidate_answers.csv")}
    scored_rows = read_csv(args.run_dir / "scored.csv")
    rows: list[dict[str, str]] = []
    for scored in scored_rows:
        if expected_family(scored) != "MULGA":
            continue
        answer = answers.get(scored["qid"], {})
        merged = {**scored, **answer}
        issue_type, recommended_fix = classify_mulga_row(merged)
        rows.append(
            {
                "qid": scored.get("qid", ""),
                "question": answer.get("question", ""),
                "score_0_10_proxy": scored.get("score_0_10_proxy", ""),
                "pass_fail_proxy": scored.get("pass_fail_proxy", ""),
                "expected_family": expected_family(scored),
                "claimed_family": answer.get("source_family_claimed", ""),
                "expected_effective_state": scored.get("effective_state_canonical", ""),
                "claimed_effective_state": answer.get("effective_state_claimed", ""),
                "temporal_qualification": answer.get("temporal_qualification", ""),
                "answer_mode": answer.get("answer_mode", ""),
                "grounding_status": answer.get("grounding_status", ""),
                "confidence_0_100": answer.get("confidence_0_100", ""),
                "temporal_validity_score": scored.get("temporal_validity_score", ""),
                "required_fact_coverage_score": answer.get("required_fact_coverage_score", ""),
                "missing_fact_slots": answer.get("missing_fact_slots", ""),
                "historical_or_repealed_question": answer.get("historical_or_repealed_question", ""),
                "repealed_scope_detected": answer.get("repealed_scope_detected", ""),
                "scenario_current_law_question": answer.get("scenario_current_law_question", ""),
                "support_contains_temporal_clause": answer.get("support_contains_temporal_clause", ""),
                "temporal_state_resolved": answer.get("temporal_state_resolved", ""),
                "temporal_clause_missing": answer.get("temporal_clause_missing", ""),
                "failure_classes": scored.get("failure_classes", ""),
                "issue_type": issue_type,
                "recommended_fix": recommended_fix,
            }
        )

    fields = [
        "qid",
        "question",
        "score_0_10_proxy",
        "pass_fail_proxy",
        "expected_family",
        "claimed_family",
        "expected_effective_state",
        "claimed_effective_state",
        "temporal_qualification",
        "answer_mode",
        "grounding_status",
        "confidence_0_100",
        "temporal_validity_score",
        "required_fact_coverage_score",
        "missing_fact_slots",
        "historical_or_repealed_question",
        "repealed_scope_detected",
        "scenario_current_law_question",
        "support_contains_temporal_clause",
        "temporal_state_resolved",
        "temporal_clause_missing",
        "failure_classes",
        "issue_type",
        "recommended_fix",
    ]
    write_csv(args.out_csv, rows, fields)

    issue_counts = Counter(row["issue_type"] for row in rows)
    pass_count = sum(1 for row in rows if bool_text(row["pass_fail_proxy"]))
    temporal_score_zero = sum(1 for row in rows if row["temporal_validity_score"] == "0.00")
    active_claims = sum(1 for row in rows if row["claimed_effective_state"].lower() == "active")
    wrong_family = sum(1 for row in rows if row["claimed_family"].upper() not in {"MULGA", "MULGA_KANUN"})

    lines = [
        "# Phase 15D MULGA Temporal/Rubric Audit",
        "",
        f"- source_run_dir: `{args.run_dir}`",
        f"- mulga_rows: {len(rows)}",
        f"- pass_count: {pass_count}/{len(rows)}",
        f"- wrong_family_claims: {wrong_family}",
        f"- active_state_claims: {active_claims}",
        f"- temporal_validity_zero_rows: {temporal_score_zero}",
        "",
        "## Issue Counts",
    ]
    for issue, count in issue_counts.most_common():
        lines.append(f"- {issue}: {count}")
    lines.extend(["", "## Rows"])
    for row in rows:
        lines.append(
            "- "
            f"{row['qid']}: score={row['score_0_10_proxy']}, claimed_family={row['claimed_family']}, "
            f"claimed_state={row['claimed_effective_state']}, issue={row['issue_type']}"
        )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    template_lines = [
        "# Phase 15D MULGA Answer Template",
        "",
        "This template is systemic and applies to repealed, historical, old-text, or current-applicability risk questions.",
        "",
        "1. Identify the selected source and whether it is active, repealed/mulga, or unresolved from evidence.",
        "2. State the historical period/date or transition effect only if it appears in selected evidence.",
        "3. State whether the source can be applied today directly; if not supported, qualify the answer instead of inferring.",
        "4. Keep current-law replacement sources separate from the repealed source; do not present an active replacement as the asked historical source.",
        "5. If temporal evidence is absent, return a qualified answer with lower confidence and manual-review reason.",
    ]
    args.template_md.write_text("\n".join(template_lines) + "\n", encoding="utf-8")

    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.template_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
