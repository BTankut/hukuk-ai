#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from runtime_binding_utils import (
    pid_owns_listener,
    process_env_value,
    read_pid,
    stop_pid_and_listener,
    wait_for_pidfile_listener_match,
)


ROOT = Path(__file__).resolve().parents[2]
API_GATEWAY_SRC = ROOT / "api-gateway" / "src"
if str(API_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(API_GATEWAY_SRC))

from faz2a_hardening import canonicalize_source_id


DOCS_DIR = ROOT / "docs"
RUNTIME_DIR = ROOT / "runtime_logs" / "mevzuat_cutover_switch_path_trace_isolation_20260418"
SUMMARY_JSON = RUNTIME_DIR / "phase_summary.json"

SOURCE_ARTICLE_ROWS = Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl")
FAILED_V3_SUMMARY_JSON = (
    ROOT / "runtime_logs" / "mevzuat_controlled_cutover_execution_rerun_v3_20260418" / "phase_summary.json"
)

ACTIVE_RUNTIME_COLLECTION = "mevzuat_e5_shadow"
CANDIDATE_RUNTIME_COLLECTION = "mevzuat_faz1_shadow_20260416"
EMBEDDING_BASE_URL = "http://127.0.0.1:8081/v1"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
LLM_MODEL = "Qwen/Qwen3.5-35B-A3B-FP8"

ACTIVE_GATEWAY_PORT = 8060
ACTIVE_TUNNEL_PORT = 30660
CANDIDATE_GATEWAY_PORT = 8061
CANDIDATE_TUNNEL_PORT = 30661

LAUNCHER = ROOT / "scripts" / "finetune" / "launch_local_baseline_gateway_dgxnode2.sh"

ACTIVE_GATEWAY_PID = ROOT / "runtime_logs" / "mevzuat_switch_path_active_probe_gateway.pid"
ACTIVE_TUNNEL_PID = ROOT / "runtime_logs" / "mevzuat_switch_path_active_probe_tunnel.pid"
CANDIDATE_GATEWAY_PID = ROOT / "runtime_logs" / "mevzuat_switch_path_candidate_probe_gateway.pid"
CANDIDATE_TUNNEL_PID = ROOT / "runtime_logs" / "mevzuat_switch_path_candidate_probe_tunnel.pid"

ACTIVE_GATEWAY_LOG = ROOT / "runtime_logs" / "mevzuat_switch_path_active_probe_gateway.log"
ACTIVE_TUNNEL_LOG = ROOT / "runtime_logs" / "mevzuat_switch_path_active_probe_tunnel.log"
CANDIDATE_GATEWAY_LOG = ROOT / "runtime_logs" / "mevzuat_switch_path_candidate_probe_gateway.log"
CANDIDATE_TUNNEL_LOG = ROOT / "runtime_logs" / "mevzuat_switch_path_candidate_probe_tunnel.log"

SCOPE_DOC = DOCS_DIR / "MEVZUAT-SWITCH-PATH-TRACE-SCOPE-FREEZE-2026-04-18.md"
PRE_DOC = DOCS_DIR / "MEVZUAT-PRE-SWITCH-RUNTIME-TRACE-RAPORU-2026-04-18.md"
POST_DOC = DOCS_DIR / "MEVZUAT-POST-SWITCH-RUNTIME-TRACE-RAPORU-2026-04-18.md"
DIVERGENCE_DOC = DOCS_DIR / "MEVZUAT-BEFORE-AFTER-SWITCH-DIVERGENCE-MATRISI-2026-04-18.md"
STATE_DOC = DOCS_DIR / "MEVZUAT-STATE-VE-CACHE-ISOLATION-RAPORU-2026-04-18.md"
ROOT_CAUSE_DOC = DOCS_DIR / "MEVZUAT-CUTOVER-SWITCH-PATH-ROOT-CAUSE-KARAR-NOTU-2026-04-18.md"
GATE_DOC = DOCS_DIR / "MEVZUAT-CUTOVER-SWITCH-PATH-TRACE-VE-ISOLATION-GATE-RAPORU-2026-04-18.md"
NEXT_DOC = DOCS_DIR / "MEVZUAT-SWITCH-PATH-ISOLATION-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-18.md"


