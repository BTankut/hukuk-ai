# Configuration

All runtime configuration is environment-driven. `.env.example` is a template; production deployments should load real values from the deployment environment or secret store.

## LLM endpoint

| Variable | Meaning |
| --- | --- |
| `DGX_BASE_URL` | OpenAI-compatible base URL, ending in `/v1`. |
| `DGX_MODEL` | Fine-tuned model id sent to the chat completion endpoint. |
| `DGX_API_KEY` | Optional API key; use a secret value when the endpoint requires auth. |
| `DGX_TEMPERATURE_DEFAULT` | Default legal advisor generation temperature. Final delivery uses deterministic `0`. |
| `DGX_MAX_TOKENS_DEFAULT` | Default max completion tokens for legal answers. |
| `DGX_REQUEST_TIMEOUT_SECONDS` | HTTP timeout for the underlying LLM client. |
| `LEGAL_ADVISOR_LLM_ENABLED` | Enables real legal advisor LLM generation. When disabled in tests, deterministic fallback behavior may be used. |

## Mevzuat retrieval and embeddings

| Variable | Meaning |
| --- | --- |
| `MILVUS_ENABLED` | Enables Milvus-backed legislation retrieval. |
| `MILVUS_URI` | Milvus endpoint, commonly `http://localhost:19530`. |
| `MILVUS_COLLECTION` | Collection containing mevzuat chunks. |
| `EMBEDDING_BACKEND` | `remote` for an OpenAI-compatible embedding service, or `hashing` for deterministic tests. |
| `EMBEDDING_BASE_URL` | OpenAI-compatible embedding base URL. |
| `EMBEDDING_MODEL` | Embedding model name. |
| `EMBEDDING_DIM` | Embedding vector dimension expected by the collection. |
| `EMBEDDING_TIMEOUT` | Embedding request timeout in seconds. |

## Judicial runtime

| Variable | Meaning |
| --- | --- |
| `JUDICIAL_RUNTIME_ENABLED` | Enables judicial decision retrieval. |
| `JUDICIAL_PROCESSED_DIR` | Directory containing generated processed judicial indexes. |
| `JUDICIAL_EXACT_LOOKUP_PATH` | Exact lookup SQLite file. Defaults to `JUDICIAL_PROCESSED_DIR/judicial_exact_lookup.sqlite`. |
| `JUDICIAL_LEXICAL_INDEX_PATH` | Lexical SQLite file. Defaults to `JUDICIAL_PROCESSED_DIR/judicial_lexical_index.sqlite`. |
| `JUDICIAL_CHUNK_REFS_PATH` | Chunk reference store. The exact lookup SQLite file is valid when it contains `chunk_refs`. |

## Legal RAG limits and timeouts

| Variable | Meaning |
| --- | --- |
| `LEGAL_RAG_RETRIEVAL_TIMEOUT_MS` | Retrieval deadline. Timeout causes fail-closed behavior. |
| `LEGAL_RAG_LLM_TIMEOUT_MS` | Legal answer generation deadline. Timeout causes fail-closed behavior. |
| `LEGAL_RAG_VERIFICATION_TIMEOUT_MS` | Post-generation verifier deadline. |
| `LEGAL_RAG_MAX_TOTAL_EVIDENCE_CHARS` | Evidence packet text budget. |
| `LEGAL_RAG_MAX_SOURCE_CARDS` | Public source card cap. |
| `LEGAL_RAG_MAX_QUERY_CHARS` | Request query length cap. |

## Runtime modes

- Judicial disabled: legislation evidence may still answer mevzuat questions. Judicial-only questions fail closed instead of receiving partial judicial answers.
- Judicial enabled and ready: exact lookup and lexical judicial lanes can provide source cards.
- Judicial enabled but unavailable or corrupt: judicial questions fail closed with readiness failures in health metadata.
- LLM enabled: the configured fine-tuned endpoint is called and the output is verified.
- Deterministic test fallback: test configurations can disable the legal advisor LLM path; this is not the production serving mode.

## Safe example values

Use placeholders for non-local infrastructure:

```bash
DGX_BASE_URL=<OPENAI_COMPATIBLE_BASE_URL>
DGX_MODEL=<FINE_TUNED_MODEL_ID>
JUDICIAL_PROCESSED_DIR=<PROCESSED_JUDICIAL_DIR>
```

Localhost defaults are acceptable for local Milvus and embedding services:

```bash
MILVUS_URI=http://localhost:19530
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
```
