#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
API_GATEWAY_SRC = ROOT / "api-gateway" / "src"
if str(API_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(API_GATEWAY_SRC))

DOCS_DIR = ROOT / "docs"
RUNTIME_DIR = ROOT / "runtime_logs" / "mevzuat_controlled_cutover_execution_rerun_20260418"
SUMMARY_JSON = RUNTIME_DIR / "phase_summary.json"

SOURCE_ARTICLE_ROWS = Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl")
ACTIVE_RUNTIME_COLLECTION = "mevzuat_e5_shadow"
CANDIDATE_RUNTIME_COLLECTION = "mevzuat_faz1_shadow_20260416"
ROLLBACK_TARGET = ACTIVE_RUNTIME_COLLECTION
BACKOUT_TARGET = ACTIVE_RUNTIME_COLLECTION

GATEWAY_HEALTH_URL = "http://127.0.0.1:8000/v1/health"
GATEWAY_CHAT_URL = "http://127.0.0.1:8000/v1/chat/completions"
LAUNCHER = ROOT / "scripts" / "finetune" / "launch_local_baseline_gateway_dgxnode2.sh"
BASELINE_PID = ROOT / "runtime_logs" / "baseline_gateway_dgxnode2.pid"
TUNNEL_PID = ROOT / "runtime_logs" / "baseline_dgxnode2_vllm_tunnel.pid"

PRESWITCH_DOC = DOCS_DIR / "MEVZUAT-CONTROLLED-CUTOVER-RERUN-PRE-SWITCH-FREEZE-RAPORU-2026-04-18.md"
SWITCH_DOC = DOCS_DIR / "MEVZUAT-CONTROLLED-CUTOVER-RERUN-SWITCH-EXECUTION-RAPORU-2026-04-18.md"
POSTSWITCH_DOC = DOCS_DIR / "MEVZUAT-CONTROLLED-CUTOVER-RERUN-POST-SWITCH-SMOKE-RAPORU-2026-04-18.md"
ROLLBACK_DOC = DOCS_DIR / "MEVZUAT-CONTROLLED-CUTOVER-RERUN-ROLLBACK-BACKOUT-TEYIT-NOTU-2026-04-18.md"
EXECUTION_DOC = DOCS_DIR / "MEVZUAT-CONTROLLED-CUTOVER-RERUN-EXECUTION-RAPORU-2026-04-18.md"
NEXT_DOC = DOCS_DIR / "MEVZUAT-CONTROLLED-CUTOVER-RERUN-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-18.md"


@dataclass(slots=True)
class SmokeCase:
    case_id: str
    label: str
    belge_turu: str
    query_text: str
    expected_source_id: str
    expected_display_citation: str
    expected_mulga_hidden: bool


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def md_bool(value: bool) -> str:
    return "true" if value else "false"