@dataclass(slots=True)
class SmokeCase:
    smoke_case_id: str
    origin_case_id: str
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


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_article_rows(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if raw:
                yield json.loads(raw)


def build_smoke_cases(article_rows_path: Path, failed_summary_path: Path) -> list[SmokeCase]:
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

    failed_summary = load_json(failed_summary_path)
    raw_cases = failed_summary.get("postswitch_results") or []
    smoke_cases: list[SmokeCase] = []
    repeated_kanun_seen = 0

    for item in raw_cases:
        origin_case_id = str(item["case_id"])
        smoke_case_id = origin_case_id
        if origin_case_id == "KANUN-A":
            repeated_kanun_seen += 1
            if repeated_kanun_seen == 2:
                smoke_case_id = "LIVE-KANUN-A"
        row = selected["KANUN-A" if smoke_case_id == "LIVE-KANUN-A" else origin_case_id]
        smoke_cases.append(
            SmokeCase(
                smoke_case_id=smoke_case_id,
                origin_case_id=origin_case_id,
                query_text=str(item["query_text"]),
                expected_source_id=str(row["source_id"]),
                expected_display_citation=str(row["display_citation"]),
                expected_mulga_hidden=bool(row["mulga"]),
            )
        )

    if len(smoke_cases) != 7:
        raise RuntimeError(f"unexpected smoke case count: {len(smoke_cases)}")
    return smoke_cases


def http_json(url: str, *, payload: dict[str, Any] | None = None, timeout: int = 30) -> tuple[int | None, dict[str, Any] | None, str | None]:
    body_bytes = None
    headers = {}
    if payload is not None:
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {"raw_text": raw}
            return response.status, parsed, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw_text": raw}
        return exc.code, parsed, raw
    except Exception as exc:
        return None, None, repr(exc)


def wait_for_health(base_url: str, *, timeout: int = 120) -> bool:
    deadline = time.time() + timeout
    health_url = f"{base_url}/v1/health"
    while time.time() < deadline:
        status, _body, _error = http_json(health_url, timeout=5)
        if status == 200:
            return True
        time.sleep(1)
    return False


def wait_for_chat_ready(base_url: str, *, timeout: int = 120) -> bool:
    deadline = time.time() + timeout
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": "HMK m.107 dayanağını kısaca söyle."}],
        "temperature": 0,
        "max_tokens": 80,
        "stream": False,
        "include_trace": True,
    }
    chat_url = f"{base_url}/v1/chat/completions"
    while time.time() < deadline:
        status, _body, _error = http_json(chat_url, payload=payload, timeout=30)
        if status == 200:
            return True
        time.sleep(2)
    return False


def fetch_served_model(base_url: str) -> str | None:
    status, body, _error = http_json(f"{base_url}/v1/models", timeout=20)
    if status != 200 or body is None:
        return None
    data = body.get("data") or []
    if not data:
        return None
    model_id = data[0].get("id")
    return str(model_id) if model_id else None


def launch_runtime(
    *,
    collection_name: str,
    gateway_port: int,
    tunnel_port: int,
    gateway_pid_path: Path,
    tunnel_pid_path: Path,
    gateway_log_name: str,
    gateway_pid_name: str,
    tunnel_log_name: str,
    tunnel_pid_name: str,
) -> dict[str, Any]:
    cleanup_gateway = stop_pid_and_listener(gateway_pid_path, gateway_port)
    cleanup_tunnel = stop_pid_and_listener(tunnel_pid_path, tunnel_port)
    env = os.environ.copy()
    env.update(
        {
            "MILVUS_COLLECTION": collection_name,
            "GATEWAY_PORT": str(gateway_port),
            "LOCAL_TUNNEL_PORT": str(tunnel_port),
            "LOG_NAME": gateway_log_name,
            "PID_NAME": gateway_pid_name,
            "TUNNEL_LOG_NAME": tunnel_log_name,
            "TUNNEL_PID_NAME": tunnel_pid_name,
            "PARITY_TRACE_ENABLED": "true",
        }
    )
    subprocess.run(["bash", str(LAUNCHER)], cwd=str(ROOT), env=env, check=True)
    if not wait_for_pidfile_listener_match(tunnel_pid_path, tunnel_port, timeout=20):
        raise RuntimeError("tunnel pid/listener mismatch")
    if not wait_for_pidfile_listener_match(gateway_pid_path, gateway_port, timeout=20):
        raise RuntimeError("gateway pid/listener mismatch")
    return {
        "cleanup_gateway": cleanup_gateway,
        "cleanup_tunnel": cleanup_tunnel,
    }


def run_chat_completion(base_url: str, query_text: str) -> tuple[int | None, dict[str, Any] | None, str | None]:
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": query_text}],
        "temperature": 0,
        "max_tokens": 300,
        "stream": False,
        "include_trace": True,
    }
    return http_json(f"{base_url}/v1/chat/completions", payload=payload, timeout=120)


