from __future__ import annotations

from collections import Counter, defaultdict
from threading import Lock


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._http_requests: Counter[tuple[str, str, str]] = Counter()
        self._http_latency_sum_ms: defaultdict[tuple[str, str], float] = defaultdict(float)
        self._http_latency_count: Counter[tuple[str, str]] = Counter()
        self._chat_blocked_total: Counter[tuple[str, str]] = Counter()
        self._chat_refusal_total: Counter[tuple[str, str]] = Counter()
        self._usage_source_total: Counter[str] = Counter()
        self._audit_events_total = 0

    def reset(self) -> None:
        with self._lock:
            self._http_requests.clear()
            self._http_latency_sum_ms.clear()
            self._http_latency_count.clear()
            self._chat_blocked_total.clear()
            self._chat_refusal_total.clear()
            self._usage_source_total.clear()
            self._audit_events_total = 0

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

    def record_chat_outcome(
        self,
        *,
        path: str,
        model: str,
        blocked: bool,
        is_refusal: bool,
        usage_source: str,
    ) -> None:
        with self._lock:
            if blocked:
                self._chat_blocked_total[(path, model)] += 1
            if is_refusal:
                self._chat_refusal_total[(path, model)] += 1
            self._usage_source_total[usage_source] += 1

    def record_audit_event(self) -> None:
        with self._lock:
            self._audit_events_total += 1

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
                "# HELP hukuk_ai_audit_events_total Total structured audit events written.",
                "# TYPE hukuk_ai_audit_events_total counter",
                f"hukuk_ai_audit_events_total {self._audit_events_total}",
            ]
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
