#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "faz2c"))

from capture_narrow_pilot_snapshot import metric_value, parse_metrics_text  # noqa: E402


def _fetch_json(url: str, *, api_key: str | None = None, timeout: float = 10.0) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(url)
    if api_key:
        request.add_header("X-API-Key", api_key)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _fetch_text(url: str, *, api_key: str | None = None, timeout: float = 10.0) -> tuple[int, str]:
    request = urllib.request.Request(url)
    if api_key:
        request.add_header("X-API-Key", api_key)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8")


def _post_json(
    url: str,
    *,
    payload: dict[str, Any],
    api_key: str | None = None,
    timeout: float = 30.0,
) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if api_key:
        request.add_header("X-API-Key", api_key)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _delete_json(url: str, *, api_key: str | None = None, timeout: float = 10.0) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(url, method="DELETE")
    if api_key:
        request.add_header("X-API-Key", api_key)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _unauthorized_status(url: str, *, timeout: float) -> int:
    request = urllib.request.Request(
        url,
        data=json.dumps(
            {
                "model": "hukuk-lora",
                "messages": [{"role": "user", "content": "anon test"}],
                "stream": False,
                "max_tokens": 16,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def run_release_smoke_suite(
    *,
    base_url: str,
    api_key: str,
    model: str,
    cited_query: str,
    refusal_query: str,
    expected_ref: str,
    session_id: str,
    timeout: float,
) -> dict[str, Any]:
    base_url = base_url.rstrip("/")
    _, metrics_before_text = _fetch_text(f"{base_url}/v1/metrics", api_key=api_key, timeout=timeout)
    metrics_before = parse_metrics_text(metrics_before_text)

    unauthorized_status = _unauthorized_status(f"{base_url}/v1/chat/completions", timeout=timeout)

    _, health = _fetch_json(f"{base_url}/v1/health", api_key=api_key, timeout=timeout)
    _, alerts = _fetch_json(f"{base_url}/v1/alerts", api_key=api_key, timeout=timeout)

    _, cited_response = _post_json(
        f"{base_url}/v1/chat/completions",
        api_key=api_key,
        timeout=timeout,
        payload={
            "model": model,
            "messages": [{"role": "user", "content": cited_query}],
            "stream": False,
            "use_verification": False,
            "max_tokens": 128,
            "session_id": session_id,
        },
    )

    _, refusal_response = _post_json(
        f"{base_url}/v1/chat/completions",
        api_key=api_key,
        timeout=timeout,
        payload={
            "model": model,
            "messages": [{"role": "user", "content": refusal_query}],
            "stream": False,
            "use_verification": False,
            "max_tokens": 128,
            "session_id": session_id,
        },
    )

    _, session_payload = _fetch_json(
        f"{base_url}/v1/sessions/{session_id}",
        api_key=api_key,
        timeout=timeout,
    )
    _, metrics_after_text = _fetch_text(f"{base_url}/v1/metrics", api_key=api_key, timeout=timeout)
    metrics_after = parse_metrics_text(metrics_after_text)

    _, delete_payload = _delete_json(
        f"{base_url}/v1/sessions/{session_id}",
        api_key=api_key,
        timeout=timeout,
    )

    audit_events_delta = metric_value(metrics_after, "hukuk_ai_audit_events_total") - metric_value(
        metrics_before,
        "hukuk_ai_audit_events_total",
    )
    auth_failure_delta = metric_value(
        metrics_after,
        "hukuk_ai_auth_failure_total",
    ) - metric_value(metrics_before, "hukuk_ai_auth_failure_total")
    citation_delta = metric_value(metrics_after, "hukuk_ai_citation_total") - metric_value(
        metrics_before,
        "hukuk_ai_citation_total",
    )
    refusal_delta = metric_value(
        metrics_after,
        "hukuk_ai_chat_refusal_total",
    ) - metric_value(metrics_before, "hukuk_ai_chat_refusal_total")

    history = session_payload.get("history") or []
    cited_answer = ((cited_response.get("choices") or [{}])[0].get("message") or {}).get("content", "")
    cited_citations = cited_response.get("citations") or []
    refusal_answer = ((refusal_response.get("choices") or [{}])[0].get("message") or {}).get("content", "")
    refusal_mode = refusal_response.get("final_mode")

    return {
        "health": health,
        "alerts": alerts,
        "auth": {
            "unauthorized_status": unauthorized_status,
            "authorized_mode": cited_response.get("final_mode"),
            "auth_failure_delta": auth_failure_delta,
        },
        "cited_smoke": {
            "answer_preview": cited_answer[:240],
            "citations": cited_citations,
            "expected_ref_found": expected_ref in cited_answer or expected_ref in " ".join(cited_citations),
        },
        "refusal_smoke": {
            "answer_preview": refusal_answer[:240],
            "final_mode": refusal_mode,
            "blocked": refusal_response.get("blocked"),
        },
        "redis_session_continuity": {
            "session_id": session_id,
            "history_length": len(history),
            "delete_status": delete_payload.get("deleted"),
        },
        "metrics_delta": {
            "audit_events_delta": audit_events_delta,
            "citation_delta": citation_delta,
            "refusal_delta": refusal_delta,
        },
        "acceptance": {
            "auth_enforced": unauthorized_status == 401,
            "cited_smoke_pass": expected_ref in cited_answer or expected_ref in " ".join(cited_citations),
            "refusal_smoke_pass": refusal_mode in {"refusal", "blocked"},
            "session_continuity_pass": len(history) >= 4,
            "audit_advancing": audit_events_delta >= 2,
            "alerts_surface_present": isinstance(alerts, dict) and "lane_unhealthy" in alerts,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run FAZ7 release smoke suite.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8004")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--model", default="hukuk-lora")
    parser.add_argument(
        "--cited-query",
        default="TBK m.49 uyarınca haksız fiilin genel şartları nelerdir? Kısa cevap ver.",
    )
    parser.add_argument(
        "--refusal-query",
        default="Bana pizza tarifi ver.",
    )
    parser.add_argument("--expected-ref", default="TBK m.49")
    parser.add_argument("--session-id", default="faz7-smoke-session")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output-path", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_release_smoke_suite(
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        cited_query=args.cited_query,
        refusal_query=args.refusal_query,
        expected_ref=args.expected_ref,
        session_id=args.session_id,
        timeout=args.timeout,
    )
    if args.output_path:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(result["acceptance"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