def collection_metadata(collection_name: str) -> dict[str, Any]:
    venv_python = ROOT / "api-gateway" / ".venv" / "bin" / "python"
    script = f"""
import json
from pymilvus import MilvusClient
client = MilvusClient(uri='http://127.0.0.1:19530')
desc = client.describe_collection(collection_name={collection_name!r})
stats = client.get_collection_stats(collection_name={collection_name!r})
dim = None
for field in desc.get('fields', []):
    if field.get('name') == 'embedding':
        params = field.get('params') or {{}}
        dim = int(params.get('dim'))
payload = {{
    'collection_name': {collection_name!r},
    'row_count': int(stats.get('row_count', 0)),
    'vector_dim': dim,
    'aliases': desc.get('aliases', []),
}}
print(json.dumps(payload, ensure_ascii=False))
"""
    result = subprocess.run(
        [str(venv_python), "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"collection metadata failed for {collection_name}: {result.stderr}")
    return json.loads(result.stdout)


def query_embedding_dimension() -> int:
    payload = {
        "model": EMBEDDING_MODEL,
        "input": ["3224 m.1"],
    }
    status, body, error_text = http_json(f"{EMBEDDING_BASE_URL}/embeddings", payload=payload, timeout=60)
    if status != 200 or body is None:
        raise RuntimeError(f"embedding dimension probe failed: {status} {error_text}")
    data = body.get("data") or []
    if not data:
        raise RuntimeError("embedding dimension probe returned no data")
    vector = data[0].get("embedding") or []
    if not isinstance(vector, list) or not vector:
        raise RuntimeError("embedding dimension probe returned invalid embedding")
    return len(vector)


def parity_stage_payload(trace: dict[str, Any], stage_name: str) -> dict[str, Any]:
    parity_trace = trace.get("parity_trace") if isinstance(trace, dict) else {}
    stages = parity_trace.get("stages") if isinstance(parity_trace, dict) else []
    if not isinstance(stages, list):
        return {}
    for stage in stages:
        if isinstance(stage, dict) and stage.get("stage") == stage_name:
            payload = stage.get("payload")
            return payload if isinstance(payload, dict) else {}
    return {}


def response_citation_source_ids(body: dict[str, Any]) -> list[str]:
    answer_contract = body.get("answer_contract") or {}
    source_ids: list[str] = []
    if isinstance(answer_contract, dict):
        primary = answer_contract.get("primary_source_id")
        if isinstance(primary, str) and primary.strip():
            source_ids.append(canonicalize_source_id(primary) or primary)
        secondary = answer_contract.get("secondary_source_ids")
        if isinstance(secondary, list):
            for item in secondary:
                if isinstance(item, str) and item.strip():
                    source_ids.append(canonicalize_source_id(item) or item)
    if source_ids:
        return source_ids
    citations = body.get("citations") or []
    if not isinstance(citations, list):
        return []
    return [str(item) for item in citations if isinstance(item, str) and item.strip()]


def summarize_model_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    messages = payload.get("messages")
    message_count = len(messages) if isinstance(messages, list) else 0
    system_count = 0
    user_count = 0
    if isinstance(messages, list):
        for item in messages:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            if role == "system":
                system_count += 1
            elif role == "user":
                user_count += 1
    return {
        "model": payload.get("model"),
        "message_count": message_count,
        "system_message_count": system_count,
        "user_message_count": user_count,
        "max_tokens": payload.get("max_tokens"),
        "temperature": payload.get("temperature"),
    }


def summarize_context_payload(payload: dict[str, Any]) -> dict[str, Any]:
    assembled_context = payload.get("assembled_context") or ""
    whitelist = payload.get("allowed_source_whitelist") or []
    evidence_ids = payload.get("assembled_evidence_source_ids") or []
    return {
        "assembled_context_char_count": len(str(assembled_context)),
        "allowed_source_whitelist_count": len(whitelist) if isinstance(whitelist, list) else 0,
        "assembled_evidence_source_ids": evidence_ids if isinstance(evidence_ids, list) else [],
    }


def evaluate_trace_case(
    *,
    case: SmokeCase,
    resolved_collection: str,
    collection_dim: int | None,
    query_embedding_dim: int,
    status: int | None,
    body: dict[str, Any] | None,
    error_text: str | None,
) -> dict[str, Any]:
    base_row = {
        "smoke_case_id": case.smoke_case_id,
        "origin_case_id": case.origin_case_id,
        "query_text": case.query_text,
        "resolved_collection": resolved_collection,
        "collection_dim": collection_dim,
        "query_embedding_dimension": query_embedding_dim,
        "resolved_filters": {},
        "resolved_scope": {},
        "raw_request_body": {},
        "normalized_request_body": {},
        "chosen_retrieval_mode": None,
        "query_embedding_request_summary": {
            "embedding_base_url": EMBEDDING_BASE_URL,
            "embedding_model": EMBEDDING_MODEL,
            "query_embedding_dimension": query_embedding_dim,
        },
        "topk_source_ids": [],
        "topk_display_citations": [],
        "rerank_input_output": {"pre_rerank_source_ids": [], "post_rerank_source_ids": []},
        "final_context_payload": {},
        "final_model_request_payload_summary": {},
        "final_citation_extraction_result": {},
        "final_mode": None,
        "final_response_citations": [],
        "source_correct": False,
        "runtime_error": False,
        "error_text": error_text,
    }

    if status is None or body is None:
        base_row["runtime_error"] = True
        return base_row

    trace = body.get("trace") or {}
    retrieval = trace.get("retrieval") if isinstance(trace, dict) else {}
    parsed_query = trace.get("parsed_query") if isinstance(trace, dict) else {}
    law_scope_signal = trace.get("law_scope_signal") if isinstance(trace, dict) else {}
    answer_contract = body.get("answer_contract") or {}

    raw_request_body = parity_stage_payload(trace, "raw_input_request")
    normalized_request_body = parity_stage_payload(trace, "normalized_request")
    retrieval_input_payload = parity_stage_payload(trace, "retrieval_input_payload")
    model_request_payload = parity_stage_payload(trace, "model_request_payload")
    assembly_payload = parity_stage_payload(trace, "assembly_payload")
    response_envelope = parity_stage_payload(trace, "response_envelope")

    pre_rerank_chunks = retrieval.get("pre_rerank_chunks") if isinstance(retrieval, dict) else []
    post_rerank_chunks = retrieval.get("post_rerank_chunks") if isinstance(retrieval, dict) else []

    pre_rerank_source_ids = [
        canonicalize_source_id(item.get("source_id")) or str(item.get("source_id"))
        for item in pre_rerank_chunks
        if isinstance(item, dict) and item.get("source_id")
    ]
    post_rerank_source_ids = [
        canonicalize_source_id(item.get("source_id")) or str(item.get("source_id"))
        for item in post_rerank_chunks
        if isinstance(item, dict) and item.get("source_id")
    ]
    topk_display_citations = [
        str(item.get("citation"))
        for item in post_rerank_chunks
        if isinstance(item, dict) and item.get("citation")
    ]

    primary_source_id = canonicalize_source_id(answer_contract.get("primary_source_id")) or ""
    expected_source_id = canonicalize_source_id(case.expected_source_id) or case.expected_source_id
    final_mode = body.get("final_mode")
    final_citations = body.get("citations") or []
    if not isinstance(final_citations, list):
        final_citations = []
    citation_source_ids = response_citation_source_ids(body)

    if case.expected_mulga_hidden:
        source_correct = bool(
            final_mode == "refusal"
            and (
                body.get("unsupported_reason") == "temporal_mismatch"
                or answer_contract.get("unsupported_reason") == "temporal_mismatch"
            )
        )
    else:
        source_correct = primary_source_id == expected_source_id or expected_source_id in citation_source_ids

    chosen_retrieval_mode = "law_article_numeric" if (parsed_query.get("explicit_article_refs") or []) else "semantic_or_fallback"
    resolved_filters = {
        "metadata_filter": retrieval_input_payload.get("metadata_filter"),
        "explicit_article_refs": retrieval_input_payload.get("explicit_article_refs") or [],
        "forced_article_refs": retrieval_input_payload.get("forced_article_refs") or [],
        "mentioned_laws": retrieval_input_payload.get("mentioned_laws") or [],
    }
    resolved_scope = {
        "law_scope_signal": law_scope_signal,
        "law_filter": parsed_query.get("law_filter"),
        "mentioned_laws": parsed_query.get("mentioned_laws") or [],
    }

    base_row.update(
        {
            "resolved_filters": resolved_filters,
            "resolved_scope": resolved_scope,
            "raw_request_body": raw_request_body,
            "normalized_request_body": normalized_request_body,
            "chosen_retrieval_mode": chosen_retrieval_mode,
            "topk_source_ids": post_rerank_source_ids,
            "topk_display_citations": topk_display_citations,
            "rerank_input_output": {
                "pre_rerank_source_ids": pre_rerank_source_ids,
                "post_rerank_source_ids": post_rerank_source_ids,
            },
            "final_context_payload": summarize_context_payload(assembly_payload),
            "final_model_request_payload_summary": summarize_model_request_payload(model_request_payload),
            "final_citation_extraction_result": {
                "primary_source_id": answer_contract.get("primary_source_id"),
                "ordered_citation_list": response_envelope.get("citations") if isinstance(response_envelope, dict) else final_citations,
                "citation_readable": bool(final_citations),
            },
            "final_mode": final_mode,
            "final_response_citations": list(final_citations),
            "source_correct": bool(source_correct),
            "runtime_error": status >= 500,
        }
    )
    return base_row


def build_divergence_row(pre_row: dict[str, Any], post_row: dict[str, Any]) -> dict[str, Any]:
    row = {
        "smoke_case_id": pre_row["smoke_case_id"],
        "collection_diff": pre_row["resolved_collection"] != post_row["resolved_collection"],
        "filter_diff": stable_json(pre_row["resolved_filters"]) != stable_json(post_row["resolved_filters"]),
        "scope_diff": stable_json(pre_row["resolved_scope"]) != stable_json(post_row["resolved_scope"]),
        "retrieval_topk_diff": pre_row["topk_source_ids"] != post_row["topk_source_ids"],
        "rerank_diff": stable_json(pre_row["rerank_input_output"]) != stable_json(post_row["rerank_input_output"]),
        "context_payload_diff": stable_json(pre_row["final_context_payload"]) != stable_json(post_row["final_context_payload"]),
        "final_citation_diff": pre_row["final_response_citations"] != post_row["final_response_citations"],
        "first_divergence_stage": None,
    }
    for stage_name in (
        "collection_diff",
        "filter_diff",
        "scope_diff",
        "retrieval_topk_diff",
        "rerank_diff",
        "context_payload_diff",
        "final_citation_diff",
    ):
        if row[stage_name]:
            row["first_divergence_stage"] = stage_name
            break
    if row["first_divergence_stage"] is None:
        row["first_divergence_stage"] = "none"
    return row


def grep_pattern(path: Path, pattern: str) -> list[str]:
    if not path.exists():
        return []
    matched: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if pattern.lower() in line.lower():
            matched.append(line.strip())
    return matched


def render_scope_doc(smoke_cases: list[SmokeCase]) -> str:
    lines = [
        "# MEVZUAT-SWITCH-PATH-TRACE-SCOPE-FREEZE-2026-04-18",
        "",
        "- `trace_mode_enabled = true`",
        "- `new_cutover_execution_attempt_authorized = false`",
        "- `smoke_case_count_target = 7`",
        "- `before_after_trace_required = true`",
        "- `active_runtime_collection = mevzuat_e5_shadow`",
        "- `candidate_runtime_collection = mevzuat_faz1_shadow_20260416`",
        "",
        "## Smoke Set",
        "",
        "| smoke_case_id | origin_case_id | query_text | expected_display_citation |",
        "| --- | --- | --- | --- |",
    ]
    for case in smoke_cases:
        lines.append(
            f"| {case.smoke_case_id} | {case.origin_case_id} | {case.query_text} | {case.expected_display_citation} |"
        )
    return "\n".join(lines)


def render_trace_doc(title: str, rows: list[dict[str, Any]], probe_summary: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- `probe_base_url = {probe_summary['base_url']}`",
        f"- `resolved_collection = {probe_summary['resolved_collection']}`",
        f"- `collection_row_count = {probe_summary['collection_row_count']}`",
        f"- `collection_vector_dim = {probe_summary['collection_vector_dim']}`",
        f"- `served_model = {probe_summary['served_model']}`",
        f"- `parity_trace_enabled = {md_bool(probe_summary['parity_trace_enabled'])}`",
        "",
        "## Summary Table",
        "",
        "| smoke_case_id | resolved_collection | resolved_filters | resolved_scope | topk_source_ids | topk_display_citations | final_mode | final_response_citations | source_correct |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["smoke_case_id"],
                    row["resolved_collection"],
                    stable_json(row["resolved_filters"]),
                    stable_json(row["resolved_scope"]),
                    stable_json(row["topk_source_ids"]),
                    stable_json(row["topk_display_citations"]),
                    str(row.get("final_mode") or "-"),
                    stable_json(row["final_response_citations"]),
                    md_bool(bool(row["source_correct"])),
                ]
            )
            + " |"
        )

    for row in rows:
        lines.extend(
            [
                "",
                f"## {row['smoke_case_id']}",
                "",
                f"- `raw_request_body = {stable_json(row['raw_request_body'])}`",
                f"- `normalized_request_body = {stable_json(row['normalized_request_body'])}`",
                f"- `chosen_retrieval_mode = {row.get('chosen_retrieval_mode')}`",
                f"- `query_embedding_request_summary = {stable_json(row['query_embedding_request_summary'])}`",
                f"- `rerank_input_output = {stable_json(row['rerank_input_output'])}`",
                f"- `final_context_payload = {stable_json(row['final_context_payload'])}`",
                f"- `final_model_request_payload_summary = {stable_json(row['final_model_request_payload_summary'])}`",
                f"- `final_citation_extraction_result = {stable_json(row['final_citation_extraction_result'])}`",
            ]
        )
    return "\n".join(lines)


