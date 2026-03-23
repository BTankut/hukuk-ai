#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


METRIC_LINE_RE = re.compile(
    r'^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(?P<labels>[^}]*)\})?\s+(?P<value>-?\d+(?:\.\d+)?)$'
)


@dataclass
class SmokeResult:
    ok: bool
    latency_ms: float | None
    cited_ref_found: bool
    blocked: bool | None
    answer_preview: str | None
    error: str | None = None


def fetch_json(url: str, *, api_key: str | None = None, timeout: float = 10.0) -> dict:
    request = urllib.request.Request(url)
    if api_key:
        request.add_header("X-API-Key", api_key)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str, *, api_key: str | None = None, timeout: float = 10.0) -> str:
    request = urllib.request.Request(url)
    if api_key:
        request.add_header("X-API-Key", api_key)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def post_chat_completion(
    *,
    url: str,
    api_key: str | None,
    model: str,
    query: str,
    max_tokens: int,
    timeout: float,
) -> tuple[dict, float]:
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": query}],
            "stream": False,
            "max_tokens": max_tokens,
            "use_verification": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if api_key:
        request.add_header("X-API-Key", api_key)
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    latency_ms = (time.perf_counter() - started) * 1000.0
    return json.loads(body), latency_ms


def parse_metrics_text(text: str) -> dict[str, list[tuple[dict[str, str], float]]]:
    parsed: dict[str, list[tuple[dict[str, str], float]]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = METRIC_LINE_RE.match(line)
        if not match:
            continue
        labels_text = match.group("labels")
        labels: dict[str, str] = {}
        if labels_text:
            for item in labels_text.split(","):
                key, _, value = item.partition("=")
                labels[key.strip()] = value.strip().strip('"')
        parsed.setdefault(match.group("name"), []).append((labels, float(match.group("value"))))
    return parsed


def metric_value(
    metrics: dict[str, list[tuple[dict[str, str], float]]],
    name: str,
    *,
    labels: dict[str, str] | None = None,
) -> float:
    total = 0.0
    found = False
    for entry_labels, value in metrics.get(name, []):
        if labels is None or all(entry_labels.get(key) == expected for key, expected in labels.items()):
            total += value
            found = True
    return total if found else 0.0


def run_smoke(
    *,
    base_url: str,
    api_key: str | None,
    smoke_query: str,
    model: str,
    expected_ref: str,
    max_tokens: int,
    timeout: float,
) -> SmokeResult:
    try:
        response, latency_ms = post_chat_completion(
            url=f"{base_url.rstrip('/')}/v1/chat/completions",
            api_key=api_key,
            model=model,
            query=smoke_query,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return SmokeResult(
            ok=False,
            latency_ms=None,
            cited_ref_found=False,
            blocked=None,
            answer_preview=None,
            error=str(exc),
        )

    choice = (response.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    answer = message.get("content") or ""
    citations = response.get("citations") or []
    blocked = response.get("blocked")
    cited_ref_found = expected_ref in answer or expected_ref in " ".join(citations)
    ok = bool(cited_ref_found and not blocked)
    return SmokeResult(
        ok=ok,
        latency_ms=latency_ms,
        cited_ref_found=cited_ref_found,
        blocked=bool(blocked),
        answer_preview=answer[:240],
    )


def capture_snapshot(
    *,
    base_url: str,
    api_key: str | None,
    smoke_query: str,
    model: str,
    expected_ref: str,
    max_tokens: int,
    timeout: float,
    latency_budget_ms: float,
) -> dict:
    health = fetch_json(f"{base_url.rstrip('/')}/v1/health", api_key=api_key, timeout=timeout)
    metrics_before_text = fetch_text(f"{base_url.rstrip('/')}/v1/metrics", api_key=api_key, timeout=timeout)
    metrics_before = parse_metrics_text(metrics_before_text)

    smoke = run_smoke(
        base_url=base_url,
        api_key=api_key,
        smoke_query=smoke_query,
        model=model,
        expected_ref=expected_ref,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    metrics_after_text = fetch_text(f"{base_url.rstrip('/')}/v1/metrics", api_key=api_key, timeout=timeout)
    metrics_after = parse_metrics_text(metrics_after_text)

    audit_events_delta = metric_value(metrics_after, "hukuk_ai_audit_events_total") - metric_value(
        metrics_before,
        "hukuk_ai_audit_events_total",
    )
    upstream_usage_delta = metric_value(
        metrics_after,
        "hukuk_ai_usage_source_total",
        labels={"source": "upstream"},
    ) - metric_value(
        metrics_before,
        "hukuk_ai_usage_source_total",
        labels={"source": "upstream"},
    )
    successful_chat_delta = metric_value(
        metrics_after,
        "hukuk_ai_http_requests_total",
        labels={"path": "/v1/chat/completions", "method": "POST", "status": "200"},
    ) - metric_value(
        metrics_before,
        "hukuk_ai_http_requests_total",
        labels={"path": "/v1/chat/completions", "method": "POST", "status": "200"},
    )
    refusal_delta = metric_value(metrics_after, "hukuk_ai_chat_refusal_total") - metric_value(
        metrics_before,
        "hukuk_ai_chat_refusal_total",
    )

    rollback_reasons: list[str] = []
    if health.get("status") != "ok":
        rollback_reasons.append("health_not_ok")
    if not smoke.ok:
        rollback_reasons.append("cited_smoke_failed")
    if audit_events_delta < 1:
        rollback_reasons.append("audit_not_advancing")
    if upstream_usage_delta < 1:
        rollback_reasons.append("upstream_usage_not_advancing")
    if successful_chat_delta < 1:
        rollback_reasons.append("chat_request_counter_not_advancing")
    if refusal_delta > 0:
        rollback_reasons.append("unexpected_refusal_delta")
    if smoke.latency_ms is not None and smoke.latency_ms > latency_budget_ms:
        rollback_reasons.append("latency_budget_exceeded")

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "health": health,
        "smoke": asdict(smoke),
        "metrics_delta": {
            "audit_events_delta": audit_events_delta,
            "upstream_usage_delta": upstream_usage_delta,
            "successful_chat_delta": successful_chat_delta,
            "refusal_delta": refusal_delta,
        },
        "latency_budget_ms": latency_budget_ms,
        "rollback_recommended": bool(rollback_reasons),
        "rollback_reasons": rollback_reasons,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture a narrow pilot monitoring snapshot.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key")
    parser.add_argument("--model", default="hukuk-lora")
    parser.add_argument(
        "--smoke-query",
        default="TBK m.49 uyarınca haksız fiilin genel şartları nelerdir? Kısa cevap ver.",
    )
    parser.add_argument("--expected-ref", default="TBK m.49")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--latency-budget-ms", type=float, default=30000.0)
    parser.add_argument("--output-path", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    snapshot = capture_snapshot(
        base_url=args.base_url,
        api_key=args.api_key,
        smoke_query=args.smoke_query,
        model=args.model,
        expected_ref=args.expected_ref,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        latency_budget_ms=args.latency_budget_ms,
    )
    output = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if args.output_path:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(output, encoding="utf-8")
        print(str(args.output_path))
    else:
        print(output, end="")
    return 0 if not snapshot["rollback_recommended"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
