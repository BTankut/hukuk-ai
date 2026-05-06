#!/usr/bin/env python3
"""Fail-closed Phase 24HR option-B candidate gateway runner.

The default `plan` command is local-only. `start-candidate` can start a
non-live gateway, so it refuses unless both `--execute` and the explicit
option-B authorization token are provided. The runner never changes live 8000,
Open WebUI, internal eval, serving candidate, productization, model path,
prompt, top-k, or fine-tuning state.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase24hr_shadow_build_dry_run import (
    EMBEDDING_MODEL,
    REPORTS_DIR,
    TARGET_COLLECTION,
    VECTOR_DIMENSION,
    rel,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_DIR = REPORTS_DIR / "productization"
AUTHORIZATION_TOKEN = "OPTION_B_APPROVED_PHASE24HR"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8010
LIVE_PORT = 8000
DEFAULT_LANE = "phase24hr_option_b_candidate"
DEFAULT_API_VERSION = "2026-05-06-phase24hr-option-b-candidate"
DEFAULT_LOG = REPO_ROOT / "runtime_logs/phase24hr/option_b_candidate_gateway.log"
DEFAULT_PID = REPO_ROOT / "runtime_logs/phase24hr/option_b_candidate_gateway.pid"
DEFAULT_TRACE_DIR = REPO_ROOT / "logs/traces/phase24hr_option_b_candidate"
DEFAULT_MILVUS_URI = "http://localhost:19530"
DEFAULT_EMBEDDING_BASE_URL = "http://127.0.0.1:8081/v1"
DEFAULT_DGX_BASE_URL = "http://192.168.12.243:30000/v1"
DEFAULT_DGX_MODEL = "/models/merged_model_fabric_stage_20260321"

PREFLIGHT = REPORTS_DIR / "phase_24HR_shadow_validation_preflight.json"
VERIFY = REPORTS_DIR / "phase_24HR_shadow_collection_verify.json"
BUILD_REPORT = REPORTS_DIR / "phase_24HR_shadow_collection_build_report.md"
OPTION_B_PLAN = PRODUCT_DIR / "phase_24HR_option_B_candidate_gateway_plan.md"
OUT_PLAN_JSON = REPORTS_DIR / "phase_24HR_option_B_candidate_gateway_runner_plan.json"
OUT_PLAN_MD = REPORTS_DIR / "phase_24HR_option_B_candidate_gateway_runner_plan.md"
OUT_START_JSON = REPORTS_DIR / "phase_24HR_option_B_candidate_gateway_start_report.json"
OUT_START_MD = REPORTS_DIR / "phase_24HR_option_B_candidate_gateway_start_report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_rel(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path)


def pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def port_is_listening(host: str, port: int, *, timeout: float = 0.2) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


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


def verify_prerequisites() -> dict[str, Any]:
    missing = [path for path in [PREFLIGHT, VERIFY, BUILD_REPORT, OPTION_B_PLAN] if not path.exists()]
    if missing:
        raise RuntimeError("Missing option-B prerequisite artifacts: " + ", ".join(rel(path) for path in missing))

    preflight = read_json(PREFLIGHT).get("summary", {})
    verify = read_json(VERIFY).get("summary", {})
    failures: list[str] = []
    if preflight.get("status") != "PASS" or preflight.get("fail_count") != 0:
        failures.append(f"preflight={preflight.get('status')} fail_count={preflight.get('fail_count')}")
    if verify.get("status") != "PASS" or verify.get("target_delta_rows_found") != 59:
        failures.append(
            f"verify={verify.get('status')} target_delta_rows_found={verify.get('target_delta_rows_found')}"
        )
    if verify.get("base_delta_id_collision_count") != 0:
        failures.append(f"base_delta_id_collision_count={verify.get('base_delta_id_collision_count')}")
    if failures:
        raise RuntimeError("Option-B prerequisites are not satisfied: " + "; ".join(failures))
    return {
        "preflight_status": preflight.get("status"),
        "preflight_pass_count": preflight.get("pass_count"),
        "verify_status": verify.get("status"),
        "target_delta_rows_found": verify.get("target_delta_rows_found"),
        "base_delta_id_collision_count": verify.get("base_delta_id_collision_count"),
    }


def candidate_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(REPO_ROOT / "api-gateway/src"),
            "RELEASE_LANE_ID": args.lane,
            "API_VERSION_LABEL": args.api_version,
            "MILVUS_ENABLED": "true",
            "MILVUS_URI": args.milvus_uri,
            "MILVUS_COLLECTION": args.collection,
            "EMBEDDING_BACKEND": "remote",
            "EMBEDDING_BASE_URL": args.embedding_base_url,
            "EMBEDDING_MODEL": args.embedding_model,
            "EMBEDDING_DIM": str(args.embedding_dim),
            "DGX_BASE_URL": args.dgx_base_url,
            "DGX_MODEL": args.dgx_model,
            "GUARDRAILS_ENABLED": "false",
            "PRESIDIO_ENABLED": "false",
            "USE_VERIFICATION": "false",
            "API_AUTH_ENABLED": "false",
            "AUDIT_LOG_ENABLED": "false",
            "TRACE_LOG_DIR": str(args.trace_dir),
        }
    )
    return env


def plan_payload(args: argparse.Namespace) -> dict[str, Any]:
    prereq = verify_prerequisites()
    return {
        "generated_at_utc": utc_now(),
        "status": "READY_FOR_OPTION_B_AUTHORIZATION",
        "authorization_token_required": AUTHORIZATION_TOKEN,
        "execute_required": True,
        "host": args.host,
        "port": args.port,
        "lane": args.lane,
        "api_version": args.api_version,
        "collection": args.collection,
        "milvus_uri": args.milvus_uri,
        "embedding_base_url": args.embedding_base_url,
        "embedding_model": args.embedding_model,
        "embedding_dim": args.embedding_dim,
        "dgx_base_url": args.dgx_base_url,
        "dgx_model": args.dgx_model,
        "pid_file": safe_rel(args.pid_file),
        "log_file": safe_rel(args.log_file),
        "trace_dir": safe_rel(args.trace_dir),
        "live_8000_modified": False,
        "candidate_gateway_started": False,
        "model_inference_called": False,
        "chat_completions_called": False,
        "prerequisites": prereq,
    }


def write_plan(args: argparse.Namespace) -> dict[str, Any]:
    payload = plan_payload(args)
    lines = [
        "# Phase 24HR Option B Candidate Gateway Runner Plan",
        "",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        f"- status: `{payload['status']}`",
        f"- host: `{payload['host']}`",
        f"- port: `{payload['port']}`",
        f"- lane: `{payload['lane']}`",
        f"- collection: `{payload['collection']}`",
        f"- authorization_token_required: `{payload['authorization_token_required']}`",
        "- live_8000_modified: `false`",
        "- candidate_gateway_started: `false`",
        "- model_inference_called: `false`",
        "- chat_completions_called: `false`",
        "",
        "## Guarded Start Command",
        "",
        "```bash",
        "python3 scripts/benchmark/phase24hr_option_b_candidate_gateway.py start-candidate \\",
        f"  --execute --authorization-token {AUTHORIZATION_TOKEN}",
        "```",
        "",
        "## Safety Notes",
        "",
        "- Without `--execute`, the runner refuses to start a process.",
        f"- Without `--authorization-token {AUTHORIZATION_TOKEN}`, the runner refuses to start a process.",
        "- The candidate host must be loopback only.",
        "- Port `8000` is refused.",
        "- The runner calls health endpoints only after an authorized start; it does not call chat completions.",
    ]
    if not getattr(args, "no_write", False):
        OUT_PLAN_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        OUT_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def ensure_start_authorized(args: argparse.Namespace) -> None:
    if not args.execute:
        raise RuntimeError("Refusing candidate gateway start: pass --execute only after owner option-B authorization.")
    if args.authorization_token != AUTHORIZATION_TOKEN:
        raise RuntimeError("Refusing candidate gateway start: missing or invalid option-B authorization token.")
    if args.host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Refusing candidate gateway start: host must be loopback only.")
    if args.port == LIVE_PORT:
        raise RuntimeError("Refusing candidate gateway start: live 8000 must not be reused.")
    if args.port < 1 or args.port > 65535:
        raise RuntimeError("Refusing candidate gateway start: port is outside the valid TCP range.")
    verify_prerequisites()
    if args.pid_file.exists():
        try:
            pid = int(args.pid_file.read_text(encoding="utf-8").strip())
        except ValueError:
            raise RuntimeError(f"Refusing candidate gateway start: invalid pid file {rel(args.pid_file)}.")
        if pid_is_running(pid):
            raise RuntimeError(f"Refusing candidate gateway start: pid file already points to running process {pid}.")
    if port_is_listening(args.host, args.port):
        raise RuntimeError(f"Refusing candidate gateway start: port {args.port} is already listening on {args.host}.")


def start_candidate(args: argparse.Namespace) -> dict[str, Any]:
    ensure_start_authorized(args)
    args.log_file.parent.mkdir(parents=True, exist_ok=True)
    args.pid_file.parent.mkdir(parents=True, exist_ok=True)
    args.trace_dir.mkdir(parents=True, exist_ok=True)
    command = [
        str(REPO_ROOT / "api-gateway/.venv/bin/uvicorn"),
        "main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    log_handle = args.log_file.open("ab")
    proc = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env=candidate_env(args),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    args.pid_file.write_text(f"{proc.pid}\n", encoding="utf-8")
    time.sleep(args.startup_wait_seconds)
    candidate_health = http_json(f"http://{args.host}:{args.port}/v1/health")
    live_health = http_json(f"http://127.0.0.1:{LIVE_PORT}/v1/health")
    report = {
        "generated_at_utc": utc_now(),
        "status": "STARTED",
        "pid": proc.pid,
        "host": args.host,
        "port": args.port,
        "lane": args.lane,
        "collection": args.collection,
        "pid_file": safe_rel(args.pid_file),
        "log_file": safe_rel(args.log_file),
        "candidate_health": candidate_health,
        "live_health": live_health,
        "live_8000_modified": False,
        "candidate_gateway_started": True,
        "model_inference_called": False,
        "chat_completions_called": False,
    }
    OUT_START_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_START_MD.write_text(
        "\n".join(
            [
                "# Phase 24HR Option B Candidate Gateway Start Report",
                "",
                f"- generated_at_utc: `{report['generated_at_utc']}`",
                f"- status: `{report['status']}`",
                f"- pid: `{report['pid']}`",
                f"- host: `{report['host']}`",
                f"- port: `{report['port']}`",
                f"- lane: `{report['lane']}`",
                f"- collection: `{report['collection']}`",
                "- live_8000_modified: `false`",
                "- model_inference_called: `false`",
                "- chat_completions_called: `false`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return report


def stop_candidate(args: argparse.Namespace) -> dict[str, Any]:
    if not args.pid_file.exists():
        report = {"status": "NOT_RUNNING", "pid_file": safe_rel(args.pid_file), "candidate_gateway_stopped": False}
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return report
    pid = int(args.pid_file.read_text(encoding="utf-8").strip())
    if pid_is_running(pid):
        os.kill(pid, signal.SIGTERM)
        time.sleep(args.stop_wait_seconds)
    stopped = not pid_is_running(pid)
    if stopped:
        args.pid_file.unlink(missing_ok=True)
    report = {
        "status": "STOPPED" if stopped else "STILL_RUNNING",
        "pid": pid,
        "pid_file": safe_rel(args.pid_file),
        "candidate_gateway_stopped": stopped,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return report


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--lane", default=DEFAULT_LANE)
    parser.add_argument("--api-version", default=DEFAULT_API_VERSION)
    parser.add_argument("--collection", default=TARGET_COLLECTION)
    parser.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", DEFAULT_MILVUS_URI))
    parser.add_argument("--embedding-base-url", default=os.getenv("EMBEDDING_BASE_URL", DEFAULT_EMBEDDING_BASE_URL))
    parser.add_argument("--embedding-model", default=os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL))
    parser.add_argument("--embedding-dim", type=int, default=VECTOR_DIMENSION)
    parser.add_argument("--dgx-base-url", default=os.getenv("DGX_BASE_URL", DEFAULT_DGX_BASE_URL))
    parser.add_argument("--dgx-model", default=os.getenv("DGX_MODEL", DEFAULT_DGX_MODEL))
    parser.add_argument("--pid-file", type=Path, default=DEFAULT_PID)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--trace-dir", type=Path, default=DEFAULT_TRACE_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan")
    add_common_args(plan)
    plan.add_argument("--no-write", action="store_true")
    plan.set_defaults(func=lambda args: (write_plan(args), 0)[1])

    start = subparsers.add_parser("start-candidate")
    add_common_args(start)
    start.add_argument("--execute", action="store_true")
    start.add_argument("--authorization-token", default="")
    start.add_argument("--startup-wait-seconds", type=float, default=3.0)
    start.set_defaults(func=lambda args: (start_candidate(args), 0)[1])

    stop = subparsers.add_parser("stop-candidate")
    add_common_args(stop)
    stop.add_argument("--stop-wait-seconds", type=float, default=3.0)
    stop.set_defaults(func=lambda args: (stop_candidate(args), 0)[1])

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