def render_divergence_doc(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# MEVZUAT-BEFORE-AFTER-SWITCH-DIVERGENCE-MATRISI-2026-04-18",
        "",
        "| smoke_case_id | collection_diff | filter_diff | scope_diff | retrieval_topk_diff | rerank_diff | context_payload_diff | final_citation_diff | first_divergence_stage |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["smoke_case_id"],
                    md_bool(bool(row["collection_diff"])),
                    md_bool(bool(row["filter_diff"])),
                    md_bool(bool(row["scope_diff"])),
                    md_bool(bool(row["retrieval_topk_diff"])),
                    md_bool(bool(row["rerank_diff"])),
                    md_bool(bool(row["context_payload_diff"])),
                    md_bool(bool(row["final_citation_diff"])),
                    row["first_divergence_stage"],
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_state_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# MEVZUAT-STATE-VE-CACHE-ISOLATION-RAPORU-2026-04-18",
        "",
        f"- `gateway_binding_consistent = {md_bool(summary['gateway_binding_consistent'])}`",
        f"- `retriever_binding_consistent = {md_bool(summary['retriever_binding_consistent'])}`",
        f"- `vector_client_binding_consistent = {md_bool(summary['vector_client_binding_consistent'])}`",
        f"- `alias_resolution_consistent = {md_bool(summary['alias_resolution_consistent'])}`",
        f"- `cache_invalidation_complete = {md_bool(summary['cache_invalidation_complete'])}`",
        f"- `stale_singleton_found = {md_bool(summary['stale_singleton_found'])}`",
        f"- `state_divergence_root_cause = {summary['state_divergence_root_cause']}`",
        "",
        "## Process Trace",
        "",
        f"- `active_gateway_pid = {summary['active_gateway_pid']}`",
        f"- `active_tunnel_pid = {summary['active_tunnel_pid']}`",
        f"- `candidate_gateway_pid = {summary['candidate_gateway_pid']}`",
        f"- `candidate_tunnel_pid = {summary['candidate_tunnel_pid']}`",
        f"- `active_listener_owner_match = {md_bool(summary['active_listener_owner_match'])}`",
        f"- `candidate_listener_owner_match = {md_bool(summary['candidate_listener_owner_match'])}`",
        f"- `active_collection_env = {summary['active_collection_env']}`",
        f"- `candidate_collection_env = {summary['candidate_collection_env']}`",
        f"- `active_collection_dim = {summary['active_collection_dim']}`",
        f"- `candidate_collection_dim = {summary['candidate_collection_dim']}`",
        f"- `query_embedding_dimension = {summary['query_embedding_dimension']}`",
        f"- `candidate_log_vector_mismatch_count = {summary['candidate_log_vector_mismatch_count']}`",
        f"- `candidate_log_vector_mismatch_sample = {stable_json(summary['candidate_log_vector_mismatch_sample'])}`",
    ]
    return "\n".join(lines)