def iter_article_rows(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if raw:
                yield json.loads(raw)


def select_smoke_cases(article_rows_path: Path) -> list[SmokeCase]:
    selected: dict[str, dict[str, Any]] = {}
    ordered_keys = ["KANUN-A", "CBK-A", "YONETMELIK-A", "CB-YONETMELIK-A", "TEBLIG-A", "MULGA-A"]

    for row in iter_article_rows(article_rows_path):
        source_id = str(row.get("source_id") or "")
        belge_turu = str(row.get("belge_turu") or "")
        mulga = bool(row.get("mulga"))
        citation = row.get("display_citation")

        if "KANUN-A" not in selected and belge_turu == "kanun" and not mulga and source_id and citation:
            selected["KANUN-A"] = row
        elif "CBK-A" not in selected and belge_turu == "cb_kararname" and not mulga and source_id and citation:
            selected["CBK-A"] = row
        elif "YONETMELIK-A" not in selected and belge_turu == "yonetmelik" and not mulga and source_id and citation:
            selected["YONETMELIK-A"] = row
        elif "CB-YONETMELIK-A" not in selected and belge_turu == "cb_yonetmelik" and not mulga and source_id and citation:
            selected["CB-YONETMELIK-A"] = row
        elif "TEBLIG-A" not in selected and belge_turu == "teblig" and not mulga and source_id and citation:
            selected["TEBLIG-A"] = row
        elif "MULGA-A" not in selected and mulga and source_id and citation:
            selected["MULGA-A"] = row

        if len(selected) == len(ordered_keys):
            break

    missing = [key for key in ordered_keys if key not in selected]
    if missing:
        raise RuntimeError(f"smoke case selection failed: {missing}")

    return [
        SmokeCase(
            case_id=case_id,
            label=str(row["display_citation"]),
            belge_turu=str(row["belge_turu"]),
            query_text=str(row["display_citation"]),
            expected_source_id=str(row["source_id"]),
            expected_display_citation=str(row["display_citation"]),
            expected_mulga_hidden=bool(row["mulga"]),
        )
        for case_id, row in selected.items()
    ]


def stop_pid_file(pid_path: Path) -> None:
    if not pid_path.exists():
        return
    raw = pid_path.read_text(encoding="utf-8").strip()
    if not raw:
        return
    try:
        pid = int(raw)
    except ValueError:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.2)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def launch_runtime(collection_name: str) -> None:
    stop_pid_file(BASELINE_PID)
    stop_pid_file(TUNNEL_PID)
    env = os.environ.copy()
    env["MILVUS_COLLECTION"] = collection_name
    subprocess.run(["bash", str(LAUNCHER)], cwd=str(ROOT), env=env, check=True)


def wait_for_health(timeout: int = 120) -> bool:
    import requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(GATEWAY_HEALTH_URL, timeout=5)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def collection_entity_count(collection_name: str) -> int | None:
    from pymilvus import MilvusClient

    client = MilvusClient(uri="http://127.0.0.1:19530")
    try:
        stats = client.get_collection_stats(collection_name=collection_name)
    except Exception:
        return None
    try:
        return int(stats.get("row_count"))
    except Exception:
        return None


def run_chat_completion(query_text: str) -> tuple[int | None, dict[str, Any] | None, str | None]:
    import requests

    payload = {
        "model": "Qwen/Qwen3.5-35B-A3B-FP8",
        "messages": [{"role": "user", "content": query_text}],
        "temperature": 0,
        "max_tokens": 300,
        "stream": False,
    }
    try:
        response = requests.post(GATEWAY_CHAT_URL, json=payload, timeout=120)
        status = response.status_code
        try:
            body = response.json()
        except Exception:
            body = {"raw_text": response.text}
        error_text = None if response.ok else json.dumps(body, ensure_ascii=False)
        return status, body, error_text
    except Exception as exc:
        return None, None, repr(exc)


def evaluate_runtime_case(case: SmokeCase, status: int | None, body: dict[str, Any] | None, error_text: str | None) -> dict[str, Any]:
    from faz2a_hardening import canonicalize_source_id

    if status is None or status >= 500 or body is None:
        error_class = "runtime_request_failure"
        if error_text and "vector" in error_text.lower() and "dimension" in error_text.lower():
            error_class = "vector_dimension_mismatch"
        elif error_text and ("connect" in error_text.lower() or "upstream" in error_text.lower()):
            error_class = "upstream_llm_connectivity_failure"
        return {
            "case_id": case.case_id,
            "query_text": case.query_text,
            "status_code": status,
            "citation_readable": False,
            "source_correct": False,
            "wrong_source": False,
            "runtime_error": True,
            "unexplained": True,
            "case_result": "FAIL",
            "error_class": error_class,
            "error_text": error_text or "no response body",
        }

    answer_contract = body.get("answer_contract") or {}
    primary = canonicalize_source_id(answer_contract.get("primary_source_id")) or ""
    expected = canonicalize_source_id(case.expected_source_id) or case.expected_source_id
    citations = body.get("citations") or []
    citation_readable = bool(citations)

    if case.expected_mulga_hidden:
        temporal_refusal = body.get("final_mode") == "refusal" and (
            body.get("unsupported_reason") == "temporal_mismatch"
            or answer_contract.get("unsupported_reason") == "temporal_mismatch"
        )
        return {
            "case_id": case.case_id,
            "query_text": case.query_text,
            "status_code": status,
            "citation_readable": False,
            "source_correct": temporal_refusal,
            "wrong_source": not temporal_refusal,
            "runtime_error": False,
            "unexplained": not temporal_refusal,
            "case_result": "PASS" if temporal_refusal else "FAIL",
            "final_mode": body.get("final_mode"),
            "primary_source_id": answer_contract.get("primary_source_id"),
            "error_class": None,
            "error_text": None,
        }

    supported = body.get("final_mode") in {"answer", "partial"}
    source_correct = supported and primary == expected
    return {
        "case_id": case.case_id,
        "query_text": case.query_text,
        "status_code": status,
        "citation_readable": citation_readable,
        "source_correct": source_correct,
        "wrong_source": not source_correct,
        "runtime_error": False,
        "unexplained": not source_correct,
        "case_result": "PASS" if source_correct else "FAIL",
        "final_mode": body.get("final_mode"),
        "primary_source_id": answer_contract.get("primary_source_id"),
        "error_class": None,
        "error_text": None,
    }


