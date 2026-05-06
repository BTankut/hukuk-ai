#!/usr/bin/env python3
"""Read-only preflight for Phase 24HR shadow validation authorization.

This script checks local artifacts only. It does not connect to Milvus, does
not start a gateway, does not call model inference, and does not modify live
8000.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
PRODUCT_DIR = REPORTS_DIR / "productization"

FULL_SPANS = REPORTS_DIR / "source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.jsonl"
CHUNKED_SPANS = REPORTS_DIR / "source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.jsonl"
CATALOG = REPORTS_DIR / "source_acquisition/phase_24HR/teb04_kdv_gut/catalog_delta/teb04_kdv_gut_catalog_delta.json"
NON_LIVE_SMOKE = REPORTS_DIR / "phase_24HR_non_live_residual_smoke.json"
SHADOW_PLAN = PRODUCT_DIR / "phase_24HR_shadow_validation_plan.md"
FINAL_GATE = PRODUCT_DIR / "final_productization_gate.md"
SOURCE_IDENTITY = REPO_ROOT / "api-gateway/src/rag/source_identity.py"

OUT_CSV = REPORTS_DIR / "phase_24HR_shadow_validation_preflight.csv"
OUT_JSON = REPORTS_DIR / "phase_24HR_shadow_validation_preflight.json"
OUT_MD = REPORTS_DIR / "phase_24HR_shadow_validation_preflight.md"

EXPECTED_RAW_SHA256 = "bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68"
EXPECTED_FULL_LOCATORS = {
    "I/C-2.1.3",
    "I/C-2.1.5",
    "I/C-2.1.5.2",
    "I/C-2.1.5.2.1",
    "I/C-2.1.5.2.2",
    "I/C-2.1.5.3",
}
EXPECTED_RUNTIME_LOCATORS = {
    "I/C-2.1.3",
    "I/C-2.1.5.2.1",
    "I/C-2.1.5.2.2",
    "I/C-2.1.5.3",
}
MAX_RUNTIME_CHUNK_CHARS = 8192


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def status_row(check_id: str, status: str, expected: str, observed: str, evidence: Path | str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "status": status,
        "expected": expected,
        "observed": observed,
        "evidence": rel(evidence) if isinstance(evidence, Path) else evidence,
    }


def duplicates(values: list[str]) -> list[str]:
    counts = Counter(value for value in values if value)
    return sorted(value for value, count in counts.items() if count > 1)


def path_checks() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in (FULL_SPANS, CHUNKED_SPANS, CATALOG, NON_LIVE_SMOKE, SHADOW_PLAN, FINAL_GATE, SOURCE_IDENTITY):
        rows.append(
            status_row(
                f"path_exists:{rel(path)}",
                "PASS" if path.exists() else "FAIL",
                "exists",
                "exists" if path.exists() else "missing",
                path,
            )
        )
    return rows


def teb_span_checks() -> list[dict[str, str]]:
    full_spans = read_jsonl(FULL_SPANS)
    chunked_spans = read_jsonl(CHUNKED_SPANS)
    full_locators = {str(span.get("section_locator", "")) for span in full_spans}
    chunked_locators = {str(span.get("section_locator", "")) for span in chunked_spans}
    all_spans = [*full_spans, *chunked_spans]
    rows = [
        status_row("teb_full_span_count", "PASS" if len(full_spans) == 6 else "FAIL", "6", str(len(full_spans)), FULL_SPANS),
        status_row(
            "teb_full_locators",
            "PASS" if EXPECTED_FULL_LOCATORS <= full_locators else "FAIL",
            "|".join(sorted(EXPECTED_FULL_LOCATORS)),
            "|".join(sorted(EXPECTED_FULL_LOCATORS & full_locators)),
            FULL_SPANS,
        ),
        status_row(
            "teb_chunked_span_count",
            "PASS" if len(chunked_spans) == 59 else "FAIL",
            "59",
            str(len(chunked_spans)),
            CHUNKED_SPANS,
        ),
        status_row(
            "teb_runtime_locator_coverage",
            "PASS"
            if all(
                locator in full_locators or any(chunked.startswith(f"{locator}.") for chunked in chunked_locators)
                for locator in EXPECTED_RUNTIME_LOCATORS
            )
            else "FAIL",
            "|".join(sorted(EXPECTED_RUNTIME_LOCATORS)),
            "|".join(
                sorted(
                    locator
                    for locator in EXPECTED_RUNTIME_LOCATORS
                    if locator in full_locators or any(chunked.startswith(f"{locator}.") for chunked in chunked_locators)
                )
            ),
            CHUNKED_SPANS,
        ),
    ]

    max_chunk = max((int(span.get("body_text_length") or 0) for span in chunked_spans), default=0)
    rows.append(
        status_row(
            "teb_max_chunk_size",
            "PASS" if max_chunk <= MAX_RUNTIME_CHUNK_CHARS else "FAIL",
            f"<= {MAX_RUNTIME_CHUNK_CHARS}",
            str(max_chunk),
            CHUNKED_SPANS,
        )
    )
    raw_sha_values = {str(span.get("raw_sha256", "")) for span in all_spans}
    rows.append(
        status_row(
            "teb_raw_sha256_consistent",
            "PASS" if raw_sha_values == {EXPECTED_RAW_SHA256} else "FAIL",
            EXPECTED_RAW_SHA256,
            "|".join(sorted(raw_sha_values)),
            CHUNKED_SPANS,
        )
    )
    source_identifiers = {str(span.get("source_identifier", "")) for span in all_spans}
    rows.append(
        status_row(
            "teb_source_identifier_consistent",
            "PASS" if source_identifiers == {"19631"} else "FAIL",
            "19631",
            "|".join(sorted(source_identifiers)),
            CHUNKED_SPANS,
        )
    )
    for key in ("canonical_source_key_v2", "binding_source_key"):
        duplicate_values = duplicates([str(span.get(key, "")) for span in all_spans])
        rows.append(
            status_row(
                f"teb_no_duplicate_{key}",
                "PASS" if not duplicate_values else "FAIL",
                "no duplicates",
                "|".join(duplicate_values[:5]) if duplicate_values else "none",
                CHUNKED_SPANS,
            )
        )
    return rows


def smoke_and_gate_checks() -> list[dict[str, str]]:
    smoke = json.loads(NON_LIVE_SMOKE.read_text(encoding="utf-8"))
    summary = smoke.get("summary", {})
    final_gate_text = FINAL_GATE.read_text(encoding="utf-8")
    source_identity_text = SOURCE_IDENTITY.read_text(encoding="utf-8")
    return [
        status_row(
            "non_live_smoke_pass",
            "PASS" if summary.get("status") == "PASS" and summary.get("fail_count") == 0 else "FAIL",
            "PASS fail_count=0",
            f"{summary.get('status')} fail_count={summary.get('fail_count')}",
            NON_LIVE_SMOKE,
        ),
        status_row(
            "non_live_smoke_no_side_effects",
            "PASS"
            if summary.get("live_8000_modified") is False
            and summary.get("milvus_modified") is False
            and summary.get("model_inference_called") is False
            else "FAIL",
            "live=false milvus=false model=false",
            f"live={summary.get('live_8000_modified')} milvus={summary.get('milvus_modified')} model={summary.get('model_inference_called')}",
            NON_LIVE_SMOKE,
        ),
        status_row(
            "productization_gate_still_closed",
            "PASS" if "not_productization_ready" in final_gate_text else "FAIL",
            "not_productization_ready",
            "not_productization_ready" if "not_productization_ready" in final_gate_text else "missing",
            FINAL_GATE,
        ),
        status_row(
            "no_qid_specific_source_identity_branch",
            "PASS" if "TEB-04" not in source_identity_text and "TUZUK-05" not in source_identity_text else "FAIL",
            "no TEB-04/TUZUK-05 literals",
            "clean" if "TEB-04" not in source_identity_text and "TUZUK-05" not in source_identity_text else "qid literal present",
            SOURCE_IDENTITY,
        ),
    ]


def authorization_checks() -> list[dict[str, str]]:
    plan_text = SHADOW_PLAN.read_text(encoding="utf-8")
    required_phrases = [
        "Building or loading a Milvus shadow collection",
        "Starting a candidate gateway",
        "Running a full trace-on candidate benchmark",
        "Any switch, cutover, internal eval opening, serving candidate opening, or productization decision",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in plan_text]
    return [
        status_row(
            "authorization_requirements_present",
            "PASS" if not missing else "FAIL",
            "all explicit authorization requirements",
            "none missing" if not missing else "|".join(missing),
            SHADOW_PLAN,
        )
    ]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["check_id", "status", "expected", "observed", "evidence"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(rows: list[dict[str, str]]) -> dict[str, Any]:
    fail_rows = [row for row in rows if row["status"] == "FAIL"]
    summary = {
        "generated_at_utc": utc_now(),
        "status": "PASS" if not fail_rows else "FAIL",
        "row_count": len(rows),
        "pass_count": len(rows) - len(fail_rows),
        "fail_count": len(fail_rows),
        "csv": rel(OUT_CSV),
        "live_8000_modified": False,
        "milvus_modified": False,
        "candidate_gateway_started": False,
        "model_inference_called": False,
        "ready_for_authorization_request": not fail_rows,
    }
    write_csv(OUT_CSV, rows)
    OUT_JSON.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Phase 24HR Shadow Validation Preflight",
        "",
        f"- generated_at_utc: `{summary['generated_at_utc']}`",
        f"- status: `{summary['status']}`",
        f"- row_count: `{summary['row_count']}`",
        f"- pass_count: `{summary['pass_count']}`",
        f"- fail_count: `{summary['fail_count']}`",
        "- live_8000_modified: `false`",
        "- milvus_modified: `false`",
        "- candidate_gateway_started: `false`",
        "- model_inference_called: `false`",
        "",
        "| check | status | expected | observed |",
        "|---|---|---|---|",
    ]
    for row in rows:
        expected = row["expected"].replace("|", "\\|")
        observed = row["observed"].replace("|", "\\|")
        lines.append(f"| `{row['check_id']}` | `{row['status']}` | {expected} | {observed} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Local preflight is sufficient to request owner authorization for the next gated shadow validation step.",
            "- This is not product readiness and not a serving/productization approval.",
            "- Base collection collision checks, shadow collection build, candidate gateway, and full trace-on benchmark are intentionally not executed here.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    rows = path_checks()
    rows.extend(teb_span_checks())
    rows.extend(smoke_and_gate_checks())
    rows.extend(authorization_checks())
    summary = write_outputs(rows)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
