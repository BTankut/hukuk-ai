#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from authoritative_candidate_utils import load_authoritative_candidate_collection_name
from run_controlled_cutover_execution_rerun_v4_phase import (
    SOURCE_ARTICLE_ROWS,
    collection_entity_count,
    current_bound_collection,
    ensure_dir,
    evaluate_runtime_case,
    md_bool,
    run_chat_completion,
    select_smoke_cases,
    summarize_case_results,
    wait_for_chat_ready,
    wait_for_health,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
RUNTIME_DIR = ROOT / "runtime_logs" / "mevzuat_post_cutover_stabilization_20260419"
SUMMARY_JSON = RUNTIME_DIR / "phase_summary.json"
PREVIOUS_SUMMARY_JSON = ROOT / "runtime_logs" / "mevzuat_controlled_cutover_execution_rerun_v4_20260419" / "phase_summary.json"

ACTIVE_RUNTIME_COLLECTION = load_authoritative_candidate_collection_name()
DEFAULT_ROLLBACK_TARGET = "mevzuat_e5_shadow"
SMOKE_ROUND_COUNT = 2
STABILIZATION_WINDOW_SLEEP_SECONDS = 5

ACTIVE_FREEZE_DOC = DOCS_DIR / "MEVZUAT-POST-CUTOVER-ACTIVE-RUNTIME-FREEZE-RAPORU-2026-04-19.md"
WINDOW_DOC = DOCS_DIR / "MEVZUAT-POST-CUTOVER-STABILIZATION-WINDOW-DOGRULAMA-RAPORU-2026-04-19.md"
SMOKE_DOC = DOCS_DIR / "MEVZUAT-POST-CUTOVER-RUNTIME-SMOKE-DOGRULAMA-RAPORU-2026-04-19.md"
ROLLBACK_DOC = DOCS_DIR / "MEVZUAT-POST-CUTOVER-ROLLBACK-HAZIRLIK-SUREKLILIK-NOTU-2026-04-19.md"
GATE_DOC = DOCS_DIR / "MEVZUAT-POST-CUTOVER-STABILIZATION-GATE-RAPORU-2026-04-19.md"
NEXT_DOC = DOCS_DIR / "MEVZUAT-POST-CUTOVER-STABILIZATION-SONRASI-NEXT-OFFICIAL-WORK-KARARI-2026-04-19.md"


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_prior_cutover_targets() -> dict[str, Any]:
    data = {
        "rollback_target": DEFAULT_ROLLBACK_TARGET,
        "backout_target": DEFAULT_ROLLBACK_TARGET,
        "operator_execution_order_preserved": True,
    }
    if not PREVIOUS_SUMMARY_JSON.exists():
        return data
    try:
        previous = json.loads(PREVIOUS_SUMMARY_JSON.read_text(encoding="utf-8"))
    except Exception:
        return data
    data["rollback_target"] = previous.get("rollback_target", DEFAULT_ROLLBACK_TARGET)
    data["backout_target"] = previous.get("backout_target", DEFAULT_ROLLBACK_TARGET)
    data["operator_execution_order_preserved"] = previous.get("operator_execution_order_preserved", True)
    return data


def run_smoke_round(round_name: str, smoke_cases: list[Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in smoke_cases:
        query_text = f"{case.expected_display_citation} metnini kısa özetle ve dayanağı yaz."
        status, body, error_text = run_chat_completion(query_text)
        result = evaluate_runtime_case(case, status, body, error_text)
        result["smoke_round"] = round_name
        result["smoke_key"] = f"retrieval:{case.case_id}"
        results.append(result)

    live_case = smoke_cases[0]
    live_query = f"{live_case.expected_display_citation} için iki cümlede özet yap ve yalnız ilgili dayanağı yaz."
    status, body, error_text = run_chat_completion(live_query)
    live_result = evaluate_runtime_case(live_case, status, body, error_text)
    live_result["smoke_round"] = round_name
    live_result["smoke_key"] = f"live:{live_case.case_id}"
    results.append(live_result)
    return results


def compute_observed_regression_count(
    immediate_results: list[dict[str, Any]],
    stabilization_results: list[dict[str, Any]],
) -> int:
    immediate_map = {item["smoke_key"]: item for item in immediate_results}
    stabilization_map = {item["smoke_key"]: item for item in stabilization_results}
    regressions = 0
    for smoke_key, immediate in immediate_map.items():
        later = stabilization_map.get(smoke_key)
        if later is None:
            regressions += 1
            continue
        if immediate["case_result"] == "PASS" and later["case_result"] != "PASS":
            regressions += 1
    return regressions


def render_active_freeze_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Post-Cutover Active Runtime Freeze Raporu 2026-04-19",
            "",
            "## Official Fields",
            f"- `active_runtime_collection = {summary['active_runtime_collection']}`",
            f"- `rollback_target = {summary['rollback_target']}`",
            f"- `backout_target = {summary['backout_target']}`",
            f"- `customer_rollout_authorized = {md_bool(summary['customer_rollout_authorized'])}`",
            f"- `runtime_switch_reopened = {md_bool(summary['runtime_switch_reopened'])}`",
        ]
    )


def render_window_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Post-Cutover Stabilization Window Dogrulama Raporu 2026-04-19",
            "",
            "## Official Fields",
            f"- `verification_window_started = {summary['verification_window_started']}`",
            f"- `verification_window_completed = {summary['verification_window_completed']}`",
            f"- `runtime_error_count = {summary['runtime_error_count']}`",
            f"- `unexplained_count = {summary['unexplained_count']}`",
            f"- `observed_regression_count = {summary['observed_regression_count']}`",
            f"- `stabilization_pass = {md_bool(summary['stabilization_pass'])}`",
            "",
            "## Window Detail",
            f"- `immediate_post_cutover_smoke_case_count = {summary['immediate_post_cutover_smoke_case_count']}`",
            f"- `stabilization_window_smoke_case_count = {summary['stabilization_window_smoke_case_count']}`",
            f"- `stabilization_window_sleep_seconds = {summary['stabilization_window_sleep_seconds']}`",
        ]
    )


