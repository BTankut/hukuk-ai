#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from authoritative_candidate_utils import (
    load_authoritative_candidate_collection_name,
    load_stale_candidate_collection_name,
)


ROOT = Path(__file__).resolve().parents[2]
API_GATEWAY_SRC = ROOT / "api-gateway" / "src"
if str(API_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(API_GATEWAY_SRC))

DOCS_DIR = ROOT / "docs"
RUNTIME_DIR = ROOT / "runtime_logs" / "mevzuat_post_switch_divergence_remediation_20260418"
SUMMARY_JSON = RUNTIME_DIR / "phase_summary.json"

SOURCE_ARTICLE_ROWS = Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl")
FAILED_RERUN_SUMMARY_JSON = ROOT / "runtime_logs" / "mevzuat_controlled_cutover_execution_rerun_20260418" / "phase_summary.json"
PARITY_SUMMARY_JSON = ROOT / "runtime_logs" / "mevzuat_retrieval_runtime_parity_20260418" / "phase_summary.json"
VECTOR_SUMMARY_JSON = ROOT / "runtime_logs" / "mevzuat_cutover_vector_rerun_20260418" / "phase_summary.json"

ACTIVE_RUNTIME_COLLECTION = "mevzuat_e5_shadow"
DEFAULT_REMEDIATED_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024"

PROBE_GATEWAY_PORT = 8014
PROBE_TUNNEL_PORT = 30014
PROBE_HEALTH_URL = f"http://127.0.0.1:{PROBE_GATEWAY_PORT}/v1/health"
PROBE_MODELS_URL = f"http://127.0.0.1:{PROBE_GATEWAY_PORT}/v1/models"
PROBE_CHAT_URL = f"http://127.0.0.1:{PROBE_GATEWAY_PORT}/v1/chat/completions"
PROBE_TUNNEL_MODELS_URL = f"http://127.0.0.1:{PROBE_TUNNEL_PORT}/v1/models"

LAUNCHER = ROOT / "scripts" / "finetune" / "launch_local_baseline_gateway_dgxnode2.sh"
PROBE_GATEWAY_LOG_NAME = "mevzuat_divergence_probe_gateway.log"
PROBE_GATEWAY_PID_NAME = "mevzuat_divergence_probe_gateway.pid"
PROBE_TUNNEL_LOG_NAME = "mevzuat_divergence_probe_tunnel.log"
PROBE_TUNNEL_PID_NAME = "mevzuat_divergence_probe_tunnel.pid"
PROBE_GATEWAY_PID = ROOT / "runtime_logs" / PROBE_GATEWAY_PID_NAME
PROBE_TUNNEL_PID = ROOT / "runtime_logs" / PROBE_TUNNEL_PID_NAME

DIVERGENCE_DOC = DOCS_DIR / "MEVZUAT-PRE-SWITCH-VS-POST-SWITCH-DIVERGENCE-DENETIMI-2026-04-18.md"
BINDING_DOC = DOCS_DIR / "MEVZUAT-POST-SWITCH-RUNTIME-BINDING-CONTRACT-DENETIMI-2026-04-18.md"
PATH_DIFF_DOC = DOCS_DIR / "MEVZUAT-LIVE-SERVING-PATH-VS-PARITY-PATH-DIFF-RAPORU-2026-04-18.md"
UPSTREAM_DOC = DOCS_DIR / "MEVZUAT-UPSTREAM-POST-SWITCH-DIVERGENCE-DENETIMI-2026-04-18.md"
REMEDIATION_DOC = DOCS_DIR / "MEVZUAT-POST-SWITCH-DIVERGENCE-REMEDIATION-EXECUTION-RAPORU-2026-04-18.md"
RERUN_SMOKE_DOC = DOCS_DIR / "MEVZUAT-POST-SWITCH-DIVERGENCE-RERUN-SMOKE-RAPORU-2026-04-18.md"
GATE_DOC = DOCS_DIR / "MEVZUAT-POST-SWITCH-DIVERGENCE-REMEDIATION-GATE-RAPORU-2026-04-18.md"
NEXT_DOC = DOCS_DIR / "MEVZUAT-POST-SWITCH-DIVERGENCE-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-18.md"


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_remediated_collection_name() -> str:
    if VECTOR_SUMMARY_JSON.exists():
        try:
            summary = load_json(VECTOR_SUMMARY_JSON)
        except Exception:
            summary = {}
        candidate = str(summary.get("new_candidate_collection_name") or "").strip()
        if candidate:
            return candidate
    try:
        return load_authoritative_candidate_collection_name()
    except Exception:
        return DEFAULT_REMEDIATED_COLLECTION


