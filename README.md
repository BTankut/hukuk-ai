# Hukuk-AI Legal Advisor

## Status

`main` is the canonical branch for the completed application. The final application tag is `legal-advisor-app-complete-20260520`.

The current product integrates mevzuat evidence and judicial decision evidence in one legal advisor runtime. Answers are evidence-grounded, claims are verified against selected sources, unsupported claims are blocked or bounded, and source cards are returned with the response.

## What the application does

Hukuk-AI exposes an OpenAI-compatible chat API for Turkish legal questions. It retrieves official legislation evidence, optionally retrieves processed judicial decision evidence, builds a bounded evidence packet, calls the configured fine-tuned LLM endpoint, verifies the answer against the selected evidence, and fails closed when required evidence or verification is unavailable.

## Current runtime architecture

```text
Client
  -> FastAPI API gateway
  -> query classification
  -> mevzuat retriever and optional judicial retrievers
  -> evidence packet and source_cards
  -> fine-tuned OpenAI-compatible LLM endpoint
  -> post-generation verifier
  -> OpenAI-compatible JSON or SSE response
```

Judicial runtime can be enabled or disabled. When enabled, processed judicial indexes must exist outside the repo. Streaming and non-streaming responses are expected to preserve the same final answer and metadata.

## Repository map

- `api-gateway/`: FastAPI application, chat router, RAG runtime, verification, tests.
- `scripts/run_legal_advisor_api.sh`: readiness-checked API launch wrapper.
- `scripts/check_legal_advisor_readiness.py`: compact environment and index readiness check.
- `scripts/run_final_legal_advisor_smoke.py`: real-index final smoke battery.
- `scripts/ci/check_closed_runtime_state.py`: fail-closed runtime state gate.
- [docs/USAGE.md](docs/USAGE.md): operator usage and curl examples.
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md): environment variables and runtime modes.
- [docs/API.md](docs/API.md): API contract and response metadata.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): concise runtime architecture.
- [docs/DATA_AND_INDEXES.md](docs/DATA_AND_INDEXES.md): external corpus and generated index handling.
- [docs/EVALUATION_AND_SMOKE.md](docs/EVALUATION_AND_SMOKE.md): validation commands and triage.
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): current development policy.
- [docs/LEGACY_DOCS.md](docs/LEGACY_DOCS.md): archived historical material map.

## Prerequisites

- Python 3.11+.
- API gateway dependencies installed in `api-gateway/.venv`.
- An OpenAI-compatible fine-tuned LLM endpoint.
- Milvus and an embedding endpoint when mevzuat retrieval is enabled.
- Processed judicial SQLite indexes when judicial runtime is enabled.

## Quick start

```bash
cd api-gateway
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev,milvus]
cd ..
```

Configure the environment with placeholders replaced by real operator values:

```bash
export DGX_BASE_URL=<OPENAI_COMPATIBLE_BASE_URL>
export DGX_MODEL=<FINE_TUNED_MODEL_ID>
export LEGAL_ADVISOR_LLM_ENABLED=true
export MILVUS_ENABLED=true
export MILVUS_URI=http://localhost:19530
export MILVUS_COLLECTION=<MEVZUAT_COLLECTION>
export EMBEDDING_BACKEND=remote
export EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
export EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
export EMBEDDING_DIM=1024
export JUDICIAL_RUNTIME_ENABLED=true
export JUDICIAL_PROCESSED_DIR=<PROCESSED_JUDICIAL_DIR>
```

## Environment configuration

Use `.env.example` as a template, then set real endpoint, model, Milvus, embedding, and judicial index values in your shell or deployment secret store. See `docs/CONFIGURATION.md` for every supported variable.

## Readiness check

```bash
python3 scripts/check_legal_advisor_readiness.py
```

The readiness check fails if required LLM settings are missing, or if judicial runtime is enabled but the processed SQLite indexes are absent or unreadable.

## Run API

```bash
scripts/run_legal_advisor_api.sh
```

The wrapper runs readiness first unless `SKIP_READINESS_CHECK=true` is set.

## Ask a question

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"TBK m.49 haksiz fiil sartlari nelerdir?"}]}'
```

## Streaming example

```bash
curl -N http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"stream":true,"messages":[{"role":"user","content":"TBK m.49 kapsaminda emsal karar var mi?"}]}'
```

## Judicial runtime modes

- Disabled: mevzuat-only questions can run; judicial-only questions fail closed with a judicial runtime reason.
- Enabled and ready: exact and lexical judicial lanes can contribute source cards.
- Enabled but unavailable or corrupt: judicial questions fail closed instead of producing partial judicial answers.

## Source cards and verification

Responses include `source_cards`, `verification_status`, `retrieval_lanes`, `legal_rag_runtime_mode`, `judicial_runtime_enabled`, `judicial_ready`, and `latency_breakdown_ms`. Source cards are the public evidence contract for legislation and judicial decisions.

## Smoke tests

```bash
python3 scripts/ci/check_closed_runtime_state.py
JUDICIAL_RUNTIME_ENABLED=true python3 scripts/ci/check_closed_runtime_state.py
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_legal_rag_runtime_integration.py -q
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_legal_advisor_application_e2e.py -q
```

For a real endpoint and real processed indexes:

```bash
python3 scripts/run_final_legal_advisor_smoke.py
```

## Benchmarking

Benchmarks are external quality measurements, not product truth by themselves. Do not patch individual benchmark questions. Fix the generic runtime, retrieval, evidence, or verification cause and rerun the benchmark.

## Development policy

Keep runtime changes scoped, do not commit generated data or local secrets, keep legacy history archived, and keep validation tied to current runtime behavior. See `docs/DEVELOPMENT.md`.

## Legacy docs

Historical development material is archived under `docs/archive/` and mapped in `docs/LEGACY_DOCS.md`. It is retained for forensics only and is not current product guidance.
