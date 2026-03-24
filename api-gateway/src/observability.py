from __future__ import annotations

import os
from collections import Counter, defaultdict
from threading import Lock
from typing import Any


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _to_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(0.0, min(1.0, percentile)) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._http_requests: Counter[tuple[str, str, str]] = Counter()
        self._http_latency_sum_ms: defaultdict[tuple[str, str], float] = defaultdict(float)
        self._http_latency_count: Counter[tuple[str, str]] = Counter()
        self._http_latency_values_ms: list[float] = []
        self._chat_blocked_total: Counter[tuple[str, str]] = Counter()
        self._chat_refusal_total: Counter[tuple[str, str]] = Counter()
        self._usage_source_total: Counter[str] = Counter()
        self._citation_total = 0
        self._hallucination_fail_total = 0
        self._audit_events_total = 0
        self._audit_write_error_total = 0
        self._auth_failure_total = 0
        self._redis_session_error_total = 0
        self._backup_error_total = 0
        self._rollback_event_total = 0
        self._token_accounting_failure_total = 0
        self._lane_health_state: dict[str, int] = {}

    def reset(self) -> None:
        with self._lock:
            self._http_requests.clear()
            self._http_latency_sum_ms.clear()
            self._http_latency_count.clear()
            self._http_latency_values_ms.clear()
            self._chat_blocked_total.clear()
            self._chat_refusal_total.clear()
            self._usage_source_total.clear()
            self._citation_total = 0
            self._hallucination_fail_total = 0
            self._audit_events_total = 0
            self._audit_write_error_total = 0
            self._auth_failure_total = 0
            self._redis_session_error_total = 0
            self._backup_error_total = 0
            self._rollback_event_total = 0
            self._token_accounting_failure_total = 0
            self._lane_health_state.clear()

    def record_http_request(
        self,
        *,
        path: str,
        method: str,
        status_code: int,
        latency_ms: float,
    ) -> None:
        status = str(status_code)
        with self._lock:
            self._http_requests[(path, method, status)] += 1
            self._http_latency_sum_ms[(path, method)] += latency_ms
            self._http_latency_count[(path, method)] += 1
            self._http_latency_values_ms.append(latency_ms)

    def record_chat_outcome(
        self,
        *,
        path: str,
        model: str,
        blocked: bool,
        is_refusal: bool,
        usage_source: str,
        citation_count: int = 0,
        hallucination_fail: bool = False,
    ) -> None:
        with self._lock:
            if blocked:
                self._chat_blocked_total[(path, model)] += 1
            if is_refusal:
                self._chat_refusal_total[(path, model)] += 1
            self._usage_source_total[usage_source] += 1
            self._citation_total += max(0, citation_count)
            if hallucination_fail:
                self._hallucination_fail_total += 1

    def record_audit_event(self) -> None:
        with self._lock:
            self._audit_events_total += 1

    def record_audit_write_error(self) -> None:
        with self._lock:
            self._audit_write_error_total += 1

    def record_auth_failure(self) -> None:
        with self._lock:
            self._auth_failure_total += 1

    def record_redis_session_error(self) -> None:
        with self._lock:
            self._redis_session_error_total += 1

    def record_backup_error(self) -> None:
        with self._lock:
            self._backup_error_total += 1

    def record_rollback_event(self) -> None:
        with self._lock:
            self._rollback_event_total += 1

    def record_token_accounting_failure(self) -> None:
        with self._lock:
            self._token_accounting_failure_total += 1

    def set_lane_health_state(self, *, lane: str, healthy: bool) -> None:
        with self._lock:
            self._lane_health_state[lane] = 1 if healthy else 0

    def alerts_snapshot(self) -> dict[str, Any]:
        auth_failure_spike_threshold = _to_int(os.getenv("AUTH_FAILURE_SPIKE_THRESHOLD"), 5)
        latency_spike_threshold_ms = float(_to_int(os.getenv("LATENCY_SPIKE_THRESHOLD_MS"), 20000))
        p95_latency_ms = _percentile(self._http_latency_values_ms, 0.95)
        with self._lock:
            lane_unhealthy = any(value == 0 for value in self._lane_health_state.values())
            return {
                "lane_unhealthy": lane_unhealthy,
                "audit_write_failure": self._audit_write_error_total > 0,
                "redis_unavailable": self._redis_session_error_total > 0,
                "token_accounting_failure": self._token_accounting_failure_total > 0,
                "backup_failure": self._backup_error_total > 0,
                "auth_failure_spike": self._auth_failure_total >= auth_failure_spike_threshold,
                "latency_regression_spike": p95_latency_ms > latency_spike_threshold_ms,
                "rollback_event": self._rollback_event_total > 0,
                "p95_latency_ms": p95_latency_ms,
            }

    def render_prometheus(self) -> str:
        lines: list[str] = [
            "# HELP hukuk_ai_http_requests_total Total HTTP requests by path, method, and status.",
            "# TYPE hukuk_ai_http_requests_total counter",
        ]
        for (path, method, status), value in sorted(self._http_requests.items()):
            lines.append(
                'hukuk_ai_http_requests_total{path="%s",method="%s",status="%s"} %d'
                % (_escape_label(path), _escape_label(method), _escape_label(status), value)
            )

        lines.extend(
            [
                "# HELP hukuk_ai_http_request_latency_ms_sum Total request latency in milliseconds.",
                "# TYPE hukuk_ai_http_request_latency_ms_sum counter",
            ]
        )
        for (path, method), value in sorted(self._http_latency_sum_ms.items()):
            lines.append(
                'hukuk_ai_http_request_latency_ms_sum{path="%s",method="%s"} %.3f'
                % (_escape_label(path), _escape_label(method), value)
            )

        lines.extend(
            [
                "# HELP hukuk_ai_http_request_latency_ms_count Total counted request latency observations.",
                "# TYPE hukuk_ai_http_request_latency_ms_count counter",
            ]
        )
        for (path, method), value in sorted(self._http_latency_count.items()):
            lines.append(
                'hukuk_ai_http_request_latency_ms_count{path="%s",method="%s"} %d'
                % (_escape_label(path), _escape_label(method), value)
            )

        p50_latency = _percentile(self._http_latency_values_ms, 0.50)
        p95_latency = _percentile(self._http_latency_values_ms, 0.95)
        p99_latency = _percentile(self._http_latency_values_ms, 0.99)
        lines.extend(
            [
                "# HELP hukuk_ai_http_request_latency_ms_p50 Request latency p50 in milliseconds.",
                "# TYPE hukuk_ai_http_request_latency_ms_p50 gauge",
                f"hukuk_ai_http_request_latency_ms_p50 {p50_latency:.3f}",
                "# HELP hukuk_ai_http_request_latency_ms_p95 Request latency p95 in milliseconds.",
                "# TYPE hukuk_ai_http_request_latency_ms_p95 gauge",
                f"hukuk_ai_http_request_latency_ms_p95 {p95_latency:.3f}",
                "# HELP hukuk_ai_http_request_latency_ms_p99 Request latency p99 in milliseconds.",
                "# TYPE hukuk_ai_http_request_latency_ms_p99 gauge",
                f"hukuk_ai_http_request_latency_ms_p99 {p99_latency:.3f}",
            ]
        )

        lines.extend(
            [
                "# HELP hukuk_ai_chat_blocked_total Total blocked chat completions.",
                "# TYPE hukuk_ai_chat_blocked_total counter",
            ]
        )
        for (path, model), value in sorted(self._chat_blocked_total.items()):
            lines.append(
                'hukuk_ai_chat_blocked_total{path="%s",model="%s"} %d'
                % (_escape_label(path), _escape_label(model), value)
            )

        lines.extend(
            [
                "# HELP hukuk_ai_chat_refusal_total Total refusal-like chat responses.",
                "# TYPE hukuk_ai_chat_refusal_total counter",
            ]
        )
        for (path, model), value in sorted(self._chat_refusal_total.items()):
            lines.append(
                'hukuk_ai_chat_refusal_total{path="%s",model="%s"} %d'
                % (_escape_label(path), _escape_label(model), value)
            )

        lines.extend(
            [
                "# HELP hukuk_ai_usage_source_total Total usage accounting sources.",
                "# TYPE hukuk_ai_usage_source_total counter",
            ]
        )
        for source, value in sorted(self._usage_source_total.items()):
            lines.append(
                'hukuk_ai_usage_source_total{source="%s"} %d' % (_escape_label(source), value)
            )

        lines.extend(
            [
                "# HELP hukuk_ai_citation_total Total emitted citations.",
                "# TYPE hukuk_ai_citation_total counter",
                f"hukuk_ai_citation_total {self._citation_total}",
                "# HELP hukuk_ai_hallucination_fail_total Total hallucination-related fail signals.",
                "# TYPE hukuk_ai_hallucination_fail_total counter",
                f"hukuk_ai_hallucination_fail_total {self._hallucination_fail_total}",
                "# HELP hukuk_ai_audit_events_total Total structured audit events written.",
                "# TYPE hukuk_ai_audit_events_total counter",
                f"hukuk_ai_audit_events_total {self._audit_events_total}",
                "# HELP hukuk_ai_audit_write_error_total Total audit write failures.",
                "# TYPE hukuk_ai_audit_write_error_total counter",
                f"hukuk_ai_audit_write_error_total {self._audit_write_error_total}",
                "# HELP hukuk_ai_auth_failure_total Total auth failures.",
                "# TYPE hukuk_ai_auth_failure_total counter",
                f"hukuk_ai_auth_failure_total {self._auth_failure_total}",
                "# HELP hukuk_ai_redis_session_error_total Total Redis session errors.",
                "# TYPE hukuk_ai_redis_session_error_total counter",
                f"hukuk_ai_redis_session_error_total {self._redis_session_error_total}",
                "# HELP hukuk_ai_backup_error_total Total backup errors.",
                "# TYPE hukuk_ai_backup_error_total counter",
                f"hukuk_ai_backup_error_total {self._backup_error_total}",
                "# HELP hukuk_ai_rollback_event_total Total rollback events.",
                "# TYPE hukuk_ai_rollback_event_total counter",
                f"hukuk_ai_rollback_event_total {self._rollback_event_total}",
                "# HELP hukuk_ai_token_accounting_failure_total Total token accounting failures.",
                "# TYPE hukuk_ai_token_accounting_failure_total counter",
                f"hukuk_ai_token_accounting_failure_total {self._token_accounting_failure_total}",
                "# HELP hukuk_ai_lane_health_state Lane health state (1=healthy, 0=unhealthy).",
                "# TYPE hukuk_ai_lane_health_state gauge",
            ]
        )
        for lane, value in sorted(self._lane_health_state.items()):
            lines.append(
                'hukuk_ai_lane_health_state{lane="%s"} %d'
                % (_escape_label(lane), value)
            )

        alerts = self.alerts_snapshot()
        lines.extend(
            [
                "# HELP hukuk_ai_alert_state Alert surfaces derived from runtime counters.",
                "# TYPE hukuk_ai_alert_state gauge",
            ]
        )
        for alert_name, enabled in sorted(alerts.items()):
            if alert_name == "p95_latency_ms":
                continue
            lines.append(
                'hukuk_ai_alert_state{alert="%s"} %d'
                % (_escape_label(alert_name), 1 if enabled else 0)
            )
        return "\n".join(lines) + "\n"


_metrics_registry = MetricsRegistry()


def get_metrics_registry() -> MetricsRegistry:
    return _metrics_registry


_REFUSAL_HINTS = (
    "yardımcı olamam",
    "yanıt veremem",
    "bilgi veremiyorum",
    "kapsam dışı",
    "uzman bir hukukçuya danışın",
    "hukuka uygun bir mevzuat sorusu sorun",
)


def looks_like_refusal(answer: str, *, blocked: bool) -> bool:
    if blocked:
        return True
    lowered = (answer or "").lower()
    return any(hint in lowered for hint in _REFUSAL_HINTS)
