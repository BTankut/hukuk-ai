#!/usr/bin/env python3
"""Expose an OpenAI-compatible chat API over a simpler /generate upstream."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenAI-compatible proxy over a /generate upstream.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=30002)
    parser.add_argument("--upstream-base-url", required=True, help="Example: http://dgxnode3:18000")
    parser.add_argument("--model-id", default="hukuk-ai-sft-v3")
    parser.add_argument("--timeout", type=float, default=300.0)
    return parser


def build_upstream_payload(request_payload: dict[str, Any]) -> dict[str, Any]:
    messages = request_payload.get("messages")
    prompt = request_payload.get("prompt")
    if not isinstance(messages, list) or not messages:
        if isinstance(prompt, str) and prompt.strip():
            messages = [{"role": "user", "content": prompt}]
        else:
            raise ValueError("Either non-empty 'messages' or 'prompt' is required.")

    max_tokens = request_payload.get("max_tokens", request_payload.get("max_completion_tokens", 512))
    try:
        max_new_tokens = int(max_tokens)
    except (TypeError, ValueError):
        max_new_tokens = 512

    temperature = request_payload.get("temperature", 0.0)
    try:
        temperature_value = float(temperature)
    except (TypeError, ValueError):
        temperature_value = 0.0

    return {
        "messages": messages,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature_value,
    }


def build_chat_response(*, text: str, model_id: str) -> dict[str, Any]:
    created = int(time.time())
    return {
        "id": f"chatcmpl-{created}",
        "object": "chat.completion",
        "created": created,
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


class ProxyState:
    def __init__(self, *, upstream_base_url: str, model_id: str, timeout: float) -> None:
        self.upstream_base_url = upstream_base_url.rstrip("/")
        self.model_id = model_id
        self.timeout = timeout

    def call_upstream_generate(self, payload: dict[str, Any]) -> str:
        url = f"{self.upstream_base_url}/generate"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = body.get("text")
        if not isinstance(text, str):
            raise ValueError("Upstream response missing text field.")
        return text

    def fetch_upstream_health(self) -> dict[str, Any]:
        url = f"{self.upstream_base_url}/health"
        with urllib.request.urlopen(url, timeout=min(self.timeout, 10.0)) as response:
            body = response.read().decode("utf-8")
        payload = json.loads(body)
        return payload if isinstance(payload, dict) else {"raw": payload}


class ProxyHandler(BaseHTTPRequestHandler):
    state: ProxyState

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/v1/health"}:
            try:
                upstream = self.state.fetch_upstream_health()
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "proxy_model": self.state.model_id,
                        "upstream_base_url": self.state.upstream_base_url,
                        "upstream": upstream,
                    },
                )
            except Exception as exc:  # pragma: no cover - real upstream behavior
                self._send_json(
                    503,
                    {
                        "status": "degraded",
                        "proxy_model": self.state.model_id,
                        "upstream_base_url": self.state.upstream_base_url,
                        "error": str(exc),
                    },
                )
            return

        if self.path == "/v1/models":
            self._send_json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": self.state.model_id,
                            "object": "model",
                            "created": 0,
                            "owned_by": "hukuk-ai",
                        }
                    ],
                },
            )
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            request_payload = json.loads(body.decode("utf-8") or "{}")
            upstream_payload = build_upstream_payload(request_payload)
            text = self.state.call_upstream_generate(upstream_payload)
            model_id = str(request_payload.get("model") or self.state.model_id)
            self._send_json(200, build_chat_response(text=text, model_id=model_id))
        except urllib.error.HTTPError as exc:  # pragma: no cover - real upstream behavior
            error_body = exc.read().decode("utf-8", errors="replace")
            self._send_json(exc.code, {"error": error_body[:500]})
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), fmt % args))


def main() -> int:
    args = build_parser().parse_args()
    ProxyHandler.state = ProxyState(
        upstream_base_url=args.upstream_base_url,
        model_id=args.model_id,
        timeout=args.timeout,
    )
    server = ThreadingHTTPServer((args.host, args.port), ProxyHandler)
    print(f"Proxy listening on http://{args.host}:{args.port} -> {args.upstream_base_url}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