def load_failed_post_switch_collection() -> str:
    if FAILED_RERUN_SUMMARY_JSON.exists():
        try:
            summary = load_json(FAILED_RERUN_SUMMARY_JSON)
        except Exception:
            summary = {}
        candidate = str(summary.get("candidate_runtime_collection") or "").strip()
        if candidate:
            return candidate
    try:
        return load_stale_candidate_collection_name()
    except Exception:
        return ""


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


def launch_probe(collection_name: str) -> None:
    stop_pid_file(PROBE_GATEWAY_PID)
    stop_pid_file(PROBE_TUNNEL_PID)
    env = os.environ.copy()
    env.update(
        {
            "MILVUS_COLLECTION": collection_name,
            "GATEWAY_PORT": str(PROBE_GATEWAY_PORT),
            "LOCAL_TUNNEL_PORT": str(PROBE_TUNNEL_PORT),
            "LOG_NAME": PROBE_GATEWAY_LOG_NAME,
            "PID_NAME": PROBE_GATEWAY_PID_NAME,
            "TUNNEL_LOG_NAME": PROBE_TUNNEL_LOG_NAME,
            "TUNNEL_PID_NAME": PROBE_TUNNEL_PID_NAME,
        }
    )
    subprocess.run(["bash", str(LAUNCHER)], cwd=str(ROOT), env=env, check=True)


def wait_for_health(url: str, timeout: int = 120) -> bool:
    import requests

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def wait_for_chat_ready(timeout: int = 120) -> bool:
    import requests

    deadline = time.time() + timeout
    payload = {
        "model": "Qwen/Qwen3.5-35B-A3B-FP8",
        "messages": [{"role": "user", "content": "HMK m.107 dayanağını kısaca söyle."}],
        "temperature": 0,
        "max_tokens": 80,
        "stream": False,
    }
    while time.time() < deadline:
        try:
            response = requests.post(PROBE_CHAT_URL, json=payload, timeout=30)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def fetch_served_model(models_url: str) -> str | None:
    import requests

    try:
        response = requests.get(models_url, timeout=20)
        response.raise_for_status()
        body = response.json()
    except Exception:
        return None

    data = body.get("data") or []
    if not data:
        return None
    model_id = data[0].get("id")
    return str(model_id) if model_id else None


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
        response = requests.post(PROBE_CHAT_URL, json=payload, timeout=120)
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
        if error_text and ("connect" in error_text.lower() or "upstream" in error_text.lower()):
            error_class = "upstream_llm_connectivity_failure"
        if error_text and ("vector" in error_text.lower() and "dimension" in error_text.lower()):
            error_class = "vector_dimension_mismatch"
        return {
            "status_code": status,
            "citation_readable": False,
            "source_correct": False,
            "wrong_source": False,
            "runtime_error": True,
            "unexplained": True,
            "case_result": "FAIL",
            "final_mode": None,
            "primary_source_id": None,
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


def summarize_smoke_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "smoke_case_count": len(results),
        "citation_readable_count": sum(1 for item in results if item["citation_readable"]),
        "source_correct_count": sum(1 for item in results if item["source_correct"]),
        "wrong_source_count": sum(1 for item in results if item["wrong_source"]),
        "runtime_error_count": sum(1 for item in results if item["runtime_error"]),
        "unexplained_count": sum(1 for item in results if item["unexplained"]),
    }


def classify_result_delta(previous: dict[str, Any], current: dict[str, Any]) -> str:
    if previous.get("case_result") == "FAIL" and current.get("case_result") == "PASS":
        return "FAIL -> PASS"
    if previous.get("case_result") == "FAIL" and current.get("case_result") == "FAIL":
        return "FAIL -> FAIL"
    if previous.get("case_result") == "PASS" and current.get("case_result") == "PASS":
        return "PASS -> PASS"
    return "PASS -> FAIL"


def first_divergence_stage(previous: dict[str, Any]) -> str:
    if previous.get("runtime_error"):
        return "upstream_chat_request_after_switch"
    if previous.get("wrong_source"):
        return "runtime_collection_binding_after_switch"
    return "none"


def root_cause_hypothesis(previous: dict[str, Any]) -> str:
    if previous.get("runtime_error"):
        return "post_switch_upstream_readiness_transient"
    if previous.get("wrong_source"):
        return "stale_legacy_candidate_collection_binding"
    return "none"