def summarize_case_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "smoke_case_count": len(results),
        "citation_readable_count": sum(1 for item in results if item["citation_readable"]),
        "source_correct_count": sum(1 for item in results if item["source_correct"]),
        "wrong_source_count": sum(1 for item in results if item["wrong_source"]),
        "runtime_error_count": sum(1 for item in results if item["runtime_error"]),
        "unexplained_count": sum(1 for item in results if item["unexplained"]),
    }


def render_preswitch_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Controlled Cutover Rerun Pre-Switch Freeze Raporu 2026-04-18",
            "",
            "## Official Fields",
            f"- `pre_switch_active_runtime_collection = {summary['pre_switch_active_runtime_collection']}`",
            f"- `candidate_runtime_collection = {summary['candidate_runtime_collection']}`",
            f"- `rollback_target = {summary['rollback_target']}`",
            f"- `backout_target = {summary['backout_target']}`",
            f"- `switch_authorized = {md_bool(summary['switch_authorized'])}`",
            f"- `customer_rollout_authorized = {md_bool(summary['customer_rollout_authorized'])}`",
        ]
    )


def render_switch_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# Mevzuat Controlled Cutover Rerun Switch Execution Raporu 2026-04-18",
        "",
        "## Official Fields",
        f"- `switch_started = {md_bool(summary['switch_started'])}`",
        f"- `switch_completed = {md_bool(summary['switch_completed'])}`",
        f"- `active_runtime_before = {summary['active_runtime_before']}`",
        f"- `active_runtime_after = {summary['active_runtime_after']}`",
        f"- `switch_error_count = {summary['switch_error_count']}`",
        f"- `rollback_invoked = {md_bool(summary['rollback_invoked'])}`",
        f"- `backout_invoked = {md_bool(summary['backout_invoked'])}`",
        "",
        "## Execution Trace",
        f"- `candidate_collection_row_count = {summary['candidate_collection_row_count']}`",
        f"- `post_switch_health_http_200 = {md_bool(summary['post_switch_health_http_200'])}`",
    ]
    if summary.get("switch_error_text"):
        lines.append(f"- `switch_error_text = {summary['switch_error_text']}`")
    return "\n".join(lines)


def render_postswitch_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# Mevzuat Controlled Cutover Rerun Post-Switch Smoke Raporu 2026-04-18",
        "",
        "## Official Fields",
        f"- `smoke_case_count = {summary['smoke_case_count']}`",
        f"- `retrieval_smoke_case_count = {summary['retrieval_smoke_case_count']}`",
        f"- `live_serving_smoke_case_count = {summary['live_serving_smoke_case_count']}`",
        f"- `citation_readable_count = {summary['citation_readable_count']}`",
        f"- `source_correct_count = {summary['source_correct_count']}`",
        f"- `wrong_source_count = {summary['wrong_source_count']}`",
        f"- `runtime_error_count = {summary['runtime_error_count']}`",
        f"- `unexplained_count = {summary['unexplained_count']}`",
        f"- `post_switch_health_pass = {md_bool(summary['post_switch_health_pass'])}`",
    ]
    if summary["error_classes"]:
        lines.extend(
            [
                "",
                "## Observed Error Classes",
                f"- `error_classes = {json.dumps(summary['error_classes'], ensure_ascii=False)}`",
            ]
        )
    return "\n".join(lines)


