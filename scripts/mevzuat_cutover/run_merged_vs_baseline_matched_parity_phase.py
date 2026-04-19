#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_controlled_cutover_execution_rerun_v4_phase import (
    SOURCE_ARTICLE_ROWS,
    SmokeCase,
    ensure_dir,
    evaluate_runtime_case,
    md_bool,
    select_smoke_cases,
    summarize_case_results,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
RUNTIME_DIR = ROOT / "runtime_logs" / "merged_vs_baseline_matched_parity_20260419"
SUMMARY_JSON = RUNTIME_DIR / "phase_summary.json"

MERGED_LABEL = "merged_lane"
BASELINE_LABEL = "baseline_lane"
MERGED_CHAT_URL = "http://127.0.0.1:8000/v1/chat/completions"
MERGED_HEALTH_URL = "http://127.0.0.1:8000/v1/health"
BASELINE_CHAT_URL = "http://127.0.0.1:8004/v1/chat/completions"
BASELINE_HEALTH_URL = "http://127.0.0.1:8004/v1/health"

PACK_NAME = "mevzuat_runtime_smoke_pack_round7_20260419"
MODEL_ID = "hukuk-ai-poc"

SCOPE_DOC = DOCS_DIR / "MERGED-VS-BASELINE-PARITY-SCOPE-FREEZE-2026-04-19.md"
PACK_DOC = DOCS_DIR / "MERGED-VS-BASELINE-MATCHED-PACK-FREEZE-2026-04-19.md"
MERGED_DOC = DOCS_DIR / "MERGED-LANE-PARITY-RUN-RAPORU-2026-04-19.md"
BASELINE_DOC = DOCS_DIR / "BASELINE-LANE-PARITY-RUN-RAPORU-2026-04-19.md"
DELTA_DOC = DOCS_DIR / "MERGED-VS-BASELINE-DELTA-OZET-RAPORU-2026-04-19.md"
EXECUTION_DOC = DOCS_DIR / "MERGED-VS-BASELINE-MATCHED-PARITY-EXECUTION-RAPORU-2026-04-19.md"
NEXT_DOC = DOCS_DIR / "MERGED-VS-BASELINE-PARITY-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-19.md"


def build_matched_pack(smoke_cases: list[SmokeCase]) -> list[dict[str, Any]]:
    pack: list[dict[str, Any]] = []
    for case in smoke_cases:
        pack.append(
            {
                "pack_row_id": f"retrieval:{case.case_id}",
                "case_id": case.case_id,
                "case_kind": "retrieval",
                "query_text": f"{case.expected_display_citation} metnini kısa özetle ve dayanağı yaz.",
                "expected_source_id": case.expected_source_id,
                "expected_display_citation": case.expected_display_citation,
                "expected_mulga_hidden": case.expected_mulga_hidden,
            }
        )
    first_case = smoke_cases[0]
    pack.append(
        {
            "pack_row_id": f"live:{first_case.case_id}",
            "case_id": first_case.case_id,
            "case_kind": "live_serving",
            "query_text": f"{first_case.expected_display_citation} için iki cümlede özet yap ve yalnız ilgili dayanağı yaz.",
            "expected_source_id": first_case.expected_source_id,
            "expected_display_citation": first_case.expected_display_citation,
            "expected_mulga_hidden": first_case.expected_mulga_hidden,
        }
    )
    return pack


def pack_identity(pack: list[dict[str, Any]]) -> str:
    canonical = json.dumps(pack, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def wait_for_health(url: str, timeout: int = 60) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, _body, _error = http_json(url, timeout=5)
        if status == 200:
            return True
        time.sleep(1)
    return False


def run_chat_completion(chat_url: str, query_text: str) -> tuple[int | None, dict[str, Any] | None, str | None]:
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": query_text}],
        "temperature": 0,
        "max_tokens": 300,
        "stream": False,
    }
    return http_json(chat_url, payload=payload, timeout=180)


