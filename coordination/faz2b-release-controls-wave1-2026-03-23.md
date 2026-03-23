# FAZ 2B Wave 1 — API surface hardening

## Scope
- Objective: close the highest-risk release-control gaps that sit directly on the main request surface.
- Strategy:
  - keep model/retrieval behavior unchanged,
  - harden the gateway request path only,
  - ship test-backed controls before broader observability/session work.

## Implemented controls

### 1) Opt-in request auth
- Added shared auth helper:
  - `api-gateway/src/release_controls.py`
- Supported headers:
  - `Authorization: Bearer <key>`
  - `X-API-Key: <key>`
- Protected endpoints:
  - `/v1/chat/completions`
  - `/v1/sessions`
  - `/v1/sessions/{id}`
  - `/v1/models`
  - legacy `/v1/chat`
- Health endpoint remains open:
  - `/v1/health`

### 2) Structured audit logging
- Added append-only JSONL audit event writer:
  - `api-gateway/src/release_controls.py`
- Logged fields:
  - request path / method
  - client host
  - auth subject
  - response id
  - session id
  - stream flag
  - blocked flag
  - citations and count
  - guardrails reasons
  - usage payload
  - usage source
- Default log path:
  - `runtime_logs/api_audit.jsonl`
- Env override:
  - `AUDIT_LOG_PATH=...`

### 3) Runtime-backed usage accounting
- Added structured LLM usage extraction in:
  - `api-gateway/src/llm/client.py`
- Propagated usage through:
  - `api-gateway/src/rag/orchestrator.py`
  - `api-gateway/src/routers/chat.py`
- Chat responses now prefer upstream runtime usage when available.
- Deterministic shortcut lanes fall back to token estimation instead of split-by-space counts.
- SSE metadata chunk now also carries `usage`.

## Verification
- `python3 -m py_compile` passed for:
  - `release_controls.py`
  - `llm/client.py`
  - `rag/orchestrator.py`
  - `api/openai.py`
  - `main.py`
  - `routers/chat.py`
- Targeted pytest passed:
  - `api-gateway/tests/test_chat_router.py`
  - `api-gateway/tests/test_openai_api.py`
  - `api-gateway/tests/test_llm_client.py`
  - `api-gateway/tests/test_orchestrator_smoke.py`

## Decision
- Wave 1 closes the request-surface hardening milestone.
- FAZ 2B remains open because the next must-close controls are still:
  - PII masking proof
  - session persistence
  - observability / alerting
  - backup / restore proof

## Next active target
- Move to FAZ 2B Wave 2:
  - PII masking release proof
  - observability / alerting contract
  - session persistence design and cutover-safe abstraction