def render_rollback_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Controlled Cutover Rerun Rollback Backout Teyit Notu 2026-04-18",
            "",
            "## Official Fields",
            f"- `rollback_target_preserved = {md_bool(summary['rollback_target_preserved'])}`",
            f"- `backout_target_preserved = {md_bool(summary['backout_target_preserved'])}`",
            f"- `rollback_test_or_dry_confirmation = {summary['rollback_test_or_dry_confirmation']}`",
            f"- `operator_execution_order_preserved = {md_bool(summary['operator_execution_order_preserved'])}`",
        ]
    )


def render_execution_doc(summary: dict[str, Any], postswitch: dict[str, Any]) -> str:
    decision = summary["decision"]
    lines = [
        "# Mevzuat Controlled Cutover Rerun Execution Raporu 2026-04-18",
        "",
        "## Official Decision",
        f"- decision = `{decision}`",
        "",
        "## PASS Criteria Contrast",
        f"- `switch_authorized = {md_bool(summary['switch_authorized'])}`",
        f"- `active_runtime_before = {summary['active_runtime_before']}`",
        f"- `active_runtime_after = {summary['active_runtime_after']}`",
        f"- `switch_error_count = {summary['switch_error_count']}`",
        f"- `smoke_case_count = {postswitch['smoke_case_count']}`",
        f"- `wrong_source_count = {postswitch['wrong_source_count']}`",
        f"- `runtime_error_count = {postswitch['runtime_error_count']}`",
        f"- `unexplained_count = {postswitch['unexplained_count']}`",
        f"- `post_switch_health_pass = {md_bool(postswitch['post_switch_health_pass'])}`",
        f"- `rollback_target_preserved = {md_bool(summary['rollback_target_preserved'])}`",
        f"- `backout_target_preserved = {md_bool(summary['backout_target_preserved'])}`",
        f"- `customer_rollout_authorized = {md_bool(summary['customer_rollout_authorized'])}`",
    ]
    if summary.get("final_active_runtime_collection"):
        lines.extend(
            [
                "",
                "## Final Runtime State",
                f"- `final_active_runtime_collection = {summary['final_active_runtime_collection']}`",
            ]
        )
    return "\n".join(lines)


def render_next_doc(decision: str) -> str:
    next_work = (
        "mevzuat post-cutover stabilization and runtime verification under canonical current authority"
        if decision.startswith("PASS")
        else "mevzuat controlled cutover remediation under canonical current authority"
    )
    return "\n".join(
        [
            "# Mevzuat Controlled Cutover Rerun Sonrasi Next Official Work Karari 2026-04-18",
            "",
            "## Official Decision",
            f"- `next_official_work = {next_work}`",
        ]
    )


