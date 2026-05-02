# Phase 23 Controlled Cutover Plan

Generated: 2026-05-02T20:21:54Z

Scope: readiness plan only. Do not execute without explicit approval.

## 1. Pre-Cutover Checks

Run these checks before touching live `8000`:

```bash
cd /Users/btmacstudio/Projects/hukuk-ai

git fetch origin bt/hukuk-ai-100-benchmark-hardening
git rev-parse HEAD
git diff --name-only 6a85a5178d5dbd9e88677fd0acf6b92bdfdd0e76..HEAD

curl -sS --max-time 5 http://127.0.0.1:8000/v1/health
curl -sS --max-time 5 http://127.0.0.1:8000/v1/models
curl -sS --max-time 5 http://127.0.0.1:8081/v1/models
curl -sS --max-time 5 http://192.168.12.243:30000/v1/models
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Required pre-check state:

| Check | Required Value |
|---|---|
| Approved runtime SHA | `6a85a5178d5dbd9e88677fd0acf6b92bdfdd0e76` or later report-only commit |
| Runtime code drift after approved SHA | No code drift outside reports/benchmark artifacts |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Gateway model alias | `hukuk-ai-poc` |
| Embedding model | `intfloat/multilingual-e5-large-instruct` |
| Candidate collection exists | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Candidate entity count | `349403` |
| Candidate vector dimension | `1024` |
| Source key collision | `0` |
| Binding collision | `0` |
| Green lane | PASS |

Stop immediately if any required value differs.

## 2. Current Live Config Backup

Before any live process change, capture the current process and API state:

```bash
cd /Users/btmacstudio/Projects/hukuk-ai
BACKUP_DIR="reports/benchmark/cutover_backups/phase23_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

lsof -ti tcp:8000 > "$BACKUP_DIR/live_8000.pid"
ps eww -p "$(cat "$BACKUP_DIR/live_8000.pid")" > "$BACKUP_DIR/live_8000_ps_eww.txt"
curl -sS --max-time 5 http://127.0.0.1:8000/v1/health > "$BACKUP_DIR/live_8000_health.json"
curl -sS --max-time 5 http://127.0.0.1:8000/v1/models > "$BACKUP_DIR/live_8000_models.json"
git rev-parse HEAD > "$BACKUP_DIR/repo_head.txt"
```

Expected current live baseline:

| Field | Value |
|---|---|
| API URL | `http://127.0.0.1:8000/v1` |
| Lane | `current_serving_lane` |
| Model | `hukuk-ai-poc` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024` |
| Entity count | `349191` |
| Guardrails | `disabled` |
| Verification | `disabled` |

## 3. Candidate Config

Approved candidate for controlled benchmark/internal eval cutover:

| Field | Value |
|---|---|
| API URL after cutover | `http://127.0.0.1:8000/v1` |
| Candidate source URL | `http://127.0.0.1:8028/v1` |
| Lane | `phase23_controlled_cutover_benchmark` |
| Model | `hukuk-ai-poc` |
| DGX base URL | `http://192.168.12.243:30000/v1` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus URI | `http://localhost:19530` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Entity count | `349403` |
| Embedding backend | `remote` |
| Embedding base URL | `http://127.0.0.1:8081/v1` |
| Embedding model | `intfloat/multilingual-e5-large-instruct` |
| Guardrails | `false` for benchmark/internal eval only |
| Verification | `false` for benchmark/internal eval only |
| Presidio | `false` for benchmark/internal eval only |

## 4. Exact Env Changes

Only these binding changes are authorized after approval:

| Env Var | Current Live | Candidate |
|---|---|---|
| `MILVUS_COLLECTION` | `mevzuat_faz1_shadow_20260418_compat1024` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| `RELEASE_LANE_ID` | `current_serving_lane` or unset | `phase23_controlled_cutover_benchmark` |
| `API_VERSION_LABEL` | `2026-03-24-rc-h` or unset | `2026-05-02-phase23-controlled-cutover` |
| `PARITY_TRACE_ENABLED` | live-specific | `false` |

All other runtime-critical values must remain unchanged:

```bash
DGX_BASE_URL=http://192.168.12.243:30000/v1
DGX_MODEL=/models/merged_model_fabric_stage_20260321
MILVUS_ENABLED=true
MILVUS_URI=http://localhost:19530
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
USE_VERIFICATION=false
```

Benchmark/internal eval cutover command, to be executed only after approval:

```bash
cd /Users/btmacstudio/Projects/hukuk-ai
OLD_PID="$(lsof -ti tcp:8000)"
kill "$OLD_PID"

env \
  DGX_BASE_URL=http://192.168.12.243:30000/v1 \
  DGX_MODEL=/models/merged_model_fabric_stage_20260321 \
  MILVUS_ENABLED=true \
  MILVUS_URI=http://localhost:19530 \
  MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill \
  EMBEDDING_BACKEND=remote \
  EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
  EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
  RELEASE_LANE_ID=phase23_controlled_cutover_benchmark \
  RELEASE_CONTROLS_STRICT=true \
  API_VERSION_LABEL=2026-05-02-phase23-controlled-cutover \
  API_AUTH_ENABLED=false \
  API_AUTH_KEYS=benchmark \
  AUDIT_LOG_ENABLED=false \
  ALLOW_ANONYMOUS_INTERNAL_SMOKE=false \
  SESSION_STORE_BACKEND=memory \
  SESSION_STORE_REDIS_REQUIRED=false \
  SESSION_STORE_REDIS_PING_ON_STARTUP=false \
  TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
  PARITY_TRACE_ENABLED=false \
  RERANKER_ENABLED=false \
  GUARDRAILS_ENABLED=false \
  PRESIDIO_ENABLED=false \
  USE_VERIFICATION=false \
  api-gateway/.venv/bin/python -m uvicorn api-gateway.src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

## 5. Health Check Commands

Run immediately after cutover:

```bash
curl -sS --max-time 5 http://127.0.0.1:8000/v1/health
curl -sS --max-time 5 http://127.0.0.1:8000/v1/models
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Expected health:

```json
{
  "status": "ok",
  "service": "hukuk-ai-api-gateway",
  "lane": "phase23_controlled_cutover_benchmark",
  "retriever": "milvus",
  "guardrails": "disabled",
  "verification": "disabled"
}
```

Also verify process env contains:

```bash
ps eww -p "$(lsof -ti tcp:8000)" | tr ' ' '\n' | grep -E 'DGX_MODEL|MILVUS_COLLECTION|EMBEDDING_MODEL|RELEASE_LANE_ID|API_VERSION_LABEL|GUARDRAILS_ENABLED|PRESIDIO_ENABLED|USE_VERIFICATION'
```

## 6. Smoke QIDs

Run the required smoke against the post-cutover `8000` endpoint:

```bash
cd /Users/btmacstudio/Projects/hukuk-ai
RUN_DIR="reports/benchmark/runs/phase23_post_cutover_smoke_$(date -u +%Y%m%dT%H%M%SZ)"

python3 scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8000/v1 \
  --model hukuk-ai-poc \
  --out-dir "$RUN_DIR" \
  --qids MULGA-01 MULGA-05 TEB-04 TEB-06 CBG-01 CBKAR-08 YON-05 UY-01 KANUN-12 KKY-03 \
  --timeout 180 \
  --retries 1

python3 scripts/benchmark/score_hukuk_ai_100.py \
  --answers "$RUN_DIR/candidate_answers.csv" \
  --out-dir "$RUN_DIR"
```

Required smoke acceptance:

| Check | Required Value |
|---|---|
| answered | all |
| contract_valid | all |
| unsupported_confident_answer | 0 |
| source_key_v2_collision | 0 |
| binding_collision | 0 |
| `TEB-06` | PASS |
| `MULGA-*` | At least expected S7 candidate behavior |
| health/runtime error | none |

## 7. Rollback Commands

Rollback immediately if any stop condition is hit:

```bash
cd /Users/btmacstudio/Projects/hukuk-ai
BAD_PID="$(lsof -ti tcp:8000)"
kill "$BAD_PID"

env \
  DGX_BASE_URL=http://192.168.12.243:30000/v1 \
  DGX_MODEL=/models/merged_model_fabric_stage_20260321 \
  MILVUS_ENABLED=true \
  MILVUS_URI=http://localhost:19530 \
  MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024 \
  EMBEDDING_BACKEND=remote \
  EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
  EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
  RELEASE_LANE_ID=current_serving_lane \
  API_VERSION_LABEL=2026-03-24-rc-h \
  GUARDRAILS_ENABLED=false \
  PRESIDIO_ENABLED=false \
  USE_VERIFICATION=false \
  VERIFICATION_ENABLED=false \
  PARITY_TRACE_ENABLED=true \
  api-gateway/.venv/bin/python -m uvicorn api-gateway.src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Post-rollback verification:

```bash
curl -sS --max-time 5 http://127.0.0.1:8000/v1/health
curl -sS --max-time 5 http://127.0.0.1:8000/v1/models
ps eww -p "$(lsof -ti tcp:8000)" | tr ' ' '\n' | grep -E 'MILVUS_COLLECTION|RELEASE_LANE_ID|DGX_MODEL'
```

Expected rollback collection: `mevzuat_faz1_shadow_20260418_compat1024`.

## 8. Stop Conditions

Stop and rollback if any condition occurs:

- Health check fails.
- Model mismatch.
- Collection mismatch.
- Entity count mismatch.
- Source key collision.
- Binding collision.
- Contract invalid.
- Unsupported confident answer.
- Green lane fails.
- `TEB-06` fails in smoke.
- Any smoke request returns API/runtime error.
- `DGX_MODEL` is not `/models/merged_model_fabric_stage_20260321`.
- `MILVUS_COLLECTION` is not exactly the approved candidate collection after cutover.

## 9. Approval Block

Cutover is not approved until all fields below are filled by the owner:

```text
CUTOVER_APPROVED_BY:
APPROVAL_DATE:
APPROVED_SCOPE:
  benchmark_only | internal_eval | serving_candidate
ROLLBACK_OWNER:
```

This plan recommends only `benchmark_only` or `internal_eval`. `serving_candidate` requires a separate serving/productization policy gate.