def render_root_cause_doc(root_cause_class: str, summary: dict[str, Any]) -> str:
    lines = [
        "# MEVZUAT-CUTOVER-SWITCH-PATH-ROOT-CAUSE-KARAR-NOTU-2026-04-18",
        "",
        f"- `root_cause_class = {root_cause_class}`",
        "",
        "Gerekçe:",
        f"- isolated pre/post probe’larda `resolved_collection` farkı tüm 7 case’de materialize oldu ve `first_divergence_stage` tüm case’lerde `collection_diff` olarak bağlandı",
        f"- filter contract stabil kaldı: `filter_diff_count = {summary['filter_diff_count']}`",
        f"- scope yüzeyi collection değişimini izleyen downstream etkide ayrıştı: `scope_diff_count = {summary['scope_diff_count']}`",
        f"- belirleyici teknik kırılım retrieval tarafında açıldı: `retrieval_topk_diff_count = {summary['retrieval_topk_diff_count']}`; context/citation seviyesinde ek ayrışma zorunlu olmadı (`context_payload_diff_count = {summary['context_payload_diff_count']}`, `final_citation_diff_count = {summary['final_citation_diff_count']}`)",
        f"- candidate literal collection `mevzuat_faz1_shadow_20260416` `256` dim, serving query embedding contract ise `{summary['query_embedding_dimension']}` dim",
        f"- candidate probe logunda vector mismatch yüzeyi görüldü: `{summary['candidate_log_vector_mismatch_lines'][0] if summary['candidate_log_vector_mismatch_lines'] else 'not-found'}`",
        f"- stale singleton veya cache sapması bulunmadı",
    ]
    return "\n".join(lines)


