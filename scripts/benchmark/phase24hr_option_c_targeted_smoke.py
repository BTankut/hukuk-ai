#!/usr/bin/env python3
"""Fail-closed Phase 24HR option-C targeted smoke runner.

The default `plan` command is local-only. `run-smoke` can call the candidate
gateway and model, so it refuses unless option B has produced a candidate
gateway start report and both `--execute` and the explicit option-C
authorization token are provided.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
PRODUCT_DIR = REPORTS_DIR / "productization"

AUTHORIZATION_TOKEN = "OPTION_C_APPROVED_PHASE24HR"
OPTION_B_START_REPORT = REPORTS_DIR / "phase_24HR_option_B_candidate_gateway_start_report.json"
OPTION_C_PLAN = PRODUCT_DIR / "phase_24HR_option_C_targeted_smoke_plan.md"
OUT_PLAN_JSON = REPORTS_DIR / "phase_24HR_option_C_targeted_smoke_runner_plan.json"
OUT_PLAN_MD = REPORTS_DIR / "phase_24HR_option_C_targeted_smoke_runner_plan.md"
OUT_RUN_DIR = REPORTS_DIR / "runs/phase_24HR_option_C_targeted_candidate_smoke"
OUT_RUN_REPORT_JSON = REPORTS_DIR / "phase_24HR_option_C_targeted_smoke_run_report.json"

DEFAULT_API_URL = "http://127.0.0.1:8010/v1"
DEFAULT_MODEL = "hukuk-ai-poc"
TARGET_QIDS = ["TEB-04", "TUZUK-05", "KANUN-08", "YON-05"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def api_port(api_url: str) -> int | None:
    parsed = urllib.parse.urlparse(api_url)
    return parsed.port


def api_root(api_url: str) -> str:
    return api_url.rstrip("/").removesuffix("/v1")


def api_health_url(api_url: str) -> str:
    return f"{api_url.rstrip('/')}/health"


def http_json(url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"HTTP health check failed for {url}: {exc}") from exc
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Health endpoint did not return a JSON object: {url}")
    return parsed


def option_b_status() -> dict[str, Any]:
    if not OPTION_B_START_REPORT.exists():
        return {
            "status": "MISSING",
            "reason": "Option-B candidate gateway start report is missing.",
            "report": rel(OPTION_B_START_REPORT),
        }
    report = read_json(OPTION_B_START_REPORT)
    candidate_health = report.get("candidate_health") if isinstance(report.get("candidate_health"), dict) else {}
    live_health = report.get("live_health") if isinstance(report.get("live_health"), dict) else {}
    problems: list[str] = []
    if report.get("status") != "STARTED":
        problems.append(f"start_status={report.get('status')}")
    if report.get("candidate_gateway_started") is not True:
        problems.append("candidate_gateway_started_not_true")
    if candidate_health.get("status") != "ok":
        problems.append(f"candidate_health={candidate_health.get('status')}")
    if report.get("port") == 8000:
        problems.append("candidate_port_is_live_8000")
    if report.get("live_8000_modified") is not False:
        problems.append("live_8000_modified_not_false")
    if not live_health:
        problems.append("live_health_missing")
    return {
        "status": "PASS" if not problems else "FAIL",
        "problems": problems,
        "report": rel(OPTION_B_START_REPORT),
        "candidate_health": candidate_health,
        "live_health": live_health,
        "candidate_port": report.get("port"),
    }


def plan_payload(args: argparse.Namespace) -> dict[str, Any]:
    b_status = option_b_status()
    status = "READY_FOR_OPTION_C_AUTHORIZATION" if b_status["status"] == "PASS" else "BLOCKED_WAITING_FOR_OPTION_B"
    return {
        "generated_at_utc": utc_now(),
        "status": status,
        "authorization_token_required": AUTHORIZATION_TOKEN,
        "execute_required": True,
        "api_url": args.api_url,
        "model": args.model,
        "target_qids": TARGET_QIDS,
        "out_dir": rel(args.out_dir),
        "option_b_status": b_status,
        "live_8000_modified": False,
        "candidate_gateway_started": False,
        "model_inference_called": False,
        "chat_completions_called": False,
    }


def write_plan(args: argparse.Namespace) -> dict[str, Any]:
    payload = plan_payload(args)
    lines = [
        "# Phase 24HR Option C Targeted Smoke Runner Plan",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- status: `{payload['status']}`",
        f"- api_url: `{payload['api_url']}`",
        f"- model: `{payload['model']}`",
        f"- target_qids: `{' '.join(TARGET_QIDS)}`",
        f"- option_b_status: `{payload['option_b_status']['status']}`",
        "- live_8000_modified: `false`",
        "- candidate_gateway_started: `false`",
        "- model_inference_called: `false`",
        "- chat_completions_called: `false`",
        "",
        "## Guarded Run Command",
        "",
        "```bash",
        "python3 scripts/benchmark/phase24hr_option_c_targeted_smoke.py run-smoke \\",
        f"  --execute --authorization-token {AUTHORIZATION_TOKEN}",
        "```",
        "",
        "## Safety Notes",
        "",
        "- Without option-B candidate health evidence, the runner remains blocked.",
        "- Without `--execute`, the runner refuses to call the candidate gateway.",
        f"- Without `--authorization-token {AUTHORIZATION_TOKEN}`, the runner refuses to call the candidate gateway.",
        "- API URL using live `8000` is refused.",
    ]
    if not args.no_write:
        OUT_PLAN_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        OUT_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def ensure_run_authorized(args: argparse.Namespace) -> None:
    if not args.execute:
        raise RuntimeError("Refusing targeted smoke: pass --execute only after owner option-C authorization.")
    if args.authorization_token != AUTHORIZATION_TOKEN:
        raise RuntimeError("Refusing targeted smoke: missing or invalid option-C authorization token.")
    if api_port(args.api_url) == 8000:
        raise RuntimeError("Refusing targeted smoke: live 8000 must not be used.")
    b_status = option_b_status()
    if b_status["status"] != "PASS":
        raise RuntimeError("Refusing targeted smoke: option-B candidate gateway is not verified.")
    if api_port(args.api_url) != b_status.get("candidate_port"):
        raise RuntimeError("Refusing targeted smoke: api-url port does not match the option-B candidate port.")
    health = http_json(api_health_url(args.api_url))
    if health.get("status") != "ok":
        raise RuntimeError("Refusing targeted smoke: candidate health is not ok.")


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    ensure_run_authorized(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    run_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/benchmark/run_hukuk_ai_100.py"),
        "--api-url",
        args.api_url,
        "--model",
        args.model,
        "--out-dir",
        str(args.out_dir),
        "--qids",
        *TARGET_QIDS,
    ]
    run_completed = subprocess.run(run_cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    score_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/benchmark/score_hukuk_ai_100.py"),
        "--answers",
        str(args.out_dir / "candidate_answers.csv"),
        "--out-dir",
        str(args.out_dir / "score"),
    ]
    score_completed = subprocess.run(score_cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    score_summary_path = args.out_dir / "score/score_summary.json"
    score_summary: dict[str, Any] = {}
    if score_summary_path.exists():
        score_summary = read_json(score_summary_path)
    hard_counter_keys = [
        "answer_contract_invalid_count",
        "unsupported_confident_answer_count",
        "source_key_v2_collision_detected_count",
        "binding_source_key_collision_detected_count",
    ]
    quality_gate_pass = (
        run_completed.returncode == 0
        and score_completed.returncode == 0
        and score_summary.get("pass_proxy") == len(TARGET_QIDS)
        and all(score_summary.get(key) == 0 for key in hard_counter_keys)
    )
    report = {
        "generated_at_utc": utc_now(),
        "status": "PASS" if run_completed.returncode == 0 and score_completed.returncode == 0 else "FAIL",
        "quality_gate_status": "PASS" if quality_gate_pass else "FAIL",
        "api_url": args.api_url,
        "model": args.model,
        "target_qids": TARGET_QIDS,
        "out_dir": rel(args.out_dir),
        "run_returncode": run_completed.returncode,
        "score_returncode": score_completed.returncode,
        "score_summary": {
            key: score_summary.get(key)
            for key in [
                "total",
                "raw_score_proxy",
                "max_score",
                "pass_proxy",
                "fail_proxy",
                *hard_counter_keys,
                "repealed_as_active_count",
                "temporal_validity_miss_count",
                "hallucinated_source_count",
                "manual_review_count",
            ]
            if key in score_summary
        },
        "live_8000_modified": False,
        "candidate_gateway_started": False,
        "model_inference_called": True,
        "chat_completions_called": True,
    }
    OUT_RUN_REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return report


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out-dir", type=Path, default=OUT_RUN_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan")
    add_common_args(plan)
    plan.add_argument("--no-write", action="store_true")
    plan.set_defaults(func=lambda args: (write_plan(args), 0)[1])

    run = subparsers.add_parser("run-smoke")
    add_common_args(run)
    run.add_argument("--execute", action="store_true")
    run.add_argument("--authorization-token", default="")
    run.set_defaults(func=lambda args: (run_smoke(args), 0)[1])

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return int(args.func(args))
    except RuntimeError as exc:
        print(json.dumps({"status": "REFUSED", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
