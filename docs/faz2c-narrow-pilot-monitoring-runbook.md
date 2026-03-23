# FAZ 2C Narrow Pilot Monitoring Runbook

## Purpose
- Monitor the live `8000` promoted lane after controlled cutover.
- Turn rollback from an operator intuition into a repo-native evidence row.

## Monitoring Command

```bash
python3 scripts/faz2c/capture_narrow_pilot_snapshot.py \
  --base-url http://127.0.0.1:8000 \
  --output-path runtime_logs/faz2c_narrow_pilot_snapshot.json
```

Optional with auth:

```bash
python3 scripts/faz2c/capture_narrow_pilot_snapshot.py \
  --base-url http://127.0.0.1:8000 \
  --api-key "$API_KEY" \
  --output-path runtime_logs/faz2c_narrow_pilot_snapshot.json
```

## Bounded Watch Command

```bash
python3 scripts/faz2c/run_narrow_pilot_watch.py \
  --base-url http://127.0.0.1:8000 \
  --samples 3 \
  --sleep-seconds 5 \
  --jsonl-path runtime_logs/faz2c_narrow_pilot_watch.jsonl \
  --summary-path runtime_logs/faz2c_narrow_pilot_watch_summary.json
```

Optional with auth:

```bash
python3 scripts/faz2c/run_narrow_pilot_watch.py \
  --base-url http://127.0.0.1:8000 \
  --api-key "$API_KEY" \
  --samples 3 \
  --sleep-seconds 5 \
  --jsonl-path runtime_logs/faz2c_narrow_pilot_watch.jsonl \
  --summary-path runtime_logs/faz2c_narrow_pilot_watch_summary.json
```

## Timestamped Job Command

```bash
python3 scripts/faz2c/run_narrow_pilot_watch_job.py \
  --base-url http://127.0.0.1:8000 \
  --samples 3 \
  --sleep-seconds 5 \
  --output-dir runtime_logs/faz2c_watch_jobs
```

Optional with auth:

```bash
python3 scripts/faz2c/run_narrow_pilot_watch_job.py \
  --base-url http://127.0.0.1:8000 \
  --api-key "$API_KEY" \
  --samples 3 \
  --sleep-seconds 5 \
  --output-dir runtime_logs/faz2c_watch_jobs
```

## What The Snapshot Checks
- `GET /v1/health`
- `GET /v1/metrics` before and after smoke
- one cited smoke request against `/v1/chat/completions`
- audit event delta
- upstream usage delta
- successful chat counter delta
- refusal delta
- latency budget

## Pass Condition
- `rollback_recommended = false`
- cited smoke keeps the expected legal source
- audit and upstream usage counters advance
- no unexpected refusal signal appears

## Immediate Rollback Trigger
- `rollback_recommended = true`
- or any of the following in the snapshot:
  - `health_not_ok`
  - `cited_smoke_failed`
  - `audit_not_advancing`
  - `upstream_usage_not_advancing`
  - `chat_request_counter_not_advancing`
  - `unexpected_refusal_delta`
  - `latency_budget_exceeded`

## Rollback Command

```bash
bash scripts/faz2c/run_controlled_rollback.sh
```

## Expected Artifacts
- monitoring snapshot:
  - `runtime_logs/faz2c_narrow_pilot_snapshot.json`
- bounded watch ledger:
  - `runtime_logs/faz2c_narrow_pilot_watch.jsonl`
- bounded watch summary:
  - `runtime_logs/faz2c_narrow_pilot_watch_summary.json`
- timestamped job bundle:
  - `runtime_logs/faz2c_watch_jobs/<label>_<timestamp>/watch.jsonl`
  - `runtime_logs/faz2c_watch_jobs/<label>_<timestamp>/summary.json`
  - `runtime_logs/faz2c_watch_jobs/<label>_<timestamp>/manifest.json`
- rollback summary if rollback is executed:
  - `runtime_logs/faz2c_controlled_rollback_summary.json`

## Known Boundary
- This runbook covers narrow-pilot live monitoring on the DGX-native lane.
- It does not expand approval to broad production or customer-appliance scope.
