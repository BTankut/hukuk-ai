#!/usr/bin/env python3
"""
build_training_dataset.py — Assemble final SFT JSONL from reconciled lawyer reviews.

Data flow:
  Reconciled master JSONL
    ├── final_bucket == "approved"       → use generated_answer  (model was right)
    └── final_bucket == "revised_needed" → use final_answer       (lawyer correction)
  ↓
  Supplementary SFT files (legal_qa, petition_examples, rag_corrected, refusal_examples)
  ↓
  Quality gate checks
  ↓
  data/finetune/sft/final_train.jsonl   (deduplicated, validated, shuffled)

Usage:
    # Build training set (dry-run, no file write)
    python scripts/build_training_dataset.py --dry-run

    # Build and write (all discovered reconciled masters by default)
    python scripts/build_training_dataset.py

    # With a specific reconciled file
    python scripts/build_training_dataset.py \\
        --reconciled data/review_sheets/.../batch1_first100_reconciled_master.jsonl

    # Verbose output
    python scripts/build_training_dataset.py --verbose
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_RECONCILED_MASTERS = sorted(
    PROJECT_ROOT.glob("data/review_sheets/**/reconciled_*/*reconciled_master.jsonl")
)
SUPPLEMENTARY_FILES = [
    PROJECT_ROOT / "data/finetune/sft/legal_qa.jsonl",
    PROJECT_ROOT / "data/finetune/sft/petition_examples.jsonl",
    PROJECT_ROOT / "data/finetune/sft/rag_corrected.jsonl",
    PROJECT_ROOT / "data/finetune/sft/refusal_examples.jsonl",
]
HELD_OUT_FILE = PROJECT_ROOT / "data/finetune/eval/held_out_test.jsonl"
OUTPUT_FILE   = PROJECT_ROOT / "data/finetune/sft/final_train.jsonl"

# ---- Quality gate thresholds (must match sft_config.yaml) ----
MIN_EXAMPLES          = 80
MAX_EMPTY_OUTPUT_PCT  = 1.0   # %
MAX_MISSING_CITE_PCT  = 30.0  # % (warning, not hard fail)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("build_training_dataset")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SFT_INSTRUCTION = "Aşağıdaki kaynaklara dayanarak soruyu yanıtla."


def _is_scaffolding(record: dict) -> bool:
    """Skip placeholder/scaffolding rows written during repo init."""
    for v in record.values():
        if isinstance(v, str) and "SCAFFOLDING" in v:
            return True
    return False


def _extract_question(text: str) -> str:
    """Normalize free text or SFT input payload into the bare question string."""
    if "\n\nSORU:" in text:
        return text.split("\n\nSORU:", 1)[1].strip()
    if "SORU:" in text:
        return text.split("SORU:", 1)[1].strip()
    return text.strip()


def _build_sft_row(
    instruction: str,
    context: str,
    question: str,
    answer: str,
    source_id: str = "",
    bucket: str = "",
    difficulty: str = "",
    category: str = "",
) -> dict:
    return {
        "instruction": instruction,
        "input": f"KAYNAKLAR:\n{context}\n\nSORU: {question}",
        "output": answer,
        "_meta": {
            "source_id": source_id,
            "bucket": bucket,       # "approved" | "revised_needed"
            "difficulty": difficulty,
            "category": category,
        },
    }


def load_reconciled(path: Path, verbose: bool = False) -> list[dict]:
    """
    Load reconciled master JSONL.

    Rules:
      - approved       → output = generated_answer  (model was correct)
      - revised_needed → output = final_answer       (lawyer correction)
      - include_in_training == "0" → skip
      - SCAFFOLDING rows → skip
    """
    records: list[dict] = []
    skipped = {"not_included": 0, "scaffolding": 0, "no_answer": 0}
    approved_count = 0
    revised_count = 0

    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("Line %d: JSON decode error: %s", lineno, e)
                continue

            if _is_scaffolding(row):
                skipped["scaffolding"] += 1
                continue

            if str(row.get("include_in_training", "1")) == "0":
                skipped["not_included"] += 1
                continue

            bucket = str(row.get("final_bucket", "")).strip()
            if bucket == "approved":
                answer = row.get("generated_answer", "").strip()
                approved_count += 1
            elif bucket == "revised_needed":
                answer = row.get("final_answer", "").strip()
                revised_count += 1
            else:
                # Unexpected bucket — use final_answer if available
                answer = row.get("final_answer", row.get("generated_answer", "")).strip()
                log.warning(
                    "Line %d: unknown bucket=%r, candidate_id=%s",
                    lineno, bucket, row.get("candidate_id", "?"),
                )

            if not answer:
                skipped["no_answer"] += 1
                if verbose:
                    log.debug("Line %d: empty answer, skipping (id=%s)", lineno, row.get("candidate_id"))
                continue

            sft_row = _build_sft_row(
                instruction=SFT_INSTRUCTION,
                context=row.get("context", ""),
                question=row.get("question", ""),
                answer=answer,
                source_id=row.get("candidate_id", ""),
                bucket=bucket,
                difficulty=row.get("difficulty", ""),
                category=row.get("category", ""),
            )
            records.append(sft_row)

    log.info(
        "Reconciled: %d loaded  (approved=%d, revised=%d)  | skipped: %s",
        len(records), approved_count, revised_count, skipped,
    )
    return records


def load_supplementary(paths: list[Path], verbose: bool = False) -> list[dict]:
    """Load supplementary SFT JSONL files (legal_qa, petition, etc.)."""
    records: list[dict] = []
    for path in paths:
        if not path.exists():
            log.debug("Supplementary file not found, skipping: %s", path)
            continue
        count = 0
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    log.warning("%s line %d: JSON error", path.name, lineno)
                    continue
                if _is_scaffolding(row):
                    continue
                if not all(row.get(k) for k in ("instruction", "input", "output")):
                    if verbose:
                        log.debug("%s line %d: missing required keys", path.name, lineno)
                    continue
                # Tag with source file info
                row.setdefault("_meta", {})["source_id"] = f"{path.stem}:{lineno}"
                row["_meta"]["bucket"] = "supplementary"
                records.append(row)
                count += 1
        log.info("Supplementary %s: %d examples", path.name, count)
    return records


def load_held_out(path: Path) -> set[str]:
    """Return the set of questions in the held-out test (to avoid contamination)."""
    questions: set[str] = set()
    if not path.exists():
        return questions
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                q = _extract_question(row.get("input", row.get("question", "")))
                if q and "SCAFFOLDING" not in q:
                    questions.add(q.strip())
            except json.JSONDecodeError:
                pass
    return questions


def quality_gate(records: list[dict]) -> bool:
    """Run pre-training quality checks. Returns True if all hard gates pass."""
    ok = True
    n = len(records)

    # Gate 1: minimum examples
    if n < MIN_EXAMPLES:
        log.error("GATE FAIL: only %d training examples, need >= %d", n, MIN_EXAMPLES)
        ok = False
    else:
        log.info("Gate 1 PASS: %d examples (min %d)", n, MIN_EXAMPLES)

    # Gate 2: empty outputs
    empty = sum(1 for r in records if not r.get("output", "").strip())
    empty_pct = (empty / n * 100) if n else 0
    if empty_pct > MAX_EMPTY_OUTPUT_PCT:
        log.error("GATE FAIL: %.1f%% empty outputs (max %.1f%%)", empty_pct, MAX_EMPTY_OUTPUT_PCT)
        ok = False
    else:
        log.info("Gate 2 PASS: %.1f%% empty outputs", empty_pct)

    # Gate 3: citation coverage (soft warning, not a hard fail)
    no_cite = sum(1 for r in records if "[Kaynak:" not in r.get("output", ""))
    no_cite_pct = (no_cite / n * 100) if n else 0
    if no_cite_pct > MAX_MISSING_CITE_PCT:
        log.warning(
            "CITATION WARNING: %.1f%% outputs missing [Kaynak:] tag (threshold %.1f%%)",
            no_cite_pct, MAX_MISSING_CITE_PCT,
        )
    else:
        log.info("Gate 3 OK: %.1f%% outputs missing citation (threshold %.1f%%)", no_cite_pct, MAX_MISSING_CITE_PCT)

    # Breakdown by bucket
    buckets: dict[str, int] = {}
    for r in records:
        b = r.get("_meta", {}).get("bucket", "unknown")
        buckets[b] = buckets.get(b, 0) + 1
    log.info("Bucket breakdown: %s", buckets)

    return ok


def deduplicate(records: list[dict]) -> list[dict]:
    """Remove duplicates based on (instruction, input, output) hash."""
    seen: set[str] = set()
    unique: list[dict] = []
    for r in records:
        key = json.dumps(
            {"i": r.get("instruction"), "inp": r.get("input"), "o": r.get("output")},
            ensure_ascii=False, sort_keys=True,
        )
        if key not in seen:
            seen.add(key)
            unique.append(r)
    removed = len(records) - len(unique)
    if removed:
        log.info("Deduplication: removed %d duplicates", removed)
    return unique


def filter_held_out_contamination(records: list[dict], held_out_questions: set[str]) -> list[dict]:
    """Remove any training example whose question appears in the held-out test."""
    if not held_out_questions:
        return records
    clean = []
    removed = 0
    for r in records:
        question_part = _extract_question(r.get("input", ""))
        if question_part in held_out_questions:
            removed += 1
        else:
            clean.append(r)
    if removed:
        log.info("Held-out contamination filter: removed %d examples", removed)
    return clean


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SFT training dataset from reconciled reviews")
    parser.add_argument(
        "--reconciled",
        nargs="+",
        default=[str(path) for path in DEFAULT_RECONCILED_MASTERS],
        help="Path(s) to reconciled master JSONL. Defaults to all discovered reconciled masters.",
    )
    parser.add_argument("--output", default=str(OUTPUT_FILE),
                        help="Output JSONL path")
    parser.add_argument("--no-supplementary", action="store_true",
                        help="Skip supplementary SFT files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and report without writing output file")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for shuffling")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    output_path = Path(args.output)
    
    # 1. Load reconciled master (approved + revised)
    records = []
    reconciled_paths = [Path(p) for p in args.reconciled] if isinstance(args.reconciled, list) else [Path(args.reconciled)]
    log.info("Reconciled source files: %d", len(reconciled_paths))
    for pth in reconciled_paths:
        if not pth.exists():
            log.error("Reconciled file not found: %s", pth)
            return 1
        records.extend(load_reconciled(pth, verbose=args.verbose))

    # 2. Append supplementary files
    if not args.no_supplementary:
        supp = load_supplementary(SUPPLEMENTARY_FILES, verbose=args.verbose)
        records.extend(supp)

    # 3. Deduplicate
    records = deduplicate(records)

    # 4. Filter held-out contamination
    held_out_questions = load_held_out(HELD_OUT_FILE)
    if held_out_questions:
        records = filter_held_out_contamination(records, held_out_questions)

    # 5. Shuffle deterministically
    random.seed(args.seed)
    random.shuffle(records)

    # 6. Quality gate
    gate_passed = quality_gate(records)
    if not gate_passed:
        log.error("Quality gate FAILED. Aborting. Fix issues before training.")
        return 1

    log.info("Total training examples: %d", len(records))

    # 7. Write (unless dry-run)
    if args.dry_run:
        log.info("DRY RUN — no file written. Would write %d examples to %s", len(records), output_path)
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            # Strip internal _meta field before writing (trainers don't need it)
            row = {k: v for k, v in r.items() if k != "_meta"}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    log.info("Wrote %d examples → %s", written, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