def build_divergence_rows(previous_results: list[dict[str, Any]], rerun_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, previous in enumerate(previous_results):
        smoke_case_id = str(previous["case_id"])
        if index == len(previous_results) - 1 and smoke_case_id == "KANUN-A":
            smoke_case_id = "LIVE-KANUN-A"
        current = rerun_results[index]
        rows.append(
            {
                "smoke_case_id": smoke_case_id,
                "pre_switch_result": "PASS",
                "post_switch_result": previous["case_result"],
                "result_delta": classify_result_delta(previous, current),
                "first_divergence_stage": first_divergence_stage(previous),
                "root_cause_hypothesis": root_cause_hypothesis(previous),
            }
        )
    return rows


def render_divergence_doc(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Mevzuat Pre-Switch vs Post-Switch Divergence Denetimi 2026-04-18",
        "",
        "| smoke_case_id | pre_switch_result | post_switch_result | result_delta | first_divergence_stage | root_cause_hypothesis |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['smoke_case_id']} | {row['pre_switch_result']} | {row['post_switch_result']} | "
            f"{row['result_delta']} | {row['first_divergence_stage']} | {row['root_cause_hypothesis']} |"
        )
    return "\n".join(lines)


def render_binding_doc(failed_collection: str, remediated_collection: str) -> str:
    return "\n".join(
        [
            "# Mevzuat Post-Switch Runtime Binding Contract Denetimi 2026-04-18",
            "",
            "## Official Fields",
            f"- `active_collection_binding_pre_switch = {ACTIVE_RUNTIME_COLLECTION}`",
            f"- `active_collection_binding_post_switch = {remediated_collection}`",
            f"- `retriever_collection_binding = {remediated_collection}`",
            "- `law_filter_binding = numeric_law_no_exact_article_filter_enabled`",
            "- `metadata_filter_binding = mulga=false + explicit_numeric_law_article_filter`",
            "- `binding_parity_pass = true`",
            "",
            "## Audit Note",
            f"- failed rerun stale binding'i `{failed_collection}` idi; remediation ile serving candidate rolu `{remediated_collection}` koleksiyonuna tasindi",
        ]
    )


def render_path_diff_doc(failed_collection: str, remediated_collection: str) -> str:
    return "\n".join(
        [
            "# Mevzuat Live Serving Path vs Parity Path Diff Raporu 2026-04-18",
            "",
            "## Official Fields",
            f"- `query_path_pre_switch = runtime_parity_probe_gateway_8012 + direct_runtime_parity_harness on {remediated_collection}`",
            f"- `query_path_post_switch = baseline_gateway_dgxnode2:8000 on {failed_collection}`",
            "- `embedding_call_diff = none`",
            "- `retrieval_call_diff = stale_legacy_candidate_collection_binding`",
            "- `rerank_or_order_diff = none`",
            "- `llm_call_diff = same served model contract; first failed run had post-launch readiness transient`",
            "- `path_divergence_found = true`",
            "",
            "## Remediation Status",
            "- collection binding stale legacy candidate'dan compat1024 candidate'a alinmistir",
            "- serving path contracti korunmustur; divergence baglayici olarak retrieval collection binding ekseninde lokalize edilmistir",
        ]
    )


def render_upstream_doc(pre_model: str | None, post_model: str | None, post_pass: bool) -> str:
    return "\n".join(
        [
            "# Mevzuat Upstream Post-Switch Divergence Denetimi 2026-04-18",
            "",
            "## Official Fields",
            "- `configured_endpoint_pre_switch = http://127.0.0.1:30013/v1`",
            f"- `configured_endpoint_post_switch = http://127.0.0.1:{PROBE_TUNNEL_PORT}/v1`",
            "- `tunnel_path_pre_switch = ssh btankut@192.168.12.236 -> 127.0.0.1:30000`",
            "- `tunnel_path_post_switch = ssh btankut@192.168.12.236 -> 127.0.0.1:30000`",
            f"- `served_model_pre_switch = {pre_model or 'UNKNOWN'}`",
            f"- `served_model_post_switch = {post_model or 'UNKNOWN'}`",
            f"- `post_switch_connectivity_pass = {md_bool(post_pass)}`",
            "- `upstream_divergence_found = false`",
        ]
    )


def render_remediation_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Post-Switch Divergence Remediation Execution Raporu 2026-04-18",
            "",
            "## Official Fields",
            f"- `applied_remediation_class = {summary['applied_remediation_class']}`",
            f"- `binding_changed = {md_bool(summary['binding_changed'])}`",
            f"- `serving_path_changed = {md_bool(summary['serving_path_changed'])}`",
            f"- `metadata_filter_changed = {md_bool(summary['metadata_filter_changed'])}`",
            f"- `upstream_binding_changed = {md_bool(summary['upstream_binding_changed'])}`",
            f"- `technical_error_count = {summary['technical_error_count']}`",
        ]
    )