def render_smoke_doc(summary: dict[str, Any]) -> str:
    lines = [
        "# Mevzuat Post-Cutover Runtime Smoke Dogrulama Raporu 2026-04-19",
        "",
        "## Official Fields",
        f"- `smoke_round_count = {summary['smoke_round_count']}`",
        f"- `total_smoke_case_count = {summary['total_smoke_case_count']}`",
        f"- `citation_readable_count = {summary['citation_readable_count']}`",
        f"- `source_correct_count = {summary['source_correct_count']}`",
        f"- `wrong_source_count = {summary['wrong_source_count']}`",
        f"- `runtime_error_count = {summary['runtime_error_count']}`",
        f"- `unexplained_count = {summary['unexplained_count']}`",
        f"- `live_serving_pass = {md_bool(summary['live_serving_pass'])}`",
    ]
    if summary.get("error_classes"):
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
            "# Mevzuat Post-Cutover Rollback Hazirlik Sureklilik Notu 2026-04-19",
            "",
            "## Official Fields",
            f"- `rollback_target_preserved = {md_bool(summary['rollback_target_preserved'])}`",
            f"- `backout_target_preserved = {md_bool(summary['backout_target_preserved'])}`",
            f"- `operator_execution_order_preserved = {md_bool(summary['operator_execution_order_preserved'])}`",
            f"- `rollback_readiness_pass = {md_bool(summary['rollback_readiness_pass'])}`",
        ]
    )