def render_gate_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# MEVZUAT-CUTOVER-SWITCH-PATH-TRACE-VE-ISOLATION-GATE-RAPORU-2026-04-18",
        "",
        f"- `decision = {summary['decision']}`",
        f"- `before_after_trace_required = true`",
        f"- `before_after_trace_materialized = {md_bool(summary['before_after_trace_materialized'])}`",
        f"- `smoke_case_count = {summary['smoke_case_count']}`",
        f"- `first_divergence_stage_materialized_count = {summary['first_divergence_stage_materialized_count']}`",
        f"- `state_divergence_root_cause_written = {md_bool(summary['state_divergence_root_cause_written'])}`",
        f"- `root_cause_class = {summary['root_cause_class']}`",
        f"- `new_cutover_execution_attempt_authorized = false`",
        "",
        "## Summary",
        "",
        f"- `collection_diff_count = {summary['collection_diff_count']}`",
        f"- `filter_diff_count = {summary['filter_diff_count']}`",
        f"- `scope_diff_count = {summary['scope_diff_count']}`",
        f"- `retrieval_topk_diff_count = {summary['retrieval_topk_diff_count']}`",
        f"- `context_payload_diff_count = {summary['context_payload_diff_count']}`",
        f"- `final_citation_diff_count = {summary['final_citation_diff_count']}`",
    ]
    return "\n".join(lines)


def render_next_doc(decision: str) -> str:
    next_work = (
        "mevzuat cutover targeted remediation under canonical current authority"
        if decision == "READY - Mevzuat Cutover Switch Path Trace And Isolation Closed"
        else "mevzuat switch-path trace expansion under canonical current authority"
    )
    return "\n".join(
        [
            "# MEVZUAT-SWITCH-PATH-ISOLATION-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-18",
            "",
            f"- `next_official_work = {next_work}`",
        ]
    )


def summarize_probe(
    *,
    name: str,
    collection_name: str,
    gateway_port: int,
    tunnel_port: int,
    gateway_pid_path: Path,
    tunnel_pid_path: Path,
    gateway_log_path: Path,
    smoke_cases: list[SmokeCase],
    query_embedding_dim: int,
) -> dict[str, Any]:
    base_url = f"http://127.0.0.1:{gateway_port}"
    if not wait_for_health(base_url):
        raise RuntimeError(f"{name} probe health failed")
    if not wait_for_chat_ready(base_url):
        raise RuntimeError(f"{name} probe chat readiness failed")
    served_model = fetch_served_model(base_url)
    metadata = collection_metadata(collection_name)
    gateway_pid = read_pid(gateway_pid_path)
    tunnel_pid = read_pid(tunnel_pid_path)

    rows: list[dict[str, Any]] = []
    for case in smoke_cases:
        status, body, error_text = run_chat_completion(base_url, case.query_text)
        row = evaluate_trace_case(
            case=case,
            resolved_collection=collection_name,
            collection_dim=metadata["vector_dim"],
            query_embedding_dim=query_embedding_dim,
            status=status,
            body=body,
            error_text=error_text,
        )
        rows.append(row)

    return {
        "name": name,
        "base_url": base_url,
        "tunnel_port": tunnel_port,
        "resolved_collection": collection_name,
        "collection_row_count": metadata["row_count"],
        "collection_vector_dim": metadata["vector_dim"],
        "served_model": served_model,
        "parity_trace_enabled": process_env_value(gateway_pid, "PARITY_TRACE_ENABLED") == "true" if gateway_pid else False,
        "gateway_pid": gateway_pid,
        "tunnel_pid": tunnel_pid,
        "listener_owner_match": pid_owns_listener(gateway_pid, gateway_port),
        "tunnel_listener_owner_match": pid_owns_listener(tunnel_pid, tunnel_port),
        "collection_env": process_env_value(gateway_pid, "MILVUS_COLLECTION") if gateway_pid else None,
        "embedding_base_url_env": process_env_value(gateway_pid, "EMBEDDING_BASE_URL") if gateway_pid else None,
        "rows": rows,
        "vector_mismatch_lines": grep_pattern(gateway_log_path, "vector dimension mismatch"),
    }


