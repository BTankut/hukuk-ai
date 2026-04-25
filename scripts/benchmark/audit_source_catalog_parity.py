#!/usr/bin/env python3
"""Compare source catalog/config material between current repo and a baseline checkout."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE_ROOT = REPO_ROOT.parent / "hukuk-ai-ablation-phase17f"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_18_recovery_source_catalog_parity.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_18_recovery_source_catalog_parity.md"
FILE_GLOBS = {
    "runtime_catalog_code": [
        "api-gateway/src/rag/source_catalog.py",
        "api-gateway/src/rag/retriever.py",
        "api-gateway/src/source_family_resolver.py",
    ],
    "runtime_supplement_code": [
        "api-gateway/src/rag/source_supplements.py",
        "api-gateway/src/rag/required_slot_matrix.py",
        "api-gateway/src/rag/required_slot_matrix.json",
    ],
    "benchmark_catalog_reports": [
        "reports/benchmark/phase_05_canonical_source_catalog.csv",
        "reports/benchmark/phase_14_canonical_span_materialization_audit.csv",
        "reports/benchmark/phase_16a_corpus_materialization_remediation.csv",
        "reports/benchmark/phase_16e_corpus_materialization_remediation.csv",
        "reports/benchmark/phase_17a_corpus_materialization_remediation.csv",
        "reports/benchmark/phase_17b_corpus_materialization_remediation.csv",
        "reports/benchmark/phase_17a_sourcekey_binding_audit.csv",
        "reports/benchmark/phase_17b_sourcekey_binding_audit.csv",
    ],
    "primary_source_text": [
        "data/primary_sources/full_acquisition/*/source_manifest.json",
        "data/primary_sources/full_acquisition/*/normalized_source.txt",
    ],
    "benchmark_config": [
        "configs/evaluation/hukuk_ai_100_public_questions.csv",
        "evaluation/hukuk_ai_100_article_alignment.py",
        "evaluation/hukuk_ai_100_source_schema.py",
        "scripts/benchmark/run_hukuk_ai_100.py",
        "scripts/benchmark/score_hukuk_ai_100.py",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE_ROOT)
    parser.add_argument("--baseline-label", default="phase17f_checkout")
    parser.add_argument("--current-label", default="current_checkout")
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    try:
        with path.open("rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def csv_row_count(path: Path) -> int | None:
    if path.suffix.lower() != ".csv" or not path.exists():
        return None
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = sum(1 for _ in reader)
    return max(rows - 1, 0)


def collect_rel_paths(root: Path) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for group, patterns in FILE_GLOBS.items():
        paths: set[str] = set()
        for pattern in patterns:
            for path in root.glob(pattern):
                if path.is_file():
                    paths.add(path.relative_to(root).as_posix())
        found[group] = paths
    return found


def record_for(root: Path, rel_path: str) -> dict[str, str]:
    path = root / rel_path
    if not path.exists():
        return {
            "exists": "False",
            "sha256": "",
            "bytes": "",
            "lines": "",
            "csv_rows": "",
        }
    return {
        "exists": "True",
        "sha256": sha256(path),
        "bytes": str(path.stat().st_size),
        "lines": str(line_count(path)),
        "csv_rows": "" if csv_row_count(path) is None else str(csv_row_count(path)),
    }


def build_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    current_paths = collect_rel_paths(args.current_root)
    baseline_paths = collect_rel_paths(args.baseline_root)
    rows: list[dict[str, str]] = []
    for group in FILE_GLOBS:
        rel_paths = sorted(current_paths.get(group, set()) | baseline_paths.get(group, set()))
        for rel_path in rel_paths:
            current = record_for(args.current_root, rel_path)
            baseline = record_for(args.baseline_root, rel_path)
            if current["exists"] == "False" and baseline["exists"] == "False":
                status = "missing_both"
            elif current["exists"] != baseline["exists"]:
                status = "presence_diff"
            elif current["sha256"] != baseline["sha256"]:
                status = "hash_diff"
            else:
                status = "match"
            rows.append(
                {
                    "group": group,
                    "path": rel_path,
                    "status": status,
                    "current_exists": current["exists"],
                    "baseline_exists": baseline["exists"],
                    "current_sha256": current["sha256"],
                    "baseline_sha256": baseline["sha256"],
                    "current_bytes": current["bytes"],
                    "baseline_bytes": baseline["bytes"],
                    "current_lines": current["lines"],
                    "baseline_lines": baseline["lines"],
                    "current_csv_rows": current["csv_rows"],
                    "baseline_csv_rows": baseline["csv_rows"],
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "group",
        "path",
        "status",
        "current_exists",
        "baseline_exists",
        "current_sha256",
        "baseline_sha256",
        "current_bytes",
        "baseline_bytes",
        "current_lines",
        "baseline_lines",
        "current_csv_rows",
        "baseline_csv_rows",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, args: argparse.Namespace, rows: list[dict[str, str]]) -> None:
    status_counts: dict[str, int] = {}
    group_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        group_counts.setdefault(row["group"], {})
        group_counts[row["group"]][row["status"]] = group_counts[row["group"]].get(row["status"], 0) + 1
    lines = [
        "# Phase 18 Recovery Source Catalog Parity Audit",
        "",
        f"- current_root: `{args.current_root}`",
        f"- baseline_root: `{args.baseline_root}`",
        f"- compared_files: {len(rows)}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Group Counts", ""])
    for group, counts in sorted(group_counts.items()):
        summary = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
        lines.append(f"- {group}: {summary}")
    lines.extend(["", "## Changed Or Missing Files", ""])
    changed = [row for row in rows if row["status"] != "match"]
    for row in changed[:80]:
        lines.append(
            "- "
            f"{row['status']}: `{row['path']}` "
            f"(current_lines={row['current_lines'] or 'NA'}, baseline_lines={row['baseline_lines'] or 'NA'})"
        )
    if not changed:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_rows(args)
    write_csv(args.out_csv, rows)
    write_md(args.out_md, args, rows)
    print(f"wrote {args.out_csv} and {args.out_md} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
