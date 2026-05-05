# Phase 24U-A Trace-Normalized Matched A/B Plan

Generated UTC: `2026-05-05T12:10:58Z`  
Branch: `bt/hukuk-ai-100-benchmark-hardening`  
Git SHA: `e803eee2cbafeed07cae02b3cffee6de5085801e`

## Boundary

- Live `8000` will not be modified.
- Productization, internal eval, and fine-tuning remain closed.
- No logic patch, no QID-specific runtime branch, no answer-key-driven change.
- Trace-off full runs are not accepted as productization evidence.
- Large run traces will not be staged or committed; only summary/decision artifacts will be committed.

## Live State Snapshot

- Health: `ok`
- Lane: `phase22f_s7_full_shadow`
- API version: `2026-05-03-phase23R-E-benchmark-only-cutover`
- Model exposed with benchmark auth: `hukuk-ai-poc`
- Guardrails: `disabled`
- Verification: `disabled`
- Retriever: `milvus`

## Collections

| Label | Collection | Row count | Load state |
|---|---:|---:|---|
| BASE | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | 349403 | Loaded |
| CBY | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06` | 349405 | Loaded |

Preflight: candidate ports `8037`, `8038`, and `8039` are free.

## Runtime Parity Contract

All candidate runtimes use the same git SHA, gateway code, scorer, prompt behavior, top-k behavior, embedding backend/model, model, DGX model, guardrails, verification, and source catalog/supplement config unless explicitly listed below.

Shared critical env:

```text
DGX_BASE_URL=http://192.168.12.243:30000/v1
DGX_MODEL=/models/merged_model_fabric_stage_20260321
MILVUS_ENABLED=true
MILVUS_URI=http://localhost:19530
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
RERANKER_ENABLED=false
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
USE_VERIFICATION=false
API_AUTH_KEYS=benchmark
```

Intended differences only:

| Runtime | API | Collection | Supplement setting | Lane |
|---|---|---|---|---|
| BASE | `http://127.0.0.1:8037/v1` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | current/default | `phase24u_base_trace_on` |
| CBY | `http://127.0.0.1:8038/v1` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06` | current/default | `phase24u_cby_trace_on` |
| ABLATION | `http://127.0.0.1:8039/v1` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=false` | `phase24u_base_supplement_ablation` |

## Benchmark Contract

Trace-on is mandatory. The runner default is trace-on; do not pass `--no-trace`.

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8037/v1 \
  --model hukuk-ai-poc \
  --api-key benchmark \
  --out-dir reports/benchmark/runs/<phase24u-run-dir> \
  --allow-missing-trace

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/<phase24u-run-dir>/candidate_answers.csv \
  --out-dir reports/benchmark/runs/<phase24u-run-dir>/score
```

`--allow-missing-trace` is diagnostic-only tolerance; any missing trace is a stop/audit condition in the generated summary.

## Reference Scores

| Reference | Raw | Pass | Notes |
|---|---:|---:|---|
| Phase23R-E | 816.86 | 91 | `include_trace=true` accepted baseline |
| Phase24T-D current trace-on | 805.09 | 89 | current-code trace-normalized reproduction |

## Stop Rules

Stop if live `8000` would be modified, trace-on cannot be used, runtime provenance differs beyond the intended collection/env flag, contract invalid appears, unsupported confident appears, `source_key_v2` or binding collision appears, or large trace files are staged.

## Commit Plan

1. `Plan Phase 24U trace-normalized matched A/B`
2. `Run Phase 24U BASE trace-on full benchmark`
3. `Run Phase 24U CBY trace-on full benchmark`
4. `Run Phase 24U source supplement ablation`
5. `Attribute Phase 24U source supplement drift rows`
6. `Record Phase 24U trace-normalized ablation decision`
7. `Report Phase 24U trace-normalized ablation outcome`
