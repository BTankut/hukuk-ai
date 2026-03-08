#!/usr/bin/env python3
"""Extract Phase-1 QA candidates into a raw/pending-review pool.

Supported source formats:
1) JSONL logs with fields like query/context/response.
2) Evaluation reports (evaluation/reports/*.json) with per_question records.

Important:
- Output is ALWAYS candidate/raw data (not lawyer-approved).
- Held-out split is deterministic and reproducible by question hash bucket.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("extract_qa")

DEFAULT_INSTRUCTION = "Aşağıdaki kaynaklara dayanarak soruyu yanıtla."


@dataclass
class Candidate:
    instruction: str
    input: str
    output: str
    source_file: str
    source_type: str
    source_record_id: str
    question_text: str
    question_key: str
    qa_key: str
    metadata: dict[str, Any]


# -----------------------------
# Helpers
# -----------------------------


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())



def stable_bucket(text: str, modulo: int) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % modulo



def candidate_id(candidate: Candidate) -> str:
    raw = "||".join(
        [candidate.source_file, candidate.source_record_id, candidate.question_key, candidate.qa_key]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]



def to_jsonl_line(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False)



def ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]



def iter_candidate_files(inputs: list[str]) -> list[Path]:
    files: set[Path] = set()
    for raw in inputs:
        p = Path(raw)
        has_glob = any(ch in raw for ch in "*?[]")

        if has_glob:
            for m in p.parent.glob(p.name):
                if m.is_file():
                    files.add(m)
            continue

        if p.is_dir():
            for m in p.rglob("*.json"):
                files.add(m)
            for m in p.rglob("*.jsonl"):
                files.add(m)
            continue

        if p.is_file():
            files.add(p)

    return sorted(files)


# -----------------------------
# Source parsers
# -----------------------------


def parse_jsonl_log(file_path: Path, instruction: str) -> tuple[list[Candidate], dict[str, int]]:
    counts = {
        "lines_total": 0,
        "lines_invalid_json": 0,
        "lines_missing_fields": 0,
        "candidates": 0,
    }
    out: list[Candidate] = []

    with file_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            counts["lines_total"] += 1
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                counts["lines_invalid_json"] += 1
                continue

            question = (
                obj.get("query")
                or obj.get("question")
                or obj.get("prompt")
                or ""
            )
            answer = (
                obj.get("response")
                or obj.get("answer")
                or obj.get("answer_text")
                or obj.get("output")
                or ""
            )

            if not str(question).strip() or not str(answer).strip():
                counts["lines_missing_fields"] += 1
                continue

            context_chunks = ensure_list(obj.get("context"))
            context_text = "\n".join(context_chunks).strip()
            if not context_text:
                context_text = "[Kaynak: BELİRTİLMEMİŞ] Kaynak metni log kaydında yok."

            question = str(question).strip()
            answer = str(answer).strip()
            input_text = f"KAYNAKLAR:\n{context_text}\n\nSORU: {question}"

            q_key = normalize_text(question)
            qa_key = normalize_text(question) + "||" + normalize_text(answer)

            out.append(
                Candidate(
                    instruction=instruction,
                    input=input_text,
                    output=answer,
                    source_file=str(file_path),
                    source_type="jsonl_log",
                    source_record_id=f"line:{line_no}",
                    question_text=question,
                    question_key=q_key,
                    qa_key=qa_key,
                    metadata={
                        "context_line_count": len(context_chunks),
                    },
                )
            )
            counts["candidates"] += 1

    return out, counts



def parse_eval_report(
    file_path: Path,
    instruction: str,
    allow_mock: bool,
    allow_report_with_errors: bool,
) -> tuple[list[Candidate], dict[str, Any]]:
    """Parse eval report JSON with `report_meta` + `per_question`."""
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("report_meta")
    per_question = data.get("per_question")

    summary: dict[str, Any] = {
        "candidates": 0,
        "skipped_no_schema": 0,
        "skipped_mock_report": 0,
        "skipped_errorful_report": 0,
        "rows_total": 0,
        "rows_skipped_missing_fields": 0,
        "rows_skipped_error": 0,
    }

    if not isinstance(meta, dict) or not isinstance(per_question, list):
        summary["skipped_no_schema"] = 1
        return [], summary

    if meta.get("mock_mode") and not allow_mock:
        summary["skipped_mock_report"] = 1
        return [], summary

    if int(meta.get("error_count", 0) or 0) > 0 and not allow_report_with_errors:
        summary["skipped_errorful_report"] = 1
        return [], summary

    out: list[Candidate] = []
    generated_at = meta.get("generated_at")
    api_url = meta.get("api_url")

    for idx, row in enumerate(per_question, start=1):
        summary["rows_total"] += 1

        if row.get("error"):
            summary["rows_skipped_error"] += 1
            continue

        question = str(row.get("question_text") or "").strip()
        answer = str(row.get("answer_text") or "").strip()
        if not question or not answer:
            summary["rows_skipped_missing_fields"] += 1
            continue

        cited_sources_raw = ensure_list(row.get("cited_sources"))
        expected_sources_raw = ensure_list(row.get("expected_sources"))

        # Keep order while removing duplicates.
        cited_sources = list(dict.fromkeys(cited_sources_raw))
        expected_sources = list(dict.fromkeys(expected_sources_raw))

        context_lines: list[str] = []
        if cited_sources:
            for src in cited_sources:
                context_lines.append(
                    f"[Kaynak: {src}] (atıf etiketi; tam kaynak metni eval raporunda yok)"
                )
        elif expected_sources:
            for src in expected_sources:
                context_lines.append(
                    f"[Beklenen Kaynak: {src}] (eval artefaktı metadata alanı)"
                )
        else:
            context_lines.append(
                "[Kaynak: BELİRTİLMEMİŞ] Eval raporunda kaynak metni bulunmuyor."
            )

        input_text = f"KAYNAKLAR:\n{"\n".join(context_lines)}\n\nSORU: {question}"
        q_key = normalize_text(question)
        qa_key = normalize_text(question) + "||" + normalize_text(answer)

        row_id = str(row.get("question_id") or f"row:{idx}")

        out.append(
            Candidate(
                instruction=instruction,
                input=input_text,
                output=answer,
                source_file=str(file_path),
                source_type="eval_report_per_question",
                source_record_id=row_id,
                question_text=question,
                question_key=q_key,
                qa_key=qa_key,
                metadata={
                    "question_id": row.get("question_id"),
                    "category": row.get("category"),
                    "difficulty": row.get("difficulty"),
                    "refusal_expected": row.get("refusal_expected"),
                    "is_hallucination": row.get("is_hallucination"),
                    "has_citation": row.get("has_citation"),
                    "blocked": row.get("blocked"),
                    "response_time_ms": row.get("response_time_ms"),
                    "run_generated_at": generated_at,
                    "api_url": api_url,
                },
            )
        )
        summary["candidates"] += 1

    return out, summary


# -----------------------------
# Main
# -----------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract raw QA candidates from Phase-1 artifacts.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Input files/dirs/globs. Example: evaluation/reports",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Target directory for raw/pending-review outputs.",
    )
    parser.add_argument(
        "--instruction",
        default=DEFAULT_INSTRUCTION,
        help="Instruction text for SFT entries.",
    )
    parser.add_argument(
        "--allow-mock-reports",
        action="store_true",
        help="Include mock eval reports (default: skip).",
    )
    parser.add_argument(
        "--allow-reports-with-errors",
        action="store_true",
        help="Include eval reports whose report_meta.error_count > 0 (default: skip).",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Disable exact QA deduplication.",
    )
    parser.add_argument(
        "--split-modulo",
        type=int,
        default=10,
        help="Modulo for deterministic held-out split (default: 10).",
    )
    parser.add_argument(
        "--heldout-buckets",
        default="0",
        help="Comma-separated bucket ids assigned to held-out split (default: '0').",
    )
    args = parser.parse_args()

    heldout_buckets = {
        int(x.strip())
        for x in args.heldout_buckets.split(",")
        if x.strip()
    }
    if not heldout_buckets:
        raise ValueError("At least one held-out bucket is required.")
    if args.split_modulo <= 1:
        raise ValueError("split-modulo must be > 1")
    if any((x < 0 or x >= args.split_modulo) for x in heldout_buckets):
        raise ValueError("held-out bucket id out of range for split-modulo")

    input_files = iter_candidate_files(args.inputs)
    if not input_files:
        logger.error("No input files found.")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/extract_qa_from_logs.py",
        "instruction": args.instruction,
        "split": {
            "method": "question_hash_bucket",
            "hash": "sha256(normalized_question)",
            "modulo": args.split_modulo,
            "heldout_buckets": sorted(heldout_buckets),
        },
        "settings": {
            "allow_mock_reports": args.allow_mock_reports,
            "allow_reports_with_errors": args.allow_reports_with_errors,
            "dedupe_exact_qa": not args.no_dedupe,
        },
        "sources": [],
        "counts": {},
    }

    all_candidates: list[Candidate] = []

    for path in input_files:
        src_summary: dict[str, Any] = {
            "file": str(path),
            "source_type": "unknown",
            "status": "processed",
            "details": {},
        }
        try:
            if path.suffix.lower() == ".jsonl":
                candidates, details = parse_jsonl_log(path, args.instruction)
                src_summary["source_type"] = "jsonl_log"
                src_summary["details"] = details
                all_candidates.extend(candidates)
            elif path.suffix.lower() == ".json":
                candidates, details = parse_eval_report(
                    path,
                    args.instruction,
                    allow_mock=args.allow_mock_reports,
                    allow_report_with_errors=args.allow_reports_with_errors,
                )
                src_summary["source_type"] = "eval_report_or_other_json"
                src_summary["details"] = details
                all_candidates.extend(candidates)
            else:
                src_summary["status"] = "skipped"
                src_summary["details"] = {"reason": "unsupported_extension"}

        except Exception as exc:  # noqa: BLE001
            src_summary["status"] = "error"
            src_summary["details"] = {"error": str(exc)}
            logger.warning("Failed to parse %s: %s", path, exc)

        manifest["sources"].append(src_summary)

    pre_dedupe_count = len(all_candidates)
    if args.no_dedupe:
        deduped = all_candidates
        duplicates_removed = 0
    else:
        seen: set[str] = set()
        deduped = []
        for c in all_candidates:
            if c.qa_key in seen:
                continue
            seen.add(c.qa_key)
            deduped.append(c)
        duplicates_removed = pre_dedupe_count - len(deduped)

    metadata_records: list[dict[str, Any]] = []
    records_by_id: dict[str, dict[str, Any]] = {}

    for c in deduped:
        bucket = stable_bucket(c.question_key, args.split_modulo)
        split = "heldout_pending_review" if bucket in heldout_buckets else "train_pending_review"

        cid = candidate_id(c)
        records_by_id[cid] = {
            "instruction": c.instruction,
            "input": c.input,
            "output": c.output,
        }

        metadata_records.append(
            {
                "candidate_id": cid,
                "split": split,
                "split_bucket": bucket,
                "source_file": c.source_file,
                "source_type": c.source_type,
                "source_record_id": c.source_record_id,
                "question_text": c.question_text,
                "metadata": c.metadata,
            }
        )

    # Stable deterministic ordering; SFT files follow metadata order.
    metadata_records.sort(key=lambda x: x["candidate_id"])

    train_records = [
        records_by_id[m["candidate_id"]]
        for m in metadata_records
        if m["split"] == "train_pending_review"
    ]
    heldout_records = [
        records_by_id[m["candidate_id"]]
        for m in metadata_records
        if m["split"] == "heldout_pending_review"
    ]
    all_records = train_records + heldout_records

    train_path = output_dir / "sft_train_pending_review.jsonl"
    heldout_path = output_dir / "sft_heldout_pending_review.jsonl"
    all_path = output_dir / "sft_all_pending_review.jsonl"
    metadata_path = output_dir / "candidate_metadata.jsonl"
    manifest_path = output_dir / "extraction_manifest.json"
    report_path = output_dir / "extraction_report.md"

    with train_path.open("w", encoding="utf-8") as f:
        for row in train_records:
            f.write(to_jsonl_line(row) + "\n")

    with heldout_path.open("w", encoding="utf-8") as f:
        for row in heldout_records:
            f.write(to_jsonl_line(row) + "\n")

    with all_path.open("w", encoding="utf-8") as f:
        for row in all_records:
            f.write(to_jsonl_line(row) + "\n")

    with metadata_path.open("w", encoding="utf-8") as f:
        for row in metadata_records:
            f.write(to_jsonl_line(row) + "\n")

    # Aggregate source counts
    source_file_counts: dict[str, int] = {}
    source_type_counts: dict[str, int] = {}
    for m in metadata_records:
        source_file_counts[m["source_file"]] = source_file_counts.get(m["source_file"], 0) + 1
        source_type_counts[m["source_type"]] = source_type_counts.get(m["source_type"], 0) + 1

    manifest["counts"] = {
        "raw_candidates_pre_dedupe": pre_dedupe_count,
        "duplicates_removed_exact_qa": duplicates_removed,
        "total_candidates_post_dedupe": len(metadata_records),
        "train_pending_review": len(train_records),
        "heldout_pending_review": len(heldout_records),
        "source_type_counts": source_type_counts,
        "source_file_counts": source_file_counts,
    }
    manifest["outputs"] = {
        "train": str(train_path),
        "heldout": str(heldout_path),
        "all": str(all_path),
        "metadata": str(metadata_path),
        "manifest": str(manifest_path),
        "report": str(report_path),
    }

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    report_lines = [
        "# Phase 2 P1 — Raw Candidate Extraction Report",
        "",
        "## Status",
        "Raw extraction completed. These files are **NOT lawyer-approved** and are only for pending review.",
        "",
        "## Split Method (Reproducible)",
        f"- Method: `sha256(normalized_question) % {args.split_modulo}`",
        f"- Held-out buckets: `{sorted(heldout_buckets)}`",
        "- Split unit: normalized question text (same question always goes to same split).",
        "",
        "## Counts",
        f"- Raw candidates (pre-dedupe): **{pre_dedupe_count}**",
        f"- Exact QA duplicates removed: **{duplicates_removed}**",
        f"- Total candidates (post-dedupe): **{len(metadata_records)}**",
        f"- Train pending-review: **{len(train_records)}**",
        f"- Held-out pending-review: **{len(heldout_records)}**",
        "",
        "## Source files",
    ]

    for file_name, count in sorted(source_file_counts.items()):
        report_lines.append(f"- `{file_name}` → {count} candidate(s)")

    report_lines.extend(
        [
            "",
            "## Outputs",
            f"- `{train_path}`",
            f"- `{heldout_path}`",
            f"- `{all_path}`",
            f"- `{metadata_path}`",
            f"- `{manifest_path}`",
            "",
            "## Reminder",
            "No record in this output is lawyer-reviewed or approved.",
        ]
    )

    with report_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    logger.info("Wrote %s", train_path)
    logger.info("Wrote %s", heldout_path)
    logger.info("Wrote %s", all_path)
    logger.info("Wrote %s", metadata_path)
    logger.info("Wrote %s", manifest_path)
    logger.info("Wrote %s", report_path)
    logger.info(
        "Extraction complete: total=%d train=%d heldout=%d",
        len(metadata_records),
        len(train_records),
        len(heldout_records),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
