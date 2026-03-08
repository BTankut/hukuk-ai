#!/usr/bin/env python3
"""Prepare lawyer review CSV sheets from pending-review JSONL candidates.

Supports optional metadata enrichment (difficulty/category/source fields) and
balanced sub-sampling for practical first-batch packet generation.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def parse_input_field(raw_input: str, fallback_question: str) -> tuple[str, str]:
    """Extract context + question from SFT input format.

    Expected format:
        KAYNAKLAR:\n<context>\n\nSORU: <question>
    """
    if "SORU:" in raw_input:
        parts = raw_input.split("SORU:", 1)
        context = parts[0].replace("KAYNAKLAR:\n", "", 1).strip()
        question = parts[1].strip()
        return context, question

    return raw_input.strip(), fallback_question.strip()


def load_qa_records(input_jsonl: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with input_jsonl.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"Warning: Skipped invalid JSON line at #{line_no}.", file=sys.stderr)
                continue

            raw_input = str(data.get("input", ""))
            context, question = parse_input_field(raw_input, str(data.get("instruction", "")))
            records.append(
                {
                    "_line_no": line_no,
                    "question": question,
                    "context": context,
                    "generated_answer": str(data.get("output", "")),
                }
            )

    return records


def load_metadata_records(metadata_jsonl: Path, split_filter: str | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with metadata_jsonl.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(
                    f"Warning: Skipped invalid metadata JSON line at #{line_no}.",
                    file=sys.stderr,
                )
                continue

            if split_filter and row.get("split") != split_filter:
                continue

            rows.append(row)
    return rows


def merge_records(
    qa_records: list[dict[str, Any]],
    metadata_records: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []

    if metadata_records is None:
        for idx, qa in enumerate(qa_records, start=1):
            merged.append(
                {
                    "batch_item_no": idx,
                    "candidate_id": str(uuid.uuid4())[:8],
                    "question_id": "",
                    "difficulty": "",
                    "category": "",
                    "source_file": "",
                    "source_record_id": "",
                    "split": "",
                    "refusal_expected": "",
                    "is_hallucination": "",
                    "has_citation": "",
                    "response_time_ms": "",
                    "question": qa["question"],
                    "context": qa["context"],
                    "generated_answer": qa["generated_answer"],
                    "lawyer_decision": "",
                    "lawyer_comment": "",
                    "corrected_answer": "",
                    "reviewer_name": "",
                }
            )
        return merged

    if len(qa_records) != len(metadata_records):
        print(
            "Error: QA and metadata record counts do not match. "
            f"qa_records={len(qa_records)}, metadata_records={len(metadata_records)}.\n"
            "Tip: use --metadata-split for sft_train/sft_heldout inputs.",
            file=sys.stderr,
        )
        sys.exit(1)

    for idx, (qa, meta) in enumerate(zip(qa_records, metadata_records), start=1):
        meta_blob = meta.get("metadata") or {}
        merged.append(
            {
                "batch_item_no": idx,
                "candidate_id": str(meta.get("candidate_id", "")),
                "question_id": str(meta_blob.get("question_id", "")),
                "difficulty": str(meta_blob.get("difficulty", "")),
                "category": str(meta_blob.get("category", "")),
                "source_file": str(meta.get("source_file", "")),
                "source_record_id": str(meta.get("source_record_id", "")),
                "split": str(meta.get("split", "")),
                "refusal_expected": str(meta_blob.get("refusal_expected", "")),
                "is_hallucination": str(meta_blob.get("is_hallucination", "")),
                "has_citation": str(meta_blob.get("has_citation", "")),
                "response_time_ms": str(meta_blob.get("response_time_ms", "")),
                "question": qa["question"],
                "context": qa["context"],
                "generated_answer": qa["generated_answer"],
                "lawyer_decision": "",
                "lawyer_comment": "",
                "corrected_answer": "",
                "reviewer_name": "",
            }
        )

    return merged


def proportional_targets(counter: Counter[str], total: int) -> dict[str, int]:
    if total <= 0 or not counter:
        return {}

    grand_total = sum(counter.values())
    base: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []

    allocated = 0
    for key, count in counter.items():
        exact = (count / grand_total) * total
        floor_val = int(exact)
        base[key] = floor_val
        allocated += floor_val
        remainders.append((exact - floor_val, key))

    missing = total - allocated
    remainders.sort(key=lambda x: (-x[0], x[1]))
    for _, key in remainders[:missing]:
        base[key] += 1

    return base


def source_priority_map(preferred_sources: list[str]) -> dict[str, int]:
    return {src: i for i, src in enumerate(preferred_sources)}


def sort_key(record: dict[str, Any], src_rank: dict[str, int]) -> tuple[Any, ...]:
    return (
        DIFFICULTY_ORDER.get(record.get("difficulty", ""), 99),
        record.get("category", ""),
        record.get("question_id", ""),
        src_rank.get(record.get("source_file", ""), 9999),
        record.get("source_file", ""),
        record.get("candidate_id", ""),
    )


def pick_distinct_sources(
    rows: list[dict[str, Any]],
    k: int,
    src_rank: dict[str, int],
) -> list[dict[str, Any]]:
    if k <= 0:
        return []

    ordered = sorted(rows, key=lambda r: (src_rank.get(r.get("source_file", ""), 9999), r.get("candidate_id", "")))
    picked: list[dict[str, Any]] = []
    used_sources: set[str] = set()

    for row in ordered:
        src = row.get("source_file", "")
        if src in used_sources:
            continue
        picked.append(row)
        used_sources.add(src)
        if len(picked) >= k:
            return picked

    for row in ordered:
        if row in picked:
            continue
        picked.append(row)
        if len(picked) >= k:
            break

    return picked


def select_balanced(
    records: list[dict[str, Any]],
    limit: int,
    preferred_sources: list[str],
) -> list[dict[str, Any]]:
    if limit >= len(records):
        return list(records)

    qid_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        qid = row.get("question_id") or row.get("question") or row.get("candidate_id")
        qid_groups[str(qid)].append(row)

    src_rank = source_priority_map(preferred_sources)

    # Base pass: broad question coverage first (2 per question when possible).
    questions = sorted(qid_groups.keys())
    initial_k = 2 if limit >= len(questions) * 2 else 1
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for qid in questions:
        rows = qid_groups[qid]
        for row in pick_distinct_sources(rows, initial_k, src_rank):
            cid = row.get("candidate_id") or f"{qid}:{row.get('source_file','')}"
            if cid in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(cid)
            if len(selected) >= limit:
                break
        if len(selected) >= limit:
            break

    if len(selected) >= limit:
        return sorted(selected[:limit], key=lambda r: sort_key(r, src_rank))

    remaining = [
        row
        for row in records
        if (row.get("candidate_id") or f"{row.get('question_id')}:{row.get('source_file')}:{id(row)}") not in selected_ids
    ]

    diff_target = proportional_targets(Counter(r.get("difficulty", "") for r in records), limit)
    cat_target = proportional_targets(Counter(r.get("category", "") for r in records), limit)

    q_counts = Counter((r.get("question_id") or r.get("question")) for r in selected)
    diff_counts = Counter(r.get("difficulty", "") for r in selected)
    cat_counts = Counter(r.get("category", "") for r in selected)

    while len(selected) < limit and remaining:
        best_idx = None
        best_score = None

        for idx, row in enumerate(remaining):
            qid = row.get("question_id") or row.get("question")
            diff = row.get("difficulty", "")
            cat = row.get("category", "")

            diff_deficit = diff_target.get(diff, 0) - diff_counts.get(diff, 0)
            cat_deficit = cat_target.get(cat, 0) - cat_counts.get(cat, 0)

            score = (
                max(diff_deficit, 0) * 100
                + max(cat_deficit, 0) * 10
                + max(3 - q_counts.get(qid, 0), 0)
            )

            tie = (
                -q_counts.get(qid, 0),
                -src_rank.get(row.get("source_file", ""), 9999),
                row.get("candidate_id", ""),
            )
            candidate_score = (score, tie)

            if best_score is None or candidate_score > best_score:
                best_score = candidate_score
                best_idx = idx

        if best_idx is None:
            break

        chosen = remaining.pop(best_idx)
        selected.append(chosen)

        qid = chosen.get("question_id") or chosen.get("question")
        q_counts[qid] += 1
        diff_counts[chosen.get("difficulty", "")] += 1
        cat_counts[chosen.get("category", "")] += 1

    return sorted(selected[:limit], key=lambda r: sort_key(r, src_rank))


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(records),
        "difficulty": dict(sorted(Counter(r.get("difficulty", "") for r in records).items())),
        "category": dict(sorted(Counter(r.get("category", "") for r in records).items())),
        "source_file": dict(sorted(Counter(r.get("source_file", "") for r in records).items())),
        "question_id_unique": len({r.get("question_id", "") for r in records if r.get("question_id", "")}),
    }


def write_csv(records: list[dict[str, Any]], output_csv: Path) -> None:
    headers = [
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
        "lawyer_decision",
        "lawyer_comment",
        "corrected_answer",
        "reviewer_name",
    ]

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for idx, row in enumerate(records, start=1):
            row = dict(row)
            row["batch_item_no"] = idx
            writer.writerow({h: row.get(h, "") for h in headers})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare lawyer review CSV sheets.")
    parser.add_argument("input_jsonl", help="Input SFT candidate JSONL file.")
    parser.add_argument("output_csv", help="Output review CSV path.")
    parser.add_argument(
        "--metadata-jsonl",
        help="Optional candidate_metadata.jsonl for difficulty/category/source enrichment.",
    )
    parser.add_argument(
        "--metadata-split",
        choices=["train_pending_review", "heldout_pending_review"],
        help="Filter metadata rows by split before alignment.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Optional max number of rows.")
    parser.add_argument(
        "--selection",
        choices=["sequential", "balanced"],
        default="sequential",
        help="Sampling strategy when --limit is set.",
    )
    parser.add_argument(
        "--preferred-sources",
        default="",
        help="Comma-separated source_file priority list used by balanced selection.",
    )
    parser.add_argument(
        "--stats-output",
        help="Optional JSON summary output path (counts + distributions).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_jsonl)
    output_path = Path(args.output_csv)

    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    qa_records = load_qa_records(input_path)

    metadata_rows = None
    if args.metadata_jsonl:
        meta_path = Path(args.metadata_jsonl)
        if not meta_path.exists():
            print(f"Error: Metadata file does not exist: {meta_path}", file=sys.stderr)
            sys.exit(1)
        metadata_rows = load_metadata_records(meta_path, args.metadata_split)

    merged = merge_records(qa_records, metadata_rows)

    selected = merged
    if args.limit and args.limit > 0:
        limit = min(args.limit, len(merged))
        if args.selection == "balanced":
            preferred_sources = [s.strip() for s in args.preferred_sources.split(",") if s.strip()]
            selected = select_balanced(merged, limit, preferred_sources)
        else:
            selected = merged[:limit]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(selected, output_path)

    summary = summarize(selected)
    print(f"Successfully generated review sheet: {output_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.stats_output:
        stats_path = Path(args.stats_output)
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_payload = {
            "input": str(input_path),
            "output": str(output_path),
            "selection": args.selection,
            "limit": args.limit,
            "metadata_jsonl": str(args.metadata_jsonl) if args.metadata_jsonl else None,
            "metadata_split": args.metadata_split,
            "summary": summary,
        }
        with stats_path.open("w", encoding="utf-8") as f:
            json.dump(stats_payload, f, ensure_ascii=False, indent=2)
        print(f"Stats written to: {stats_path}")


if __name__ == "__main__":
    main()