def render_gate_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Mevzuat Post-Cutover Stabilization Gate Raporu 2026-04-19",
            "",
            "## Official Decision",
            f"- decision = `{summary['decision']}`",
            "",
            "## PASS Criteria Contrast",
            f"- `active_runtime_collection = {summary['active_runtime_collection']}`",
            f"- `runtime_error_count = {summary['runtime_error_count']}`",
            f"- `unexplained_count = {summary['unexplained_count']}`",
            f"- `observed_regression_count = {summary['observed_regression_count']}`",
            f"- `wrong_source_count = {summary['wrong_source_count']}`",
            f"- `live_serving_pass = {md_bool(summary['live_serving_pass'])}`",
            f"- `stabilization_pass = {md_bool(summary['stabilization_pass'])}`",
            f"- `rollback_target_preserved = {md_bool(summary['rollback_target_preserved'])}`",
            f"- `backout_target_preserved = {md_bool(summary['backout_target_preserved'])}`",
            f"- `customer_rollout_authorized = {md_bool(summary['customer_rollout_authorized'])}`",
        ]
    )


def render_next_doc(decision: str) -> str:
    next_work = (
        "mevzuat primary-law runtime authoritative line closed under canonical current authority"
        if decision.startswith("PASS")
        else "mevzuat post-cutover remediation under canonical current authority"
    )
    return "\n".join(
        [
            "# Mevzuat Post-Cutover Stabilization Sonrasi Next Official Work Karari 2026-04-19",
            "",
            "## Official Decision",
            f"- `next_official_work = {next_work}`",
        ]
    )


