# Data And Indexes

Generated corpora, indexes, logs, and benchmark outputs are external artifacts. They are not committed to this repository.

## Mevzuat index

The mevzuat retriever expects an official legislation corpus already indexed in Milvus. Configure it with:

```bash
MILVUS_ENABLED=true
MILVUS_URI=http://localhost:19530
MILVUS_COLLECTION=<MEVZUAT_COLLECTION>
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
EMBEDDING_DIM=1024
```

The embedding dimension must match the Milvus collection.

## Judicial processed indexes

Judicial runtime uses generated SQLite artifacts under:

```bash
JUDICIAL_PROCESSED_DIR=<PROCESSED_JUDICIAL_DIR>
```

Expected files:

```text
judicial_exact_lookup.sqlite
judicial_lexical_index.sqlite
judicial_processed_coverage_audit.json
```

The exact lookup SQLite file is expected to contain decision lookup data and chunk references. The lexical SQLite file is expected to contain judicial chunks and an FTS table.

Local example used during final verification:

```text
/Users/btmacstudio/Projects/yargi/_work/final_package/processed/
```

This path is an operator-local example, not a repository default or deployment requirement.

## Readiness validation

```bash
python3 scripts/check_legal_advisor_readiness.py
```

With `JUDICIAL_RUNTIME_ENABLED=true`, readiness opens the SQLite files in read-only mode and checks required tables. Missing or corrupt indexes prevent judicial runtime from serving judicial answers.

## Operational scale context

Previous processed corpus runs were on the order of:

- about 1.5M raw rows,
- about 623k canonical decisions,
- about 802k chunks.

These numbers are operational context only. The running service should trust readiness and coverage checks for the actual configured artifact set.

## What not to commit

Do not commit raw judicial corpus files, processed SQLite indexes, generated Milvus data, benchmark run outputs, logs, local secrets, private endpoint values, or generated corpus audit dumps unless a small fixture is explicitly required by tests.

## Regeneration and verification

Use the existing ingestion and shadow retrieval scripts in `api-gateway/src/data_pipeline/judicial/` and the focused tests documented in `docs/EVALUATION_AND_SMOKE.md`. Keep regenerated artifacts outside the repository and point the runtime at them with environment variables.
