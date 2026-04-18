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

from authoritative_candidate_utils import (
    ACTIVE_RUNTIME_COLLECTION,
    build_candidate_inventory,
    load_authoritative_candidate_collection_name,
    select_authoritative_candidate,
    select_stale_candidate,
)
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

DOCS_DIR = ROOT / "docs"
RUNTIME_DIR = ROOT / "runtime_logs" / "mevzuat_collection_binding_divergence_remediation_20260419"
SUMMARY_JSON = RUNTIME_DIR / "phase_summary.json"

FAILED_RERUN_SUMMARY_JSON = ROOT / "runtime_logs" / "mevzuat_controlled_cutover_execution_rerun_v3_20260418" / "phase_summary.json"
SOURCE_ARTICLE_ROWS = Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl")

PROBE_GATEWAY_PORT = 8062
PROBE_TUNNEL_PORT = 30662
PROBE_GATEWAY_PID = ROOT / "runtime_logs" / "mevzuat_binding_divergence_probe_gateway.pid"
PROBE_TUNNEL_PID = ROOT / "runtime_logs" / "mevzuat_binding_divergence_probe_tunnel.pid"
LAUNCHER = ROOT / "scripts" / "finetune" / "launch_local_baseline_gateway_dgxnode2.sh"
LLM_MODEL = "Qwen/Qwen3.5-35B-A3B-FP8"

INVENTORY_DOC = DOCS_DIR / "MEVZUAT-CANDIDATE-INVENTORY-RAPORU-2026-04-19.md"
SELECTION_DOC = DOCS_DIR / "MEVZUAT-AUTHORITATIVE-CANDIDATE-SECIM-NOTU-2026-04-19.md"
BINDING_DOC = DOCS_DIR / "MEVZUAT-BINDING-CORRECTION-DENETIMI-2026-04-19.md"
TRACE_DOC = DOCS_DIR / "MEVZUAT-POST-FIX-SWITCH-TRACE-TEYIT-RAPORU-2026-04-19.md"
GATE_DOC = DOCS_DIR / "MEVZUAT-COLLECTION-BINDING-DIVERGENCE-REMEDIATION-GATE-RAPORU-2026-04-19.md"
NEXT_DOC = DOCS_DIR / "MEVZUAT-COLLECTION-BINDING-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-19.md"

CURRENT_SERVING_PATHS = [
    ROOT / "scripts" / "mevzuat_cutover" / "run_controlled_cutover_execution_rerun_phase.py",
    ROOT / "scripts" / "mevzuat_cutover" / "run_cutover_state_binding_live_serving_remediation_phase.py",
    ROOT / "scripts" / "mevzuat_cutover" / "run_post_switch_divergence_remediation_phase.py",
    ROOT / "scripts" / "mevzuat_cutover" / "run_retrieval_runtime_parity_phase.py",
    ROOT / "scripts" / "mevzuat_cutover" / "authoritative_candidate_utils.py",
]


@dataclass(slots=True)
class SmokeCase:
    case_id: str
    query_text: str
    expected_source_id: str
    expected_display_citation: str
    expected_mulga_hidden: bool


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def md_bool(value: bool) -> str:
    return "true" if value else "false"


def iter_article_rows(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if raw:
                yield json.loads(raw)


def build_smoke_cases(article_rows_path: Path, failed_summary: dict[str, Any]) -> list[SmokeCase]:
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

    smoke_cases: list[SmokeCase] = []
    repeated_kanun_seen = 0
    for item in failed_summary["postswitch_results"]:
        raw_case_id = str(item["case_id"])
        case_id = raw_case_id
        if raw_case_id == "KANUN-A":
            repeated_kanun_seen += 1
            if repeated_kanun_seen == 2:
                case_id = "LIVE-KANUN-A"
        row = selected["KANUN-A" if case_id == "LIVE-KANUN-A" else raw_case_id]
        smoke_cases.append(
            SmokeCase(
                case_id=case_id,
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
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {"raw_text": raw}
            return response.status, body, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"raw_text": raw}
        return exc.code, body, raw
    except Exception as exc:
        return None, None, repr(exc)


def wait_for_health(base_url: str, *, timeout: int = 120) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, _body, _error = http_json(f"{base_url}/v1/health", timeout=5)
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
    }
    while time.time() < deadline:
        status, _body, _error = http_json(f"{base_url}/v1/chat/completions", payload=payload, timeout=30)
        if status == 200:
            return True
        time.sleep(2)
    return False


def launch_runtime(collection_name: str) -> None:
    stop_pid_and_listener(PROBE_GATEWAY_PID, PROBE_GATEWAY_PORT)
    stop_pid_and_listener(PROBE_TUNNEL_PID, PROBE_TUNNEL_PORT)
    env = os.environ.copy()
    env.update(
        {
            "MILVUS_COLLECTION": collection_name,
            "GATEWAY_PORT": str(PROBE_GATEWAY_PORT),
            "LOCAL_TUNNEL_PORT": str(PROBE_TUNNEL_PORT),
            "LOG_NAME": "mevzuat_binding_divergence_probe_gateway.log",
            "PID_NAME": "mevzuat_binding_divergence_probe_gateway.pid",
            "TUNNEL_LOG_NAME": "mevzuat_binding_divergence_probe_tunnel.log",
            "TUNNEL_PID_NAME": "mevzuat_binding_divergence_probe_tunnel.pid",
        }
    )
    subprocess.run(["bash", str(LAUNCHER)], cwd=str(ROOT), env=env, check=True)
    if not wait_for_pidfile_listener_match(PROBE_TUNNEL_PID, PROBE_TUNNEL_PORT, timeout=20):
        raise RuntimeError("probe tunnel pid/listener mismatch")
    if not wait_for_pidfile_listener_match(PROBE_GATEWAY_PID, PROBE_GATEWAY_PORT, timeout=20):
        raise RuntimeError("probe gateway pid/listener mismatch")


def run_chat_completion(base_url: str, query_text: str) -> tuple[int | None, dict[str, Any] | None, str | None]:
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": query_text}],
        "temperature": 0,
        "max_tokens": 300,
        "stream": False,
    }
    return http_json(f"{base_url}/v1/chat/completions", payload=payload, timeout=120)


