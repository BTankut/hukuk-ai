# Phase 24R-A Matched Runtime A/B Plan

## Scope

Phase24R is a controlled evidence phase. It does not merge, remediate, cut over live `8000`, open productization, open internal eval, or fine-tune.

## Planned Pair

| lane | api_url | collection | expected_entity_count |
|---|---|---|---:|
| BASE | `http://127.0.0.1:8035/v1` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | 349403 |
| CBY | `http://127.0.0.1:8036/v1` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06` | 349405 |

## Required Identical Fields

```text
git_sha
gateway_code
scorer
model
DGX_MODEL
prompt_behavior
retrieval_top_k
embedding_backend
embedding_model
guardrails_state
verification_state
source_catalog_config
source_supplement_config
```

Only `MILVUS_COLLECTION`, entity count, port, release lane label, and API version label may differ. Gateway code, model binding, prompt behavior, retrieval/top-k, embedding backend/model, guardrails, verification, scorer, source catalog, and source supplement config must be identical.

## Runtime Contract

```json
{
  "API_AUTH_ENABLED": "false",
  "API_AUTH_KEYS": "benchmark",
  "DGX_BASE_URL": "http://192.168.12.243:30000/v1",
  "DGX_MODEL": "/models/merged_model_fabric_stage_20260321",
  "EMBEDDING_BACKEND": "remote",
  "EMBEDDING_BASE_URL": "http://127.0.0.1:8081/v1",
  "EMBEDDING_MODEL": "intfloat/multilingual-e5-large-instruct",
  "GUARDRAILS_ENABLED": "false",
  "MILVUS_ENABLED": "true",
  "MILVUS_URI": "http://localhost:19530",
  "PARITY_TRACE_ENABLED": "false",
  "PRESIDIO_ENABLED": "false",
  "RERANKER_ENABLED": "false",
  "USE_VERIFICATION": "false"
}
```

## Targeted Smoke QIDs

```text
CBY-06
CBY-05
MULGA-01
MULGA-05
TEB-06
KANUN-12
YON-04
TUZUK-04
CBG-01
CBKAR-08
UY-01
```

## Stop Rules

Stop before full A/B if targeted smoke has contract invalid, unsupported confident answer, source key collision, binding collision, or critical guard regression. Do not commit large traces.

## Metadata

- generated_at_utc: `2026-05-04T20:14:31.335632+00:00`
- plan_authoring_git_sha: `fa93e931726dea322596f1710038d97f824f7c1d`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- benchmark_answer_key_for_runtime_changes: `not_used`
- live_8000_modified: `false`
