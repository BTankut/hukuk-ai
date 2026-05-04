# Phase 24R-B Runtime Pair Verification

## Outcome

```text
both_runtimes_healthy = true
both_models_ok = true
collections_loaded = true
entity_counts_expected = true
only_allowed_env_diffs = true
passed = true
```

## Pair

| lane | api_url | pid | collection | entity_count | load_state | health | models_ok |
|---|---|---:|---|---:|---|---|---:|
| BASE | `http://127.0.0.1:8035/v1` | 26325 | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | 349403 | `Loaded` | `ok` | true |
| CBY | `http://127.0.0.1:8036/v1` | 26422 | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06` | 349405 | `Loaded` | `ok` | true |

## Env Diff Check

Only these env differences were observed:

```json
{
  "API_VERSION_LABEL": {
    "allowed": true,
    "base": "2026-05-04-phase24r-base-matched-ab",
    "cby": "2026-05-04-phase24r-cby-matched-ab"
  },
  "MILVUS_COLLECTION": {
    "allowed": true,
    "base": "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill",
    "cby": "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06"
  },
  "RELEASE_LANE_ID": {
    "allowed": true,
    "base": "phase24r_base_matched_ab",
    "cby": "phase24r_cby_matched_ab"
  }
}
```

## Shared Runtime Evidence

```text
git_sha = a1122c31614d643098cf11d944d63ea9a797bbff
DGX_MODEL = /models/merged_model_fabric_stage_20260321
EMBEDDING_MODEL = intfloat/multilingual-e5-large-instruct
GUARDRAILS_ENABLED = false
PRESIDIO_ENABLED = false
USE_VERIFICATION = false
RERANKER_ENABLED = false
PARITY_TRACE_ENABLED = false
```

## Live 8000 Probe

```json
{"api_version": "2026-05-03-phase23R-E-benchmark-only-cutover", "guardrails": "disabled", "lane": "phase22f_s7_full_shadow", "retriever": "milvus", "service": "hukuk-ai-api-gateway", "status": "ok", "verification": "disabled"}
```

Live `8000` was not modified.
