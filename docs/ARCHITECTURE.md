# Architecture

Hukuk-AI Legal Advisor is a FastAPI service that turns a legal question into an evidence-grounded answer with source cards and verification metadata.

## Components

- Client: sends OpenAI-compatible chat completion requests.
- FastAPI API gateway: owns `/v1/health` and `/v1/chat/completions`.
- Query classification: identifies mevzuat-only, judicial-only, mixed, unsupported, and unsafe requests.
- Mevzuat retriever: fetches official legislation chunks from the configured Milvus collection.
- Judicial exact lookup: resolves specific decision identifiers from the processed SQLite index.
- Judicial lexical retrieval: searches processed judicial chunks through SQLite FTS.
- Optional vector lane: represented in health metadata when configured.
- Evidence packet: bounded selected evidence used by generation and verification.
- Fine-tuned LLM generation: calls the configured OpenAI-compatible endpoint.
- Post-generation verifier: checks claims and citations against selected evidence.
- Source cards: public evidence cards returned to clients.
- Streaming adapter: emits OpenAI-style SSE chunks plus a metadata event.
- Health/readiness: exposes runtime mode, index availability, and timeout settings.

## Request flow

```text
chat request
  -> normalize and classify query
  -> retrieve mevzuat evidence if required
  -> retrieve judicial evidence if enabled and required
  -> build evidence packet and source_cards
  -> generate legal answer with configured LLM
  -> verify generated claims against evidence
  -> return JSON or SSE response
```

## Fail-closed paths

- Judicial disabled: judicial-only claims are blocked instead of answered from priors.
- Judicial index missing or corrupt: judicial requests fail closed with readiness failures.
- Retrieval timeout: answer is blocked with a retrieval timeout reason.
- LLM timeout or generation failure: answer is blocked with the LLM failure reason.
- Verification failure: unsupported generated claims are blocked or repaired from evidence.
- Unsupported claim or fabrication request: runtime refuses and returns `blocked=true`.

## Evidence contract

The answer may rely only on selected evidence in the evidence packet. `source_cards` expose that evidence to clients. Citations and judicial metadata must come from those cards, not from model memory.