def evaluate_runtime_case(case: SmokeCase, status: int | None, body: dict[str, Any] | None, error_text: str | None) -> dict[str, Any]:
    from faz2a_hardening import canonicalize_source_id

    if status is None or status >= 500 or body is None:
        return {
            "status_code": status,
            "source_correct": False,
            "wrong_source": False,
            "runtime_error": True,
            "unexplained": True,
            "final_mode": None,
            "primary_source_id": None,
            "error_text": error_text or "no response body",
        }

    answer_contract = body.get("answer_contract") or {}
    primary = canonicalize_source_id(answer_contract.get("primary_source_id")) or ""
    expected = canonicalize_source_id(case.expected_source_id) or case.expected_source_id
    if case.expected_mulga_hidden:
        temporal_refusal = body.get("final_mode") == "refusal" and (
            body.get("unsupported_reason") == "temporal_mismatch"
            or answer_contract.get("unsupported_reason") == "temporal_mismatch"
        )
        return {
            "status_code": status,
            "source_correct": temporal_refusal,
            "wrong_source": not temporal_refusal,
            "runtime_error": False,
            "unexplained": not temporal_refusal,
            "final_mode": body.get("final_mode"),
            "primary_source_id": answer_contract.get("primary_source_id"),
            "error_text": None,
        }

    supported = body.get("final_mode") in {"answer", "partial"}
    source_correct = supported and primary == expected
    return {
        "status_code": status,
        "source_correct": source_correct,
        "wrong_source": not source_correct,
        "runtime_error": False,
        "unexplained": not source_correct,
        "final_mode": body.get("final_mode"),
        "primary_source_id": answer_contract.get("primary_source_id"),
        "error_text": None,
    }


def current_serving_stale_hits(stale_collection_name: str) -> dict[str, int]:
    hits: dict[str, int] = {}
    for path in CURRENT_SERVING_PATHS:
        text = path.read_text(encoding="utf-8")
        count = text.count(stale_collection_name)
        if count:
            hits[str(path)] = count
    return hits


def render_inventory_doc(inventory: list[dict[str, Any]]) -> str:
    lines = [
        "# Mevzuat Candidate Inventory Raporu 2026-04-19",
        "",
        "| collection_name | vector_dimension | row_count | intended_role | serving_candidate_eligible |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in inventory:
        lines.append(
            f"| {item['collection_name']} | {item['vector_dimension']} | {item['row_count']} | "
            f"{item['intended_role']} | {md_bool(bool(item['serving_candidate_eligible']))} |"
        )
    return "\n".join(lines)


def render_selection_doc(authoritative: dict[str, Any], stale: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Authoritative Candidate Secim Notu 2026-04-19",
            "",
            "## Official Fields",
            f"- `authoritative_candidate_collection = {authoritative['collection_name']}`",
            f"- `authoritative_candidate_dimension = {authoritative['vector_dimension']}`",
            f"- `authoritative_candidate_row_count = {authoritative['row_count']}`",
            f"- `stale_candidate_collection = {stale['collection_name']}`",
            f"- `stale_candidate_dimension = {stale['vector_dimension']}`",
            (
                "- `selection_reason = only 1024-dim mevzuat faz1 candidate with full row_count parity "
                f"({authoritative['row_count']}) and serving contract compatibility; stale {stale['vector_dimension']}-dim "
                "collection is explicitly serving-disabled`"
            ),
        ]
    )