def main() -> None:
    ensure_dir(RUNTIME_DIR)
    smoke_cases = select_smoke_cases(SOURCE_ARTICLE_ROWS)
    previous_targets = load_prior_cutover_targets()
    rollback_target = str(previous_targets["rollback_target"])
    backout_target = str(previous_targets["backout_target"])

    active_freeze = {
        "active_runtime_collection": ACTIVE_RUNTIME_COLLECTION,
        "rollback_target": rollback_target,
        "backout_target": backout_target,
        "customer_rollout_authorized": False,
        "runtime_switch_reopened": False,
    }

    bound_collection = current_bound_collection()
    if bound_collection:
        active_freeze["active_runtime_collection"] = bound_collection

    window = {
        "verification_window_started": now_utc(),
        "verification_window_completed": None,
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "observed_regression_count": 0,
        "stabilization_pass": False,
        "immediate_post_cutover_smoke_case_count": 0,
        "stabilization_window_smoke_case_count": 0,
        "stabilization_window_sleep_seconds": STABILIZATION_WINDOW_SLEEP_SECONDS,
    }

    smoke = {
        "smoke_round_count": SMOKE_ROUND_COUNT,
        "total_smoke_case_count": 0,
        "citation_readable_count": 0,
        "source_correct_count": 0,
        "wrong_source_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "live_serving_pass": False,
        "error_classes": [],
    }

    rollback = {
        "rollback_target_preserved": rollback_target == DEFAULT_ROLLBACK_TARGET and collection_entity_count(rollback_target) is not None,
        "backout_target_preserved": backout_target == DEFAULT_ROLLBACK_TARGET and collection_entity_count(backout_target) is not None,
        "operator_execution_order_preserved": bool(previous_targets["operator_execution_order_preserved"]),
        "rollback_readiness_pass": False,
    }

    immediate_results: list[dict[str, Any]] = []
    stabilization_results: list[dict[str, Any]] = []
    execution_error_class: str | None = None
    execution_error_text: str | None = None

    try:
        if active_freeze["active_runtime_collection"] != ACTIVE_RUNTIME_COLLECTION:
            raise RuntimeError(
                f"active runtime binding mismatch: expected {ACTIVE_RUNTIME_COLLECTION}, got {active_freeze['active_runtime_collection']}"
            )
        if not wait_for_health():
            raise RuntimeError("active runtime health timeout")
        if not wait_for_chat_ready():
            raise RuntimeError("active runtime chat readiness timeout")

        immediate_results = run_smoke_round("immediate_post_cutover_smoke", smoke_cases)
        window["immediate_post_cutover_smoke_case_count"] = len(immediate_results)

        time.sleep(STABILIZATION_WINDOW_SLEEP_SECONDS)

        if not wait_for_health():
            raise RuntimeError("stabilization window health timeout")
        if not wait_for_chat_ready():
            raise RuntimeError("stabilization window chat readiness timeout")

        stabilization_results = run_smoke_round("stabilization_window_smoke", smoke_cases)
        window["stabilization_window_smoke_case_count"] = len(stabilization_results)
    except Exception as exc:
        execution_error_class = "stabilization_window_failure"
        execution_error_text = repr(exc)
        smoke["runtime_error_count"] += 1
        smoke["unexplained_count"] += 1
        smoke["error_classes"] = [execution_error_class]
    finally:
        window["verification_window_completed"] = now_utc()

    all_results = immediate_results + stabilization_results
    if all_results:
        summarized = summarize_case_results(all_results)
        smoke.update(summarized)
        smoke["total_smoke_case_count"] = len(all_results)
        smoke["error_classes"] = sorted({item["error_class"] for item in all_results if item.get("error_class")})
        window["runtime_error_count"] = smoke["runtime_error_count"]
        window["unexplained_count"] = smoke["unexplained_count"]
        if immediate_results and stabilization_results:
            window["observed_regression_count"] = compute_observed_regression_count(immediate_results, stabilization_results)
        smoke["live_serving_pass"] = all(
            [
                smoke["wrong_source_count"] == 0,
                smoke["runtime_error_count"] == 0,
                smoke["unexplained_count"] == 0,
                smoke["total_smoke_case_count"] == 14,
            ]
        )
    else:
        smoke["live_serving_pass"] = False

    if execution_error_class and execution_error_text and execution_error_class not in smoke["error_classes"]:
        smoke["error_classes"].append(execution_error_class)

    window["stabilization_pass"] = all(
        [
            smoke["runtime_error_count"] == 0,
            smoke["unexplained_count"] == 0,
            window["observed_regression_count"] == 0,
            window["immediate_post_cutover_smoke_case_count"] == 7,
            window["stabilization_window_smoke_case_count"] == 7,
        ]
    )
    rollback["rollback_readiness_pass"] = all(
        [
            rollback["rollback_target_preserved"],
            rollback["backout_target_preserved"],
            rollback["operator_execution_order_preserved"],
        ]
    )

    decision = "PASS - Mevzuat Post-Cutover Stabilization And Runtime Verification Closed"
    if not all(
        [
            active_freeze["active_runtime_collection"] == ACTIVE_RUNTIME_COLLECTION,
            smoke["runtime_error_count"] == 0,
            smoke["unexplained_count"] == 0,
            window["observed_regression_count"] == 0,
            smoke["wrong_source_count"] == 0,
            smoke["live_serving_pass"],
            window["stabilization_pass"],
            rollback["rollback_target_preserved"],
            rollback["backout_target_preserved"],
            not active_freeze["customer_rollout_authorized"],
        ]
    ):
        decision = "NO-GO - Mevzuat Post-Cutover Stabilization Or Runtime Verification"

    summary = {
        **active_freeze,
        **window,
        **smoke,
        **rollback,
        "decision": decision,
        "immediate_results": immediate_results,
        "stabilization_results": stabilization_results,
        "execution_error_text": execution_error_text,
    }

    write_text(ACTIVE_FREEZE_DOC, render_active_freeze_doc(active_freeze))
    write_text(WINDOW_DOC, render_window_doc(window))
    write_text(SMOKE_DOC, render_smoke_doc(smoke))
    write_text(ROLLBACK_DOC, render_rollback_doc(rollback))
    write_text(GATE_DOC, render_gate_doc(summary))
    write_text(NEXT_DOC, render_next_doc(decision))
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