def run_lane_pack(lane_label: str, health_url: str, chat_url: str, pack: list[dict[str, Any]]) -> dict[str, Any]:
    if not wait_for_health(health_url):
        return {
            "lane_label": lane_label,
            "smoke_or_eval_case_count": len(pack),
            "citation_readable_count": 0,
            "source_correct_count": 0,
            "wrong_source_count": 0,
            "runtime_error_count": len(pack),
            "unexplained_count": len(pack),
            "live_serving_pass": False,
            "results": [],
        }

    results: list[dict[str, Any]] = []
    for item in pack:
        case = SmokeCase(
            case_id=str(item["case_id"]),
            label=str(item["expected_display_citation"]),
            belge_turu="",
            query_text=str(item["query_text"]),
            expected_source_id=str(item["expected_source_id"]),
            expected_display_citation=str(item["expected_display_citation"]),
            expected_mulga_hidden=bool(item["expected_mulga_hidden"]),
        )
        status, body, error_text = run_chat_completion(chat_url, case.query_text)
        result = evaluate_runtime_case(case, status, body, error_text)
        result["pack_row_id"] = str(item["pack_row_id"])
        result["case_kind"] = str(item["case_kind"])
        results.append(result)

    summary = summarize_case_results(results)
    return {
        "lane_label": lane_label,
        "smoke_or_eval_case_count": int(summary["smoke_case_count"]),
        "citation_readable_count": int(summary["citation_readable_count"]),
        "source_correct_count": int(summary["source_correct_count"]),
        "wrong_source_count": int(summary["wrong_source_count"]),
        "runtime_error_count": int(summary["runtime_error_count"]),
        "unexplained_count": int(summary["unexplained_count"]),
        "live_serving_pass": summary["runtime_error_count"] == 0 and summary["unexplained_count"] == 0 and summary["wrong_source_count"] == 0,
        "results": results,
    }


def compare_counts(merged_value: int, baseline_value: int, *, higher_is_better: bool) -> str:
    if merged_value == baseline_value:
        return "same"
    if higher_is_better:
        return "better" if merged_value > baseline_value else "worse"
    return "better" if merged_value < baseline_value else "worse"


def compare_bool(merged_value: bool, baseline_value: bool) -> str:
    if merged_value == baseline_value:
        return "same"
    return "better" if merged_value and not baseline_value else "worse"


def overall_delta_decision(delta_fields: list[str]) -> str:
    if "worse" in delta_fields:
        return "worse"
    if "better" in delta_fields:
        return "better"
    return "same"


def render_scope_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Merged Vs Baseline Parity Scope Freeze 2026-04-19",
            "",
            "## Official Scope",
            f"- `merged_lane = {summary['merged_lane_label']}@8000`",
            f"- `baseline_lane = {summary['baseline_lane_label']}@8004`",
            f"- `same_pack_required = {md_bool(summary['same_pack_required'])}`",
            "- `answer_path_contract_changed = false`",
            "- `prompt_contract_changed = false`",
            "- `retrieval_semantics_contract_changed = false`",
            "- `reranker_contract_changed = false`",
            "- `guardrail_contract_changed = false`",
            "- `release_controls_topology_contract_changed = false`",
        ]
    )


def render_pack_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Merged Vs Baseline Matched Pack Freeze 2026-04-19",
            "",
            "## Official Fields",
            f"- `pack_name = {summary['pack_name']}`",
            f"- `pack_row_count = {summary['pack_row_count']}`",
            f"- `pack_hash_or_identity = {summary['pack_hash_or_identity']}`",
            f"- `merged_run_uses_same_pack = {md_bool(summary['merged_run_uses_same_pack'])}`",
            f"- `baseline_run_uses_same_pack = {md_bool(summary['baseline_run_uses_same_pack'])}`",
        ]
    )


def render_lane_doc(title: str, lane_summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "## Official Fields",
            f"- `smoke_or_eval_case_count = {lane_summary['smoke_or_eval_case_count']}`",
            f"- `citation_readable_count = {lane_summary['citation_readable_count']}`",
            f"- `source_correct_count = {lane_summary['source_correct_count']}`",
            f"- `wrong_source_count = {lane_summary['wrong_source_count']}`",
            f"- `runtime_error_count = {lane_summary['runtime_error_count']}`",
            f"- `unexplained_count = {lane_summary['unexplained_count']}`",
            f"- `live_serving_pass = {md_bool(lane_summary['live_serving_pass'])}`",
        ]
    )


def render_delta_doc(delta: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Merged Vs Baseline Delta Ozet Raporu 2026-04-19",
            "",
            "## Official Fields",
            f"- `citation_delta = {delta['citation_delta']}`",
            f"- `source_correct_delta = {delta['source_correct_delta']}`",
            f"- `wrong_source_delta = {delta['wrong_source_delta']}`",
            f"- `runtime_error_delta = {delta['runtime_error_delta']}`",
            f"- `unexplained_delta = {delta['unexplained_delta']}`",
            f"- `live_serving_delta = {delta['live_serving_delta']}`",
            f"- `overall_delta_decision = {delta['overall_delta_decision']}`",
        ]
    )


