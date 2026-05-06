#!/usr/bin/env python3
"""Local guard smoke for the Phase 24HR option-C targeted smoke runner."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
RUNNER = REPO_ROOT / "scripts/benchmark/phase24hr_option_c_targeted_smoke.py"

OUT_CSV = REPORTS_DIR / "phase_24HR_option_C_targeted_smoke_guard_smoke.csv"
OUT_JSON = REPORTS_DIR / "phase_24HR_option_C_targeted_smoke_guard_smoke.json"
OUT_MD = REPORTS_DIR / "phase_24HR_option_C_targeted_smoke_guard_smoke.md"

AUTHORIZATION_TOKEN = "OPTION_C_APPROVED_PHASE24HR"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def parse_json_line(stdout: str) -> dict[str, Any]:
    text = stdout.strip().splitlines()[-1] if stdout.strip() else "{}"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"raw_stdout": stdout.strip()}
    return parsed if isinstance(parsed, dict) else {"raw_stdout": stdout.strip()}


def run_case(
    case_id: str,
    args: list[str],
    *,
    expected_returncode: int,
    expected_status: str,
    expected_error_substring: str = "",
) -> dict[str, Any]:
    command = [sys.executable, str(RUNNER), *args]
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    parsed = parse_json_line(completed.stdout)
    observed_status = str(parsed.get("status", ""))
    observed_error = str(parsed.get("error", ""))
    pass_returncode = completed.returncode == expected_returncode
    pass_status = observed_status == expected_status
    pass_error = not expected_error_substring or expected_error_substring in observed_error
    return {
        "case_id": case_id,
        "command": " ".join(command),
        "expected_returncode": expected_returncode,
        "observed_returncode": completed.returncode,
        "expected_status": expected_status,
        "observed_status": observed_status,
        "expected_error_substring": expected_error_substring,
        "observed_error": observed_error,
        "stdout_last_json": json.dumps(parsed, ensure_ascii=False, sort_keys=True),
        "stderr": completed.stderr.strip(),
        "status": "PASS" if pass_returncode and pass_status and pass_error else "FAIL",
    }


def run_cases() -> list[dict[str, Any]]:
    return [
        run_case(
            "plan_local_only",
            ["plan", "--no-write"],
            expected_returncode=0,
            expected_status="BLOCKED_WAITING_FOR_OPTION_B",
        ),
        run_case(
            "run_without_execute_refused",
            ["run-smoke"],
            expected_returncode=2,
            expected_status="REFUSED",
            expected_error_substring="--execute",
        ),
        run_case(
            "run_without_token_refused",
            ["run-smoke", "--execute"],
            expected_returncode=2,
            expected_status="REFUSED",
            expected_error_substring="authorization token",
        ),
        run_case(
            "run_live_8000_refused_before_candidate",
            ["run-smoke", "--execute", "--authorization-token", AUTHORIZATION_TOKEN, "--api-url", "http://127.0.0.1:8000/v1"],
            expected_returncode=2,
            expected_status="REFUSED",
            expected_error_substring="live 8000",
        ),
        run_case(
            "run_missing_option_b_refused_before_chat",
            ["run-smoke", "--execute", "--authorization-token", AUTHORIZATION_TOKEN],
            expected_returncode=2,
            expected_status="REFUSED",
            expected_error_substring="option-B candidate gateway is not verified",
        ),
    ]


def write_outputs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row for row in rows if row["status"] != "PASS"]
    summary = {
        "generated_at_utc": utc_now(),
        "status": "PASS" if not failed else "FAIL",
        "row_count": len(rows),
        "pass_count": len(rows) - len(failed),
        "fail_count": len(failed),
        "live_8000_modified": False,
        "candidate_gateway_started": False,
        "model_inference_called": False,
        "chat_completions_called": False,
        "safe_without_authorization": True,
        "csv": rel(OUT_CSV),
        "report_md": rel(OUT_MD),
    }
    fields = [
        "case_id",
        "status",
        "expected_returncode",
        "observed_returncode",
        "expected_status",
        "observed_status",
        "expected_error_substring",
        "observed_error",
        "stdout_last_json",
        "stderr",
        "command",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    OUT_JSON.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Phase 24HR Option C Targeted Smoke Guard Smoke",
        "",
        f"- generated_at_utc: `{summary['generated_at_utc']}`",
        f"- status: `{summary['status']}`",
        f"- row_count: `{summary['row_count']}`",
        f"- pass_count: `{summary['pass_count']}`",
        f"- fail_count: `{summary['fail_count']}`",
        "- live_8000_modified: `false`",
        "- candidate_gateway_started: `false`",
        "- model_inference_called: `false`",
        "- chat_completions_called: `false`",
        "",
        "| case | status | observed_status | observed_error |",
        "|---|---|---|---|",
    ]
    for row in rows:
        error = str(row.get("observed_error", "")).replace("|", "\\|")
        lines.append(f"| `{row['case_id']}` | `{row['status']}` | `{row['observed_status']}` | {error} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Guard smoke is safe to run without option-C authorization.",
            "- It verifies fail-closed behavior only; it does not call the candidate gateway, chat completions, or model.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    rows = run_cases()
    summary = write_outputs(rows)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