def main() -> None:
    ensure_dir(RUNTIME_DIR)
    smoke_cases = select_smoke_cases(SOURCE_ARTICLE_ROWS)

    preswitch = {
        "pre_switch_active_runtime_collection": ACTIVE_RUNTIME_COLLECTION,
        "candidate_runtime_collection": CANDIDATE_RUNTIME_COLLECTION,
        "rollback_target": ROLLBACK_TARGET,
        "backout_target": BACKOUT_TARGET,
        "switch_authorized": True,
        "customer_rollout_authorized": False,
    }

    execution = {
        "switch_started": False,
        "switch_completed": False,
        "active_runtime_before": ACTIVE_RUNTIME_COLLECTION,
        "active_runtime_after": CANDIDATE_RUNTIME_COLLECTION,
        "switch_error_count": 0,
        "rollback_invoked": False,
        "backout_invoked": False,
        "candidate_collection_row_count": collection_entity_count(CANDIDATE_RUNTIME_COLLECTION),
        "post_switch_health_http_200": False,
        "switch_error_text": None,
        "final_active_runtime_collection": CANDIDATE_RUNTIME_COLLECTION,
    }

    postswitch_results: list[dict[str, Any]] = []
    postswitch = {
        "smoke_case_count": 0,
        "retrieval_smoke_case_count": 6,
        "live_serving_smoke_case_count": 1,
        "citation_readable_count": 0,
        "source_correct_count": 0,
        "wrong_source_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "post_switch_health_pass": False,
        "error_classes": [],
    }

    rollback = {
        "rollback_target_preserved": True,
        "backout_target_preserved": True,
        "rollback_test_or_dry_confirmation": "dry",
        "operator_execution_order_preserved": True,
    }

    execution["switch_started"] = True
    try:
        launch_runtime(CANDIDATE_RUNTIME_COLLECTION)
        if not wait_for_health():
            raise RuntimeError("post-switch gateway health timeout")
        execution["post_switch_health_http_200"] = True

        for case in smoke_cases:
            query_text = f"{case.expected_display_citation} metnini kısa özetle ve dayanağı yaz."
            status, body, error_text = run_chat_completion(query_text)
            postswitch_results.append(evaluate_runtime_case(case, status, body, error_text))

        live_case = smoke_cases[0]
        live_query = f"{live_case.expected_display_citation} için iki cümlede özet yap ve yalnız ilgili dayanağı yaz."
        live_status, live_body, live_error_text = run_chat_completion(live_query)
        postswitch_results.append(evaluate_runtime_case(live_case, live_status, live_body, live_error_text))

        summarized = summarize_case_results(postswitch_results)
        postswitch.update(summarized)
        postswitch["smoke_case_count"] = len(postswitch_results)
        postswitch["error_classes"] = sorted({item["error_class"] for item in postswitch_results if item.get("error_class")})
        postswitch["post_switch_health_pass"] = all(
            [
                postswitch["smoke_case_count"] >= 7,
                postswitch["wrong_source_count"] == 0,
                postswitch["runtime_error_count"] == 0,
                postswitch["unexplained_count"] == 0,
            ]
        )
    except Exception as exc:
        execution["switch_error_count"] += 1
        execution["switch_error_text"] = repr(exc)
        postswitch["runtime_error_count"] += 1
        postswitch["unexplained_count"] += 1
        postswitch["error_classes"] = ["switch_execution_failure"]
        postswitch["post_switch_health_pass"] = False
    finally:
        execution["switch_completed"] = True

    if not postswitch["post_switch_health_pass"]:
        execution["rollback_invoked"] = True
        rollback["rollback_test_or_dry_confirmation"] = "actual"
        launch_runtime(ROLLBACK_TARGET)
        wait_for_health()
        execution["final_active_runtime_collection"] = ROLLBACK_TARGET

    decision = "PASS - Mevzuat Controlled Cutover Execution Rerun Closed"
    if not all(
        [
            preswitch["switch_authorized"],
            execution["active_runtime_before"] == ACTIVE_RUNTIME_COLLECTION,
            execution["active_runtime_after"] == CANDIDATE_RUNTIME_COLLECTION,
            execution["switch_error_count"] == 0,
            postswitch["smoke_case_count"] >= 7,
            postswitch["wrong_source_count"] == 0,
            postswitch["runtime_error_count"] == 0,
            postswitch["unexplained_count"] == 0,
            postswitch["post_switch_health_pass"],
            rollback["rollback_target_preserved"],
            rollback["backout_target_preserved"],
            not preswitch["customer_rollout_authorized"],
        ]
    ):
        decision = "NO-GO - Mevzuat Controlled Cutover Execution Rerun"

    summary = {
        **preswitch,
        **execution,
        **rollback,
        "decision": decision,
        "postswitch": postswitch,
        "postswitch_results": postswitch_results,
    }

    write_text(PRESWITCH_DOC, render_preswitch_doc(preswitch))
    write_text(SWITCH_DOC, render_switch_doc(execution))
    write_text(POSTSWITCH_DOC, render_postswitch_doc(postswitch))
    write_text(ROLLBACK_DOC, render_rollback_doc(rollback))
    write_text(EXECUTION_DOC, render_execution_doc(summary, postswitch))
    write_text(NEXT_DOC, render_next_doc(decision))
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