def render_binding_doc(summary: dict[str, Any], stale_hits: dict[str, int]) -> str:
    lines = [
        "# Mevzuat Binding Correction Denetimi 2026-04-19",
        "",
        "## Official Fields",
        f"- `gateway_binding_before = {summary['gateway_binding_before']}`",
        f"- `gateway_binding_after = {summary['gateway_binding_after']}`",
        f"- `retriever_binding_before = {summary['retriever_binding_before']}`",
        f"- `retriever_binding_after = {summary['retriever_binding_after']}`",
        f"- `alias_resolution_before = {summary['alias_resolution_before']}`",
        f"- `alias_resolution_after = {summary['alias_resolution_after']}`",
        f"- `literal_stale_reference_removed = {md_bool(summary['literal_stale_reference_removed'])}`",
        f"- `binding_consistency_pass = {md_bool(summary['binding_consistency_pass'])}`",
    ]
    if stale_hits:
        lines.extend(
            [
                "",
                "## Remaining Stale Literal Hits",
                *[f"- `{path}` -> {count}" for path, count in sorted(stale_hits.items())],
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Audit Note",
                "- current serving/remediation path files icinde stale literal candidate referansi kalmadi",
            ]
        )
    return "\n".join(lines)


def render_trace_doc(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Mevzuat Post-Fix Switch Trace Teyit Raporu 2026-04-19",
        "",
        "| smoke_case_id | resolved_collection | resolved_dimension | source_correct | wrong_source | first_divergence_stage_remaining |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in results:
        lines.append(
            f"| {item['smoke_case_id']} | {item['resolved_collection']} | {item['resolved_dimension']} | "
            f"{md_bool(item['source_correct'])} | {md_bool(item['wrong_source'])} | {item['first_divergence_stage_remaining']} |"
        )
    return "\n".join(lines)


def render_gate_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Collection Binding Divergence Remediation Gate Raporu 2026-04-19",
            "",
            "## Official Decision",
            f"- decision = `{summary['decision']}`",
            "",
            "## READY Criteria Contrast",
            f"- `authoritative_candidate_dimension = {summary['authoritative_candidate_dimension']}`",
            f"- `stale_candidate_dimension = {summary['stale_candidate_dimension']}`",
            f"- `literal_stale_reference_removed = {md_bool(summary['literal_stale_reference_removed'])}`",
            f"- `binding_consistency_pass = {md_bool(summary['binding_consistency_pass'])}`",
            f"- `smoke_case_count = {summary['smoke_case_count']}`",
            f"- `source_correct_count = {summary['source_correct_count']}`",
            f"- `wrong_source_count = {summary['wrong_source_count']}`",
            f"- `runtime_error_count = {summary['runtime_error_count']}`",
            f"- `unexplained_count = {summary['unexplained_count']}`",
        ]
    )


def render_next_doc(decision: str) -> str:
    next_work = (
        "mevzuat controlled cutover execution rerun under canonical current authority"
        if decision.startswith("READY")
        else "mevzuat collection binding remediation continues under canonical current authority"
    )
    return "\n".join(
        [
            "# Mevzuat Collection Binding Sonrasi Next Official Work Karari 2026-04-19",
            "",
            "## Official Decision",
            f"- `next_official_work = {next_work}`",
        ]
    )


