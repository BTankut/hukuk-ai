#!/usr/bin/env python3
"""Reconcile two lawyer-reviewed CSV files into final training candidates.

Policy (default):
- APPROVE + APPROVE => approved
- any REJECT => manual_escalation
- APPROVE + REVISE or REVISE + REVISE => revised_needed

Provenance is preserved by carrying both lawyers' decisions/comments/corrections
into the reconciled master outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

VALID_DECISIONS = {"APPROVE", "REVISE", "REJECT"}
BASE_FIELDS = [
    "batch_item_no",
    "candidate_id",
    "question_id",
    "difficulty",
    "category",
    "source_file",
    "source_record_id",
    "split",
    "refusal_expected",
    "is_hallucination",
    "has_citation",
    "response_time_ms",
    "question",
    "context",
    "generated_answer",
]


def _read_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def _norm_decision(value: str) -> str:
    return (value or "").strip().upper()


def _norm_text(value: str) -> str:
    return " ".join((value or "").split())


def _index_by_candidate(rows: List[Dict[str, str]], name: str) -> Dict[str, Dict[str, str]]:
    indexed: Dict[str, Dict[str, str]] = {}
    for row in rows:
        candidate_id = (row.get("candidate_id") or "").strip()
        if not candidate_id:
            raise ValueError(f"{name}: missing candidate_id in row {row}")
        if candidate_id in indexed:
            raise ValueError(f"{name}: duplicate candidate_id={candidate_id}")
        indexed[candidate_id] = row
    return indexed


def _validate_alignment(rows_a: List[Dict[str, str]], rows_b: List[Dict[str, str]]) -> None:
    map_a = _index_by_candidate(rows_a, "lawyer_a")
    map_b = _index_by_candidate(rows_b, "lawyer_b")

    if set(map_a.keys()) != set(map_b.keys()):
        only_a = sorted(set(map_a.keys()) - set(map_b.keys()))
        only_b = sorted(set(map_b.keys()) - set(map_a.keys()))
        raise ValueError(
            "candidate_id sets differ between files. "
            f"only_a={only_a[:5]} only_b={only_b[:5]}"
        )

    for cid in map_a:
        ra = map_a[cid]
        rb = map_b[cid]
        for field in BASE_FIELDS:
            if (ra.get(field) or "") != (rb.get(field) or ""):
                raise ValueError(
                    f"Base field mismatch for candidate_id={cid} field={field}"
                )


def _resolve_revised_answer(
    decision_a: str,
    decision_b: str,
    corrected_a: str,
    corrected_b: str,
) -> Tuple[str, str, str]:
    """Returns (final_answer, answer_source, unresolved_reason)."""
    corrected_a = (corrected_a or "").strip()
    corrected_b = (corrected_b or "").strip()

    if decision_a == "REVISE" and decision_b != "REVISE":
        if corrected_a:
            return corrected_a, "lawyerA_corrected", ""
        return "", "", "missing_corrected_answer_lawyerA"

    if decision_b == "REVISE" and decision_a != "REVISE":
        if corrected_b:
            return corrected_b, "lawyerB_corrected", ""
        return "", "", "missing_corrected_answer_lawyerB"

    # REVISE + REVISE
    if corrected_a and corrected_b:
        if _norm_text(corrected_a) == _norm_text(corrected_b):
            return corrected_a, "both_corrected_identical", ""
        # deterministic, transparent tie-break to keep pipeline moving
        return corrected_a, "lawyerA_corrected_tiebreak", ""

    if corrected_a:
        return corrected_a, "lawyerA_corrected_only", ""
    if corrected_b:
        return corrected_b, "lawyerB_corrected_only", ""

    return "", "", "missing_corrected_answer_both_lawyers"


def reconcile(rows_a: List[Dict[str, str]], rows_b: List[Dict[str, str]]) -> Dict[str, object]:
    _validate_alignment(rows_a, rows_b)

    map_a = _index_by_candidate(rows_a, "lawyer_a")
    map_b = _index_by_candidate(rows_b, "lawyer_b")

    ordered = sorted(rows_a, key=lambda r: int((r.get("batch_item_no") or "0").strip() or 0))

    reconciled_rows: List[Dict[str, str]] = []
    approved_revised_rows: List[Dict[str, str]] = []
    rejected_or_manual_rows: List[Dict[str, str]] = []
    sft_records: List[Dict[str, str]] = []

    pair_counter: Counter[str] = Counter()
    bucket_counter: Counter[str] = Counter()
    disagreement_count = 0

    breakdown_difficulty = defaultdict(lambda: Counter())
    breakdown_category = defaultdict(lambda: Counter())

    for ra in ordered:
        cid = ra["candidate_id"]
        rb = map_b[cid]

        da = _norm_decision(ra.get("lawyer_decision", ""))
        db = _norm_decision(rb.get("lawyer_decision", ""))

        pair = f"{da}+{db}"
        pair_counter[pair] += 1
        if da != db:
            disagreement_count += 1

        unresolved_reason = ""
        final_answer = ""
        final_answer_source = ""

        if da not in VALID_DECISIONS or db not in VALID_DECISIONS:
            final_bucket = "manual_escalation"
            unresolved_reason = "invalid_or_missing_decision"
        elif "REJECT" in (da, db):
            final_bucket = "manual_escalation"
            unresolved_reason = "contains_reject"
        elif da == "APPROVE" and db == "APPROVE":
            final_bucket = "approved"
            final_answer = (ra.get("generated_answer") or "").strip()
            final_answer_source = "generated_answer"
        else:
            final_bucket = "revised_needed"
            final_answer, final_answer_source, unresolved_reason = _resolve_revised_answer(
                da,
                db,
                ra.get("corrected_answer", ""),
                rb.get("corrected_answer", ""),
            )
            if unresolved_reason:
                final_bucket = "manual_escalation"

        include_in_training = final_bucket in {"approved", "revised_needed"} and bool(final_answer)

        out = {
            **{field: ra.get(field, "") for field in BASE_FIELDS},
            "lawyerA_decision": da,
            "lawyerA_comment": (ra.get("lawyer_comment") or "").strip(),
            "lawyerA_corrected_answer": (ra.get("corrected_answer") or "").strip(),
            "lawyerA_reviewer_name": (ra.get("reviewer_name") or "").strip(),
            "lawyerB_decision": db,
            "lawyerB_comment": (rb.get("lawyer_comment") or "").strip(),
            "lawyerB_corrected_answer": (rb.get("corrected_answer") or "").strip(),
            "lawyerB_reviewer_name": (rb.get("reviewer_name") or "").strip(),
            "decision_pair": pair,
            "is_disagreement": "1" if da != db else "0",
            "final_bucket": final_bucket,
            "final_answer_source": final_answer_source,
            "final_answer": final_answer,
            "include_in_training": "1" if include_in_training else "0",
            "unresolved_reason": unresolved_reason,
        }
        reconciled_rows.append(out)

        bucket_counter[final_bucket] += 1
        breakdown_difficulty[(ra.get("difficulty") or "unknown").strip()][final_bucket] += 1
        breakdown_category[(ra.get("category") or "unknown").strip()][final_bucket] += 1

        if include_in_training:
            approved_revised_rows.append(out)
            sft_records.append(
                {
                    "instruction": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.",
                    "input": f"KAYNAKLAR:\n{ra.get('context', '')}\n\nSORU: {ra.get('question', '')}",
                    "output": final_answer,
                }
            )
        else:
            rejected_or_manual_rows.append(out)

    total = len(reconciled_rows)
    approval_like = bucket_counter["approved"] + bucket_counter["revised_needed"]
    gate_pct = (approval_like / total * 100.0) if total else 0.0

    summary = {
        "total_records": total,
        "decision_pair_counts": dict(sorted(pair_counter.items())),
        "final_bucket_counts": dict(sorted(bucket_counter.items())),
        "agreement_count": total - disagreement_count,
        "disagreement_count": disagreement_count,
        "approval_gate_percentage": round(gate_pct, 2),
        "approval_gate_passed": gate_pct >= 80.0,
        "training_candidate_count": len(sft_records),
        "manual_review_count": bucket_counter["manual_escalation"],
        "breakdown_by_difficulty": {
            k: dict(sorted(v.items())) for k, v in sorted(breakdown_difficulty.items())
        },
        "breakdown_by_category": {
            k: dict(sorted(v.items())) for k, v in sorted(breakdown_category.items())
        },
        "policy": {
            "APPROVE+APPROVE": "approved",
            "any_REJECT": "manual_escalation",
            "APPROVE+REVISE_or_REVISE+REVISE": "revised_needed (requires corrected_answer if any REVISE)",
            "revised_tiebreak_when_both_corrected_differ": "prefer_lawyerA_corrected",
        },
    }

    return {
        "reconciled_rows": reconciled_rows,
        "approved_revised_rows": approved_revised_rows,
        "rejected_or_manual_rows": rejected_or_manual_rows,
        "sft_records": sft_records,
        "summary": summary,
    }


def _write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = [
            *BASE_FIELDS,
            "lawyerA_decision",
            "lawyerA_comment",
            "lawyerA_corrected_answer",
            "lawyerA_reviewer_name",
            "lawyerB_decision",
            "lawyerB_comment",
            "lawyerB_corrected_answer",
            "lawyerB_reviewer_name",
            "decision_pair",
            "is_disagreement",
            "final_bucket",
            "final_answer_source",
            "final_answer",
            "include_in_training",
            "unresolved_reason",
        ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_jsonl(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile two lawyer-reviewed CSV files.")
    parser.add_argument("--lawyer-a", required=True, help="Path to lawyer A reviewed CSV")
    parser.add_argument("--lawyer-b", required=True, help="Path to lawyer B reviewed CSV")
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Output directory for reconciled CSV/JSONL/summary",
    )
    parser.add_argument(
        "--training-jsonl",
        required=True,
        help="Output JSONL path for approved training candidate records",
    )
    args = parser.parse_args()

    rows_a = _read_rows(Path(args.lawyer_a))
    rows_b = _read_rows(Path(args.lawyer_b))
    result = reconcile(rows_a, rows_b)

    out_dir = Path(args.out_dir)
    reconciled_csv = out_dir / "batch1_first100_reconciled_master.csv"
    reconciled_jsonl = out_dir / "batch1_first100_reconciled_master.jsonl"
    approved_revised_csv = out_dir / "batch1_first100_approved_revised.csv"
    rejected_manual_csv = out_dir / "batch1_first100_rejected_or_manual.csv"
    summary_json = out_dir / "batch1_first100_reconciliation_summary.json"

    _write_csv(reconciled_csv, result["reconciled_rows"])
    _write_jsonl(reconciled_jsonl, result["reconciled_rows"])
    _write_csv(approved_revised_csv, result["approved_revised_rows"])
    _write_csv(rejected_manual_csv, result["rejected_or_manual_rows"])
    _write_json(summary_json, result["summary"])
    _write_jsonl(Path(args.training_jsonl), result["sft_records"])

    print(json.dumps({
        "reconciled_csv": str(reconciled_csv),
        "reconciled_jsonl": str(reconciled_jsonl),
        "approved_revised_csv": str(approved_revised_csv),
        "rejected_manual_csv": str(rejected_manual_csv),
        "summary_json": str(summary_json),
        "training_jsonl": str(args.training_jsonl),
        "summary": result["summary"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