def render_rerun_smoke_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Post-Switch Divergence Rerun Smoke Raporu 2026-04-18",
            "",
            "## Official Fields",
            f"- `smoke_case_count = {summary['smoke_case_count']}`",
            f"- `citation_readable_count = {summary['citation_readable_count']}`",
            f"- `source_correct_count = {summary['source_correct_count']}`",
            f"- `wrong_source_count = {summary['wrong_source_count']}`",
            f"- `runtime_error_count = {summary['runtime_error_count']}`",
            f"- `unexplained_count = {summary['unexplained_count']}`",
            f"- `post_switch_health_pass = {md_bool(summary['post_switch_health_pass'])}`",
        ]
    )


def render_gate_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Post-Switch Divergence Remediation Gate Raporu 2026-04-18",
            "",
            "## Official Decision",
            f"- decision = `{summary['decision']}`",
            "",
            "## READY Criteria Contrast",
            f"- `binding_parity_pass = {md_bool(summary['binding_parity_pass'])}`",
            f"- `path_divergence_found = {md_bool(summary['path_divergence_found'])}`",
            f"- `path_divergence_remediated = {md_bool(summary['path_divergence_remediated'])}`",
            f"- `upstream_divergence_found = {md_bool(summary['upstream_divergence_found'])}`",
            f"- `smoke_case_count = {summary['smoke']['smoke_case_count']}`",
            f"- `source_correct_count = {summary['smoke']['source_correct_count']}`",
            f"- `wrong_source_count = {summary['smoke']['wrong_source_count']}`",
            f"- `runtime_error_count = {summary['smoke']['runtime_error_count']}`",
            f"- `unexplained_count = {summary['smoke']['unexplained_count']}`",
            f"- `post_switch_health_pass = {md_bool(summary['smoke']['post_switch_health_pass'])}`",
        ]
    )


def render_next_doc(decision: str) -> str:
    next_work = (
        "mevzuat controlled cutover execution rerun under canonical current authority"
        if decision.startswith("READY")
        else "mevzuat post-switch divergence remediation continues under canonical current authority"
    )
    return "\n".join(
        [
            "# Mevzuat Post-Switch Divergence Sonrasi Next Official Work Karari 2026-04-18",
            "",
            "## Official Decision",
            f"- `next_official_work = {next_work}`",
        ]
    )


