# Usage

This guide shows how to run and call the completed Hukuk-AI Legal Advisor.

## Install API gateway dependencies

```bash
cd api-gateway
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev,milvus]
cd ..
```

## Configure environment

Set environment variables directly or copy `.env.example` into your deployment system. Replace placeholders before running readiness:

```bash
export DGX_BASE_URL=<OPENAI_COMPATIBLE_BASE_URL>
export DGX_MODEL=<FINE_TUNED_MODEL_ID>
export DGX_API_KEY=<OPTIONAL_API_KEY_OR_NOT_NEEDED>
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

`<PROCESSED_JUDICIAL_DIR>` must contain generated judicial indexes such as `judicial_exact_lookup.sqlite`, `judicial_lexical_index.sqlite`, and `judicial_processed_coverage_audit.json`.

## Run readiness check

```bash
python3 scripts/check_legal_advisor_readiness.py
```

If `JUDICIAL_RUNTIME_ENABLED=true`, readiness requires readable judicial SQLite indexes. If `MILVUS_ENABLED=true`, readiness requires Milvus and embedding configuration values.

## Start API

```bash
scripts/run_legal_advisor_api.sh
```

Optional launch settings:

```bash
HOST=127.0.0.1 PORT=8000 scripts/run_legal_advisor_api.sh
```

## Call health

```bash
curl -s http://127.0.0.1:8000/v1/health
```

Important fields include `llm_configured`, `mevzuat_retriever_available`, `judicial_runtime_enabled`, `judicial_ready`, `judicial_readiness_failures`, `legal_rag_runtime_mode`, `runtime_mode`, `source_card_limit`, and timeout settings.

## Non-streaming chat

### Mevzuat-only question

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"TBK m.49 haksiz fiil sartlari nelerdir?"}]}'
```

### Judicial-only question

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Yargitay kararlarinda haksiz fiil tazminati nasil degerlendiriliyor?"}]}'
```

### Mixed mevzuat and judicial question

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"TBK m.49 kapsaminda haksiz fiil icin Yargitay uygulamasini da ozetle."}]}'
```

### Unsupported or fabrication request

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Kaynak kullanmadan emsal karar ve madde numarasi uydur."}]}'
```

Unsupported requests should return `blocked=true` and a machine-readable `final_reason`.

## Streaming chat

```bash
curl -N http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"stream":true,"messages":[{"role":"user","content":"TBK m.49 kapsaminda haksiz fiil icin Yargitay uygulamasini da ozetle."}]}'
```

The stream uses Server-Sent Events. Content chunks use OpenAI-compatible delta events. A metadata event carries fields such as `source_cards`, `verification_status`, `final_reason`, and runtime mode metadata before `[DONE]`.

## Interpret response fields

- `blocked`: `true` means the runtime refused or bounded the answer.
- `final_reason`: machine-readable reason such as missing evidence, disabled judicial runtime, retrieval timeout, LLM timeout, verification failure, or unsupported claim.
- `source_cards`: public evidence cards. They identify selected legislation or judicial decision evidence and are the only citation basis for the answer.
- `verification_status`: verifier result, commonly `pass`, `fail`, or `not_run`.
- `answer_contract`: extended legal advisor contract; use for debugging and audits, not as user-facing prose.
- `retrieval_lanes`: lanes that contributed evidence, such as mevzuat, judicial exact lookup, or judicial lexical retrieval.