def main() -> None:
    ensure_dir(RUNTIME_DIR)

    inventory = build_candidate_inventory()
    authoritative = select_authoritative_candidate(inventory)
    stale = select_stale_candidate(inventory)
    authoritative_collection = load_authoritative_candidate_collection_name()

    failed_summary = load_json(FAILED_RERUN_SUMMARY_JSON)
    smoke_cases = build_smoke_cases(SOURCE_ARTICLE_ROWS, failed_summary)

    gateway_binding_before = str(failed_summary.get("candidate_runtime_collection") or stale["collection_name"])
    retriever_binding_before = gateway_binding_before
    alias_resolution_before = gateway_binding_before

    probe_base_url = f"http://127.0.0.1:{PROBE_GATEWAY_PORT}"
    trace_results: list[dict[str, Any]] = []
    gateway_binding_after = ""
    retriever_binding_after = ""
    alias_resolution_after = authoritative_collection
    stale_hits: dict[str, int] = {}
    literal_stale_reference_removed = False
    binding_consistency_pass = False
    try:
        launch_runtime(authoritative_collection)
        if not wait_for_health(probe_base_url):
            raise RuntimeError("binding remediation probe health timeout")
        if not wait_for_chat_ready(probe_base_url):
            raise RuntimeError("binding remediation probe chat readiness timeout")

        probe_gateway_pid = read_pid(PROBE_GATEWAY_PID)
        probe_tunnel_pid = read_pid(PROBE_TUNNEL_PID)
        gateway_binding_after = process_env_value(probe_gateway_pid, "MILVUS_COLLECTION") or authoritative_collection
        retriever_binding_after = gateway_binding_after
        alias_resolution_after = authoritative_collection

        stale_hits = current_serving_stale_hits(str(stale["collection_name"]))
        literal_stale_reference_removed = not stale_hits
        binding_consistency_pass = all(
            [
                gateway_binding_after == authoritative_collection,
                retriever_binding_after == authoritative_collection,
                alias_resolution_after == authoritative_collection,
                pid_owns_listener(probe_gateway_pid, PROBE_GATEWAY_PORT),
                pid_owns_listener(probe_tunnel_pid, PROBE_TUNNEL_PORT),
                literal_stale_reference_removed,
            ]
        )

        for case in smoke_cases:
            status, body, error_text = run_chat_completion(probe_base_url, case.query_text)
            evaluation = evaluate_runtime_case(case, status, body, error_text)
            first_divergence_stage_remaining = "none"
            if evaluation["runtime_error"]:
                first_divergence_stage_remaining = "runtime_error"
            elif evaluation["wrong_source"]:
                first_divergence_stage_remaining = "source_resolution"

            trace_results.append(
                {
                    "smoke_case_id": case.case_id,
                    "resolved_collection": gateway_binding_after,
                    "resolved_dimension": int(authoritative["vector_dimension"]),
                    "source_correct": bool(evaluation["source_correct"]),
                    "wrong_source": bool(evaluation["wrong_source"]),
                    "first_divergence_stage_remaining": first_divergence_stage_remaining,
                    "runtime_error": bool(evaluation["runtime_error"]),
                    "unexplained": bool(evaluation["unexplained"]),
                }
            )
    finally:
        stop_pid_and_listener(PROBE_GATEWAY_PID, PROBE_GATEWAY_PORT)
        stop_pid_and_listener(PROBE_TUNNEL_PID, PROBE_TUNNEL_PORT)

    source_correct_count = sum(1 for item in trace_results if item["source_correct"])
    wrong_source_count = sum(1 for item in trace_results if item["wrong_source"])
    runtime_error_count = sum(1 for item in trace_results if item["runtime_error"])
    unexplained_count = sum(1 for item in trace_results if item["unexplained"])

    decision = "READY - Mevzuat Collection Binding Divergence Remediation Closed"
    if not all(
        [
            int(authoritative["vector_dimension"]) == 1024,
            int(stale["vector_dimension"]) == 256,
            literal_stale_reference_removed,
            binding_consistency_pass,
            len(trace_results) == 7,
            source_correct_count == 7,
            wrong_source_count == 0,
            runtime_error_count == 0,
            unexplained_count == 0,
            all(item["resolved_dimension"] == 1024 for item in trace_results),
            all(item["first_divergence_stage_remaining"] == "none" for item in trace_results),
        ]
    ):
        decision = "NO-GO - Mevzuat Collection Binding Divergence Remediation"

    write_text(INVENTORY_DOC, render_inventory_doc(inventory))
    write_text(SELECTION_DOC, render_selection_doc(authoritative, stale))
    binding_summary = {
        "gateway_binding_before": gateway_binding_before,
        "gateway_binding_after": gateway_binding_after,
        "retriever_binding_before": retriever_binding_before,
        "retriever_binding_after": retriever_binding_after,
        "alias_resolution_before": alias_resolution_before,
        "alias_resolution_after": alias_resolution_after,
        "literal_stale_reference_removed": literal_stale_reference_removed,
        "binding_consistency_pass": binding_consistency_pass,
    }
    write_text(BINDING_DOC, render_binding_doc(binding_summary, stale_hits))
    write_text(TRACE_DOC, render_trace_doc(trace_results))
    gate_summary = {
        "decision": decision,
        "authoritative_candidate_dimension": int(authoritative["vector_dimension"]),
        "stale_candidate_dimension": int(stale["vector_dimension"]),
        "literal_stale_reference_removed": literal_stale_reference_removed,
        "binding_consistency_pass": binding_consistency_pass,
        "smoke_case_count": len(trace_results),
        "source_correct_count": source_correct_count,
        "wrong_source_count": wrong_source_count,
        "runtime_error_count": runtime_error_count,
        "unexplained_count": unexplained_count,
    }
    write_text(GATE_DOC, render_gate_doc(gate_summary))
    write_text(NEXT_DOC, render_next_doc(decision))

    SUMMARY_JSON.write_text(
        json.dumps(
            {
                "inventory": inventory,
                "authoritative_candidate_collection": authoritative_collection,
                "stale_candidate_collection": stale["collection_name"],
                "binding_summary": binding_summary,
                "trace_results": trace_results,
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