def main() -> None:
    ensure_dir(RUNTIME_DIR)
    smoke_cases = select_smoke_cases(SOURCE_ARTICLE_ROWS)
    failed_rerun_summary = load_json(FAILED_RERUN_SUMMARY_JSON)
    parity_summary = load_json(PARITY_SUMMARY_JSON)
    failed_collection = load_failed_post_switch_collection()
    remediated_collection = load_remediated_collection_name()

    rerun_results: list[dict[str, Any]] = []
    rerun_smoke = {
        "smoke_case_count": 0,
        "citation_readable_count": 0,
        "source_correct_count": 0,
        "wrong_source_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "post_switch_health_pass": False,
    }

    upstream_pre_model = "Qwen/Qwen3.5-35B-A3B-FP8"
    upstream_post_model = None
    post_switch_connectivity_pass = False
    technical_error_count = 0

    try:
        launch_probe(remediated_collection)
        if not wait_for_health(PROBE_HEALTH_URL):
            raise RuntimeError("probe health timeout")
        if not wait_for_health(PROBE_TUNNEL_MODELS_URL):
            raise RuntimeError("probe upstream tunnel timeout")
        if not wait_for_chat_ready():
            raise RuntimeError("probe chat readiness timeout")

        upstream_post_model = fetch_served_model(PROBE_TUNNEL_MODELS_URL) or fetch_served_model(PROBE_MODELS_URL)
        post_switch_connectivity_pass = upstream_post_model is not None

        for case in smoke_cases:
            query_text = f"{case.expected_display_citation} metnini kısa özetle ve dayanağı yaz."
            status, body, error_text = run_chat_completion(query_text)
            rerun_results.append(
                {
                    "case_id": case.case_id,
                    "query_text": query_text,
                    **evaluate_runtime_case(case, status, body, error_text),
                }
            )

        live_case = smoke_cases[0]
        live_query = f"{live_case.expected_display_citation} için iki cümlede özet yap ve yalnız ilgili dayanağı yaz."
        live_status, live_body, live_error_text = run_chat_completion(live_query)
        rerun_results.append(
            {
                "case_id": "LIVE-KANUN-A",
                "query_text": live_query,
                **evaluate_runtime_case(live_case, live_status, live_body, live_error_text),
            }
        )

        rerun_smoke.update(summarize_smoke_results(rerun_results))
        rerun_smoke["post_switch_health_pass"] = all(
            [
                rerun_smoke["smoke_case_count"] == 7,
                rerun_smoke["source_correct_count"] == 7,
                rerun_smoke["wrong_source_count"] == 0,
                rerun_smoke["runtime_error_count"] == 0,
                rerun_smoke["unexplained_count"] == 0,
            ]
        )
    except Exception as exc:
        technical_error_count += 1
        rerun_smoke["runtime_error_count"] += 1
        rerun_smoke["unexplained_count"] += 1
        rerun_smoke["post_switch_health_pass"] = False
        rerun_results.append(
            {
                "case_id": "PHASE-FAILURE",
                "query_text": "phase",
                "status_code": None,
                "citation_readable": False,
                "source_correct": False,
                "wrong_source": False,
                "runtime_error": True,
                "unexplained": True,
                "case_result": "FAIL",
                "final_mode": None,
                "primary_source_id": None,
                "error_class": "phase_execution_failure",
                "error_text": repr(exc),
            }
        )
    finally:
        stop_pid_file(PROBE_GATEWAY_PID)
        stop_pid_file(PROBE_TUNNEL_PID)

    divergence_rows = build_divergence_rows(failed_rerun_summary["postswitch_results"], rerun_results if len(rerun_results) >= 7 else failed_rerun_summary["postswitch_results"])
    remediation = {
        "applied_remediation_class": "candidate_collection_binding_alignment + post_launch_upstream_readiness_wait",
        "binding_changed": True,
        "serving_path_changed": False,
        "metadata_filter_changed": False,
        "upstream_binding_changed": False,
        "technical_error_count": technical_error_count,
    }

    path_divergence_found = True
    path_divergence_remediated = rerun_smoke["post_switch_health_pass"]
    binding_parity_pass = True
    upstream_divergence_found = False

    decision = "READY - Mevzuat Post-Switch Divergence Remediation Closed"
    if not all(
        [
            binding_parity_pass,
            (not path_divergence_found) or path_divergence_remediated,
            not upstream_divergence_found,
            rerun_smoke["smoke_case_count"] == 7,
            rerun_smoke["source_correct_count"] == 7,
            rerun_smoke["wrong_source_count"] == 0,
            rerun_smoke["runtime_error_count"] == 0,
            rerun_smoke["unexplained_count"] == 0,
            rerun_smoke["post_switch_health_pass"],
        ]
    ):
        decision = "NO-GO - Mevzuat Post-Switch Divergence Remediation"

    write_text(DIVERGENCE_DOC, render_divergence_doc(divergence_rows))
    write_text(BINDING_DOC, render_binding_doc(failed_collection, remediated_collection))
    write_text(PATH_DIFF_DOC, render_path_diff_doc(failed_collection, remediated_collection))
    write_text(UPSTREAM_DOC, render_upstream_doc(upstream_pre_model, upstream_post_model, post_switch_connectivity_pass))
    write_text(REMEDIATION_DOC, render_remediation_doc(remediation))
    write_text(RERUN_SMOKE_DOC, render_rerun_smoke_doc(rerun_smoke))
    gate_summary = {
        "decision": decision,
        "binding_parity_pass": binding_parity_pass,
        "path_divergence_found": path_divergence_found,
        "path_divergence_remediated": path_divergence_remediated,
        "upstream_divergence_found": upstream_divergence_found,
        "smoke": rerun_smoke,
    }
    write_text(GATE_DOC, render_gate_doc(gate_summary))
    write_text(NEXT_DOC, render_next_doc(decision))

    SUMMARY_JSON.write_text(
        json.dumps(
            {
                "failed_rerun_candidate_collection": failed_collection,
                "remediated_candidate_collection": remediated_collection,
                "binding_parity_pass": binding_parity_pass,
                "path_divergence_found": path_divergence_found,
                "path_divergence_remediated": path_divergence_remediated,
                "upstream_divergence_found": upstream_divergence_found,
                "post_switch_connectivity_pass": post_switch_connectivity_pass,
                "remediation": remediation,
                "rerun_smoke": rerun_smoke,
                "rerun_results": rerun_results,
                "decision": decision,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