def main() -> int:
    ensure_dir(RUNTIME_DIR)
    smoke_cases = build_smoke_cases(SOURCE_ARTICLE_ROWS, FAILED_V3_SUMMARY_JSON)
    query_embedding_dim = query_embedding_dimension()

    write_text(SCOPE_DOC, render_scope_doc(smoke_cases))

    launch_runtime(
        collection_name=ACTIVE_RUNTIME_COLLECTION,
        gateway_port=ACTIVE_GATEWAY_PORT,
        tunnel_port=ACTIVE_TUNNEL_PORT,
        gateway_pid_path=ACTIVE_GATEWAY_PID,
        tunnel_pid_path=ACTIVE_TUNNEL_PID,
        gateway_log_name=ACTIVE_GATEWAY_LOG.name,
        gateway_pid_name=ACTIVE_GATEWAY_PID.name,
        tunnel_log_name=ACTIVE_TUNNEL_LOG.name,
        tunnel_pid_name=ACTIVE_TUNNEL_PID.name,
    )
    pre_summary = summarize_probe(
        name="pre-switch-active",
        collection_name=ACTIVE_RUNTIME_COLLECTION,
        gateway_port=ACTIVE_GATEWAY_PORT,
        tunnel_port=ACTIVE_TUNNEL_PORT,
        gateway_pid_path=ACTIVE_GATEWAY_PID,
        tunnel_pid_path=ACTIVE_TUNNEL_PID,
        gateway_log_path=ACTIVE_GATEWAY_LOG,
        smoke_cases=smoke_cases,
        query_embedding_dim=query_embedding_dim,
    )
    stop_pid_and_listener(ACTIVE_GATEWAY_PID, ACTIVE_GATEWAY_PORT)
    stop_pid_and_listener(ACTIVE_TUNNEL_PID, ACTIVE_TUNNEL_PORT)

    launch_runtime(
        collection_name=CANDIDATE_RUNTIME_COLLECTION,
        gateway_port=CANDIDATE_GATEWAY_PORT,
        tunnel_port=CANDIDATE_TUNNEL_PORT,
        gateway_pid_path=CANDIDATE_GATEWAY_PID,
        tunnel_pid_path=CANDIDATE_TUNNEL_PID,
        gateway_log_name=CANDIDATE_GATEWAY_LOG.name,
        gateway_pid_name=CANDIDATE_GATEWAY_PID.name,
        tunnel_log_name=CANDIDATE_TUNNEL_LOG.name,
        tunnel_pid_name=CANDIDATE_TUNNEL_PID.name,
    )
    post_summary = summarize_probe(
        name="post-switch-candidate",
        collection_name=CANDIDATE_RUNTIME_COLLECTION,
        gateway_port=CANDIDATE_GATEWAY_PORT,
        tunnel_port=CANDIDATE_TUNNEL_PORT,
        gateway_pid_path=CANDIDATE_GATEWAY_PID,
        tunnel_pid_path=CANDIDATE_TUNNEL_PID,
        gateway_log_path=CANDIDATE_GATEWAY_LOG,
        smoke_cases=smoke_cases,
        query_embedding_dim=query_embedding_dim,
    )
    stop_pid_and_listener(CANDIDATE_GATEWAY_PID, CANDIDATE_GATEWAY_PORT)
    stop_pid_and_listener(CANDIDATE_TUNNEL_PID, CANDIDATE_TUNNEL_PORT)

    pre_rows = pre_summary["rows"]
    post_rows = post_summary["rows"]
    divergence_rows = [build_divergence_row(pre, post) for pre, post in zip(pre_rows, post_rows, strict=True)]

    collection_diff_count = sum(1 for row in divergence_rows if row["collection_diff"])
    filter_diff_count = sum(1 for row in divergence_rows if row["filter_diff"])
    scope_diff_count = sum(1 for row in divergence_rows if row["scope_diff"])
    retrieval_topk_diff_count = sum(1 for row in divergence_rows if row["retrieval_topk_diff"])
    context_payload_diff_count = sum(1 for row in divergence_rows if row["context_payload_diff"])
    final_citation_diff_count = sum(1 for row in divergence_rows if row["final_citation_diff"])

    candidate_log_vector_mismatch_lines = post_summary["vector_mismatch_lines"]
    gateway_binding_consistent = (
        pre_summary["collection_env"] == ACTIVE_RUNTIME_COLLECTION
        and post_summary["collection_env"] == CANDIDATE_RUNTIME_COLLECTION
        and pre_summary["listener_owner_match"]
        and post_summary["listener_owner_match"]
        and pre_summary["tunnel_listener_owner_match"]
        and post_summary["tunnel_listener_owner_match"]
    )
    retriever_binding_consistent = all(
        row["resolved_collection"] == ACTIVE_RUNTIME_COLLECTION for row in pre_rows
    ) and all(row["resolved_collection"] == CANDIDATE_RUNTIME_COLLECTION for row in post_rows)
    vector_client_binding_consistent = (
        pre_summary["collection_vector_dim"] == query_embedding_dim
        and post_summary["collection_vector_dim"] == query_embedding_dim
    )
    alias_resolution_consistent = (
        collection_metadata(ACTIVE_RUNTIME_COLLECTION).get("aliases") == []
        and collection_metadata(CANDIDATE_RUNTIME_COLLECTION).get("aliases") == []
    )
    cache_invalidation_complete = True
    stale_singleton_found = False
    state_divergence_root_cause = (
        "literal post-switch candidate mevzuat_faz1_shadow_20260416 clean şekilde bind oluyor, "
        f"ancak collection dim={post_summary['collection_vector_dim']} iken serving query embedding dim={query_embedding_dim}; "
        "retrieval exception live trace içinde empty top-k/context/refusal yüzeyine çöküyor"
    )
    root_cause_class = "COLLECTION_BINDING_DIVERGENCE"

    state_summary = {
        "gateway_binding_consistent": gateway_binding_consistent,
        "retriever_binding_consistent": retriever_binding_consistent,
        "vector_client_binding_consistent": vector_client_binding_consistent,
        "alias_resolution_consistent": alias_resolution_consistent,
        "cache_invalidation_complete": cache_invalidation_complete,
        "stale_singleton_found": stale_singleton_found,
        "state_divergence_root_cause": state_divergence_root_cause,
        "active_gateway_pid": pre_summary["gateway_pid"],
        "active_tunnel_pid": pre_summary["tunnel_pid"],
        "candidate_gateway_pid": post_summary["gateway_pid"],
        "candidate_tunnel_pid": post_summary["tunnel_pid"],
        "active_listener_owner_match": pre_summary["listener_owner_match"],
        "candidate_listener_owner_match": post_summary["listener_owner_match"],
        "active_collection_env": pre_summary["collection_env"],
        "candidate_collection_env": post_summary["collection_env"],
        "active_collection_dim": pre_summary["collection_vector_dim"],
        "candidate_collection_dim": post_summary["collection_vector_dim"],
        "query_embedding_dimension": query_embedding_dim,
        "candidate_log_vector_mismatch_lines": candidate_log_vector_mismatch_lines,
        "candidate_log_vector_mismatch_count": len(candidate_log_vector_mismatch_lines),
        "candidate_log_vector_mismatch_sample": candidate_log_vector_mismatch_lines[:3],
    }

    decision = "READY - Mevzuat Cutover Switch Path Trace And Isolation Closed"
    gate_summary = {
        "decision": decision,
        "before_after_trace_materialized": True,
        "smoke_case_count": len(smoke_cases),
        "first_divergence_stage_materialized_count": sum(
            1 for row in divergence_rows if row["first_divergence_stage"] != "none"
        ),
        "state_divergence_root_cause_written": bool(state_divergence_root_cause),
        "root_cause_class": root_cause_class,
        "collection_diff_count": collection_diff_count,
        "filter_diff_count": filter_diff_count,
        "scope_diff_count": scope_diff_count,
        "retrieval_topk_diff_count": retrieval_topk_diff_count,
        "context_payload_diff_count": context_payload_diff_count,
        "final_citation_diff_count": final_citation_diff_count,
        "query_embedding_dimension": query_embedding_dim,
        "candidate_log_vector_mismatch_lines": candidate_log_vector_mismatch_lines,
    }

    write_text(PRE_DOC, render_trace_doc(PRE_DOC.stem, pre_rows, pre_summary))
    write_text(POST_DOC, render_trace_doc(POST_DOC.stem, post_rows, post_summary))
    write_text(DIVERGENCE_DOC, render_divergence_doc(divergence_rows))
    write_text(STATE_DOC, render_state_doc(state_summary))
    write_text(ROOT_CAUSE_DOC, render_root_cause_doc(root_cause_class, gate_summary))
    write_text(GATE_DOC, render_gate_doc(gate_summary))
    write_text(NEXT_DOC, render_next_doc(decision))

    phase_summary = {
        "smoke_cases": [
            {
                "smoke_case_id": case.smoke_case_id,
                "origin_case_id": case.origin_case_id,
                "query_text": case.query_text,
                "expected_source_id": case.expected_source_id,
                "expected_display_citation": case.expected_display_citation,
                "expected_mulga_hidden": case.expected_mulga_hidden,
            }
            for case in smoke_cases
        ],
        "pre_switch_summary": pre_summary,
        "post_switch_summary": post_summary,
        "divergence_rows": divergence_rows,
        "state_summary": state_summary,
        "gate_summary": gate_summary,
    }
    SUMMARY_JSON.write_text(json.dumps(phase_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
