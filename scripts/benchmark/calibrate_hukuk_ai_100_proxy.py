#!/usr/bin/env python3
"""Calibrate Phase 1 proxy scores against a public label-only subset."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALIBRATION = REPO_ROOT / "configs/evaluation/hukuk_ai_100_calibration_subset.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scored", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def band_for_score(score: float) -> str:
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


def band_distance(expected: str, actual: str) -> int:
    order = {"low": 0, "medium": 1, "high": 2}
    return abs(order[expected] - order[actual])


def split_flags(value: str) -> set[str]:
    return {part.strip() for part in (value or "").split("|") if part.strip()}


def write_md(path: Path, summary: dict[str, Any], rows: list[dict[str, str]]) -> None:
    lines = [
        "# hukuk-ai 100 proxy calibration",
        "",
        f"- calibration_mode: `{summary['calibration_mode']}`",
        f"- label_source: `{summary['label_source']}`",
        f"- total: {summary['total']}",
        f"- exact_band_accuracy: {summary['exact_band_accuracy']}",
        f"- adjacent_or_exact_band_accuracy: {summary['adjacent_or_exact_band_accuracy']}",
        f"- low_band_recall: {summary['low_band_recall']}",
        f"- critical_flag_any_match_rate: {summary['critical_flag_any_match_rate']}",
        "",
        "## Band Confusion",
    ]
    for key, count in summary["band_confusion"].items():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Calibration Rows", ""])
    lines.append("| QID | Expected | Proxy | Score | Critical flag match |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['qid']} | {row['expected_band']} | {row['proxy_band']} | "
            f"{row['score_0_10_proxy']} | {row['critical_flag_any_match']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    scored = {row["qid"]: row for row in load_csv(args.scored)}
    calibration = load_csv(args.calibration)
    rows: list[dict[str, str]] = []
    missing: list[str] = []

    for label in calibration:
        qid = label["qid"]
        scored_row = scored.get(qid)
        if not scored_row:
            missing.append(qid)
            continue
        score = float(scored_row["score_0_10_proxy"])
        expected_flags = split_flags(label.get("critical_error_flags", ""))
        actual_flags = split_flags(scored_row.get("failure_classes", ""))
        matched_flags = sorted(expected_flags & actual_flags)
        rows.append(
            {
                "qid": qid,
                "expected_band": label["expected_band"],
                "proxy_band": band_for_score(score),
                "score_0_10_proxy": f"{score:.2f}",
                "critical_error_flags_expected": "|".join(sorted(expected_flags)),
                "critical_error_flags_actual": "|".join(sorted(actual_flags)),
                "critical_flag_any_match": "True" if bool(matched_flags) or not expected_flags else "False",
                "critical_flag_matches": "|".join(matched_flags),
                "label_source": label.get("label_source", ""),
            }
        )

    if missing:
        raise SystemExit(f"Missing scored rows for calibration qids: {', '.join(missing)}")

    exact = sum(1 for row in rows if row["expected_band"] == row["proxy_band"])
    adjacent = sum(1 for row in rows if band_distance(row["expected_band"], row["proxy_band"]) <= 1)
    expected_low = [row for row in rows if row["expected_band"] == "low"]
    low_recall = (
        sum(1 for row in expected_low if row["proxy_band"] == "low") / len(expected_low)
        if expected_low
        else 0.0
    )
    critical_expected = [row for row in rows if row["critical_error_flags_expected"]]
    critical_match_rate = (
        sum(1 for row in critical_expected if row["critical_flag_any_match"] == "True") / len(critical_expected)
        if critical_expected
        else 1.0
    )
    confusion = Counter(f"{row['expected_band']}->{row['proxy_band']}" for row in rows)
    label_sources = sorted({row["label_source"] for row in rows if row.get("label_source")})
    summary = {
        "calibration_mode": "phase1_label_only_subset_no_private_answer_key",
        "label_source": ", ".join(label_sources),
        "total": len(rows),
        "exact_band_accuracy": round(exact / len(rows), 4) if rows else 0.0,
        "adjacent_or_exact_band_accuracy": round(adjacent / len(rows), 4) if rows else 0.0,
        "low_band_recall": round(low_recall, 4),
        "critical_flag_any_match_rate": round(critical_match_rate, 4),
        "band_confusion": dict(sorted(confusion.items())),
    }

    scored_path = args.out_dir / "calibration_scored.csv"
    with scored_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "qid",
            "expected_band",
            "proxy_band",
            "score_0_10_proxy",
            "critical_error_flags_expected",
            "critical_error_flags_actual",
            "critical_flag_any_match",
            "critical_flag_matches",
            "label_source",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    (args.out_dir / "calibration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_md(args.out_dir / "calibration_summary.md", summary, rows)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
