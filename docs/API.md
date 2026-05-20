# API

The API gateway exposes OpenAI-compatible chat completions plus Hukuk-AI legal advisor metadata.

## `GET /v1/health`

Returns machine-readable runtime state:

```json
{
  "status": "ok",
  "llm_configured": true,
  "llm_model": "<FINE_TUNED_MODEL_ID>",
  "mevzuat_retriever_available": true,
  "mevzuat_collection": "<MEVZUAT_COLLECTION>",
  "judicial_runtime_enabled": true,
  "judicial_ready": true,
  "judicial_readiness_failures": [],
  "legal_rag_runtime_mode": "advisor",
  "runtime_mode": "judicial_enabled_ready",
  "streaming_supported": true,
  "source_card_limit": 16
}
```

Important fields:

- `llm_configured`, `llm_reachable_if_checked`, `llm_model`, `llm_temperature`, `llm_max_tokens`.
- `mevzuat_retriever_available`, `mevzuat_index_ready`, `mevzuat_retrieval_enabled`.
- `judicial_runtime_enabled`, `judicial_ready`, `judicial_readiness_status`, `judicial_readiness_failures`.
- `judicial_processed_dir`, `judicial_exact_lookup_path`, `judicial_lexical_index_path`, `judicial_chunk_refs_path`.
- `embedding_backend`, `embedding_base_url`, `embedding_model`, `embedding_dim`.
- `retrieval_timeout_ms`, `llm_timeout_ms`, `verification_timeout_ms`.

## `POST /v1/chat/completions`

### Request schema

```json
{
  "model": "hukuk-ai-poc",
  "messages": [
    {"role": "user", "content": "TBK m.49 haksiz fiil sartlari nelerdir?"}
  ],
  "stream": false,
  "temperature": 0,
  "max_tokens": 1600,
  "session_id": null,
  "law_filter": null,
  "use_verification": true,
  "top_k": 20,
  "include_trace": false
}
```

`model`, `temperature`, and `max_tokens` are accepted for OpenAI compatibility. The legal advisor runtime uses configured defaults for production operation unless explicitly overridden by supported code paths.

### Non-streaming response schema

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1779290000,
  "model": "hukuk-ai-poc",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
  "blocked": false,
  "final_reason": null,
  "source_cards": [],
  "verification_status": "pass",
  "legal_rag_runtime_mode": "advisor",
  "judicial_runtime_enabled": true,
  "judicial_ready": true,
  "retrieval_lanes": [],
  "latency_breakdown_ms": {},
  "model_id": "<FINE_TUNED_MODEL_ID>"
}
```

### Streaming response

Set `stream=true`. The endpoint returns `text/event-stream` with OpenAI-style delta events:

```text
data: {"choices":[{"delta":{"content":"..."}}]}
data: {"object":"chat.completion.metadata","source_cards":[...],"verification_status":"pass"}
data: [DONE]
```

Streaming should preserve the same final content and metadata as the non-streaming response for the same runtime path.

## Hukuk-AI extensions

- `source_cards`: selected evidence cards; part of the public legal advisor contract.
- `verification_status`: verifier verdict for the generated or deterministic answer.
- `verification`: detailed verifier object when available.
- `answer_contract`: extended internal contract for audits and debugging.
- `blocked`: true when the runtime refused or bounded the answer.
- `final_reason`: machine-readable reason for blocked or degraded output.
- `legal_rag_runtime_mode`: current legal RAG mode, typically `advisor`.
- `judicial_runtime_enabled`, `judicial_ready`: judicial retrieval state.
- `retrieval_lanes`: evidence lanes that contributed selected sources.
- `latency_breakdown_ms`: retrieval and verification timing metadata.
- `model_id`: configured fine-tuned LLM model id.
- `trace`: include-trace/debug metadata, returned only when `include_trace=true` and supported by the route.

## Source card schema

Cards are dictionaries produced by the runtime. Common fields include:

```json
{
  "evidence_id": "mevzuat:...",
  "source_type": "mevzuat",
  "citation": "...",
  "retrieval_lane": "mevzuat",
  "title": "...",
  "metadata": {}
}
```

Judicial cards use `source_type` values for judicial evidence and include decision metadata when available. Clients should cite or display only evidence present in `source_cards`.
