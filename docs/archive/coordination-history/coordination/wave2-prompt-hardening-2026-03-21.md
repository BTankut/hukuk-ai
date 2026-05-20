# Wave 2 Prompt Hardening

Date: 2026-03-21
Scope: first narrow Wave 2 prompt-only intervention on the live gateway path
Decision: harden the live prompt in `llm/client.py` instead of touching unused `PromptBuilder`, and make the local embedding service start from cache without network or MPS dependency

## Why This Was The Narrow Change

Code inspection showed:

- `api-gateway/src/rag/prompt_builder.py` exists
- but the live path does not use it
- the active prompt is assembled inside `api-gateway/src/llm/client.py`

So a prompt-only Wave 2 change had to target the real production path, not the unused builder.

## What Changed

### 1) Live prompt hardened in the real execution path

File:

- `api-gateway/src/llm/client.py`

New live rules added to the RAG prompt:

- explicit law-family selection as an internal step
- mandatory respect for explicitly asked articles when present in context
- law-prefix preservation (`TBK/TMK/TCK/HMK/TTK/İİK`)
- cross-law citation discipline
- short answer / compactness bias
- explicit ban on neighbor-article citation drift

### 2) Tests added for the real prompt path

File:

- `api-gateway/tests/test_llm_client.py`

The tests lock the actual message content sent by `generate_rag_draft()` for:

- context-present flow
- no-context refusal flow

### 3) Embedding startup hardened for cache-only local bring-up

File:

- `services/embedding-service/src/model.py`

Hardening added:

- prefer local cache automatically when the E5 model cache is already present
- force HF/Transformers offline mode in cache-only flow
- device auto-fallback from unsupported `mps` to `cpu`
- `EMBEDDING_DEVICE` override support

### 4) Offline startup tests added

File:

- `tests/test_embedding_service_model.py`

These tests lock:

- local-files-only resolution
- cache detection
- device fallback
- offline env setup

## Verified Results

### Code-level verification

Passed:

- `python3 -m py_compile api-gateway/src/llm/client.py`
- `python3 -m py_compile services/embedding-service/src/model.py`
- `pytest tests/test_embedding_service_model.py`
- `pytest tests/test_embedding_service_model.py api-gateway/tests/test_llm_client.py api-gateway/tests/test_orchestrator_smoke.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py`

### Local stack recovery

Verified:

- embedding service bound successfully outside sandbox
- `curl http://127.0.0.1:8081/health` returned `status=ok`
- gateway bound successfully outside sandbox
- `curl http://127.0.0.1:8000/v1/health` returned `status=ok`

## Current Live Blocker

The local stack is healthy, but live generation is currently blocked upstream:

- `curl http://192.168.12.236:8080/v1/models` → connection failed
- `curl http://192.168.101.12:8080/v1/models` → timeout

So the remaining blocker for prompt eval is now:

- **dgxnode2 live model endpoint unavailable**

Not blocked anymore:

- local embedding startup
- local gateway startup
- prompt-path test coverage

## Next Action

When the dgxnode2 model endpoint comes back:

1. run a live smoke through `localhost:8000`
2. run a citation-drift / cross-law focused eval slice
3. decide whether the first Wave 2 prompt-only change earns a wider eval