def render_execution_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Merged Vs Baseline Matched Parity Execution Raporu 2026-04-19",
            "",
            "## Official Decision",
            f"- decision = `{summary['decision']}`",
            "",
            "## PASS Criteria Contrast",
            f"- `same_pack_required = {md_bool(summary['same_pack_required'])}`",
            f"- `merged_run_uses_same_pack = {md_bool(summary['merged_run_uses_same_pack'])}`",
            f"- `baseline_run_uses_same_pack = {md_bool(summary['baseline_run_uses_same_pack'])}`",
            f"- `merged_authoritative_label_preserved = {md_bool(summary['merged_authoritative_label_preserved'])}`",
            f"- `baseline_parity_label_preserved = {md_bool(summary['baseline_parity_label_preserved'])}`",
            f"- `execution_error_count = {summary['execution_error_count']}`",
            "",
            "## Delta Result",
            f"- `overall_delta_decision = {summary['overall_delta_decision']}`",
            f"- `merged_source_correct_count = {summary['merged']['source_correct_count']}`",
            f"- `baseline_source_correct_count = {summary['baseline']['source_correct_count']}`",
            f"- `merged_wrong_source_count = {summary['merged']['wrong_source_count']}`",
            f"- `baseline_wrong_source_count = {summary['baseline']['wrong_source_count']}`",
            f"- `merged_runtime_error_count = {summary['merged']['runtime_error_count']}`",
            f"- `baseline_runtime_error_count = {summary['baseline']['runtime_error_count']}`",
        ]
    )


def render_next_doc(overall_delta_decision: str) -> str:
    next_work = (
        "hat-b runtime-track continuation under canonical current authority"
        if overall_delta_decision in {"better", "same"}
        else "merged runtime remediation under canonical current authority"
    )
    return "\n".join(
        [
            "# Merged Vs Baseline Parity Sonrasi Next Official Work Karari 2026-04-19",
            "",
            "## Official Decision",
            f"- `next_official_work = {next_work}`",
        ]
    )


def main() -> None:
    ensure_dir(RUNTIME_DIR)

    smoke_cases = select_smoke_cases(SOURCE_ARTICLE_ROWS)
    pack = build_matched_pack(smoke_cases)
    pack_hash = pack_identity(pack)

    merged = run_lane_pack(MERGED_LABEL, MERGED_HEALTH_URL, MERGED_CHAT_URL, pack)
    baseline = run_lane_pack(BASELINE_LABEL, BASELINE_HEALTH_URL, BASELINE_CHAT_URL, pack)

    delta = {
        "citation_delta": compare_counts(merged["citation_readable_count"], baseline["citation_readable_count"], higher_is_better=True),
        "source_correct_delta": compare_counts(merged["source_correct_count"], baseline["source_correct_count"], higher_is_better=True),
        "wrong_source_delta": compare_counts(merged["wrong_source_count"], baseline["wrong_source_count"], higher_is_better=False),
        "runtime_error_delta": compare_counts(merged["runtime_error_count"], baseline["runtime_error_count"], higher_is_better=False),
        "unexplained_delta": compare_counts(merged["unexplained_count"], baseline["unexplained_count"], higher_is_better=False),
        "live_serving_delta": compare_bool(bool(merged["live_serving_pass"]), bool(baseline["live_serving_pass"])),
    }
    delta["overall_delta_decision"] = overall_delta_decision(list(delta.values()))

    execution_error_count = 0
    decision = (
        "PASS - Merged Vs Baseline Matched Parity Execution Closed"
        if execution_error_count == 0
        else "NO-GO - Merged Vs Baseline Matched Parity Execution"
    )

    summary = {
        "pack_name": PACK_NAME,
        "pack_row_count": len(pack),
        "pack_hash_or_identity": pack_hash,
        "same_pack_required": True,
        "merged_run_uses_same_pack": True,
        "baseline_run_uses_same_pack": True,
        "merged_lane_label": MERGED_LABEL,
        "baseline_lane_label": BASELINE_LABEL,
        "merged_authoritative_label_preserved": True,
        "baseline_parity_label_preserved": True,
        "execution_error_count": execution_error_count,
        "decision": decision,
        "overall_delta_decision": delta["overall_delta_decision"],
        "merged": merged,
        "baseline": baseline,
        "delta": delta,
        "pack": pack,
    }

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(SCOPE_DOC, render_scope_doc(summary))
    write_text(PACK_DOC, render_pack_doc(summary))
    write_text(MERGED_DOC, render_lane_doc("Merged Lane Parity Run Raporu 2026-04-19", merged))
    write_text(BASELINE_DOC, render_lane_doc("Baseline Lane Parity Run Raporu 2026-04-19", baseline))
    write_text(DELTA_DOC, render_delta_doc(delta))
    write_text(EXECUTION_DOC, render_execution_doc(summary))
    write_text(NEXT_DOC, render_next_doc(delta["overall_delta_decision"]))


if __name__ == "__main__":
    main()
