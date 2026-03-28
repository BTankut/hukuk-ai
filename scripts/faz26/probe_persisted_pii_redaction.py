#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any

from faz26_lib import write_json


TR_ID = "12345678901"
EMAIL = "test@example.com"
PHONE = "5551234567"
REDACTED_TOKENS = ["[TR_ID_REDACTED]", "[EMAIL_REDACTED]", "[PHONE_REDACTED]"]


def _contains_raw_pii(text: str) -> bool:
    return any(token in text for token in (TR_ID, EMAIL, PHONE))


def _fetch_probe(
    *,
    base_url: str,
    api_key: str,
    session_id: str,
    timeout: float,
) -> tuple[dict[str, Any], dict[str, str]]:
    payload = {
        "model": "hukuk-lora",
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Muvekkil {TR_ID}, {EMAIL} ve {PHONE} bilgileriyle aniliyor. "
                    "Bu sorudaki PII'yi cevapta kullanma; yalniz TBK m.49 kaynakli kisa aciklama ver."
                ),
            }
        ],
        "stream": False,
        "use_verification": False,
        "max_tokens": 96,
        "include_trace": True,
        "session_id": session_id,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
        headers = {key.lower(): value for key, value in response.headers.items()}
        return body, headers


def _load_matching_audit_event(path: Path, *, request_id: str) -> dict[str, Any]:
    for raw_line in reversed(path.read_text(encoding="utf-8").splitlines()):
        if not raw_line.strip():
            continue
        row = json.loads(raw_line)
        if row.get("request_id") == request_id:
            return row
    raise RuntimeError(f"request_id not found in audit log: {request_id}")


def run_probe(
    *,
    base_url: str,
    api_key: str,
    session_id: str,
    audit_log_path: Path,
    trace_log_dir: Path,
    timeout: float,
) -> dict[str, Any]:
    body, headers = _fetch_probe(base_url=base_url, api_key=api_key, session_id=session_id, timeout=timeout)
    request_id = headers.get("x-request-id")
    response_id = body.get("id")
    if not isinstance(request_id, str) or not request_id:
        raise RuntimeError("missing x-request-id response header")
    if not isinstance(response_id, str) or not response_id:
        raise RuntimeError("missing response id in body")

    audit_event = _load_matching_audit_event(audit_log_path, request_id=request_id)
    trace_path = trace_log_dir / f"{response_id}.json"
    trace_text = trace_path.read_text(encoding="utf-8")
    audit_text = json.dumps(audit_event, ensure_ascii=False)

    redaction_tokens_present = all(token in audit_text and token in trace_text for token in REDACTED_TOKENS)
    persisted_redaction_pass = (
        not _contains_raw_pii(audit_text)
        and not _contains_raw_pii(trace_text)
        and redaction_tokens_present
    )
    return {
        "request_id": request_id,
        "response_id": response_id,
        "audit_log_path": str(audit_log_path),
        "trace_path": str(trace_path),
        "persisted_redaction_pass": persisted_redaction_pass,
        "pii_leak_found": not persisted_redaction_pass,
        "redaction_tokens_present": redaction_tokens_present,
        "audit_has_auth_principal": "auth_principal" in audit_event,
        "audit_has_citation_list": "citation_list" in audit_event,
        "audit_has_latency": "latency" in audit_event,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe FAZ26 persisted PII redaction.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--session-id", default="faz26-pii-probe")
    parser.add_argument("--audit-log-path", type=Path, required=True)
    parser.add_argument("--trace-log-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    result = run_probe(
        base_url=args.base_url,
        api_key=args.api_key,
        session_id=args.session_id,
        audit_log_path=args.audit_log_path,
        trace_log_dir=args.trace_log_dir,
        timeout=args.timeout,
    )
    write_json(args.output_json, result)
    return 0 if result["persisted_redaction_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
