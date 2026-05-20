# Node3 Post-Train Eval Bridge

Date: 2026-03-21
Scope: bridge the completed dgxnode3 adapter into the repo's official `eval_runner` path without disturbing the existing baseline runtime
Decision: keep the proven node3 adapter serve in place, wrap it with an OpenAI-compatible proxy, and bind a separate local candidate gateway to that proxy

## Problem

The completed node3 fine-tune produced a valid adapter, but the external proven repo exposed:

- `/generate`
- `/health`

The repo's promotion-compatible path requires:

- `runner=eval_runner`
- gateway-compatible `/v1/chat/completions`

Direct local routing from the candidate gateway to `192.168.12.234:30002` was not stable from the local Python stack and produced `No route to host`.

## Bridge Design

### Remote node3 layer

The completed adapter was served on node3:

- adapter path: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/lora_adapter`
- serve port: `18000`

An OpenAI-compatible proxy was then launched on node3:

- proxy script: `scripts/finetune/openai_generate_proxy.py`
- proxy port: `30002`
- upstream: `http://127.0.0.1:18000`
- model id: `hukuk-ai-sft-qwen35-807-20260321`

### Local bridge layer

To avoid the local route issue, an SSH tunnel was opened:

- local port: `127.0.0.1:30002`
- remote target: `dgxnode3:127.0.0.1:30002`

This made the remote candidate runtime reachable from the local gateway over loopback.

### Local candidate gateway

A separate local API gateway instance was launched on `127.0.0.1:8002` with:

- `DGX_BASE_URL=http://127.0.0.1:30002/v1`
- `DGX_MODEL=hukuk-ai-sft-qwen35-807-20260321`
- `MILVUS_ENABLED=true`
- `MILVUS_COLLECTION=mevzuat_e5_shadow`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `RERANKER_ENABLED=false`
- `GUARDRAILS_ENABLED=true`
- `PRESIDIO_ENABLED=false`

This preserves the accepted runner family while isolating the candidate path from any existing baseline instance.

## Verification

Verified checkpoints:

1. node3 proxy model list responded on `/v1/models`
2. local SSH tunnel exposed the same `/v1/models` on `127.0.0.1:30002`
3. candidate gateway `127.0.0.1:8002/v1/health` returned:
   - `guardrails=enabled`
   - `retriever=milvus`
4. end-to-end smoke against `127.0.0.1:8002/v1/chat/completions` returned a cited answer for `TBK m.49`

## Outcome

The completed node3 adapter is now reachable through a promotion-compatible gateway runner path.

## Next Step

1. run `faz1-50` post-train eval against `http://127.0.0.1:8002`
2. freeze the raw report into a post-train evidence manifest
3. run the promotion gate against the frozen baseline manifest
