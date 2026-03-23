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

## Rollup Command

```bash
python3 scripts/faz2c/build_pilot_watch_rollup.py \
  --watch-root runtime_logs/faz2c_watch_jobs \
  --output-path runtime_logs/faz2c_watch_rollup.json
```

## Status Report Command

```bash
python3 scripts/faz2c/build_pilot_status_report.py \
  --snapshot-path runtime_logs/faz2c_narrow_pilot_snapshot.json \
  --rollup-path runtime_logs/faz2c_watch_rollup.json \
  --output-path runtime_logs/faz2c_pilot_status_report.md
```

## Full Monitoring Cycle Command

```bash
python3 scripts/faz2c/run_pilot_monitoring_cycle.py \
  --base-url http://127.0.0.1:8000 \
  --samples 2 \
  --sleep-seconds 2 \
  --watch-root runtime_logs/faz2c_watch_jobs \
  --output-dir runtime_logs/faz2c_cycles
```

This command now refreshes stable latest surfaces alongside the timestamped bundle:
- `runtime_logs/faz2c_cycles/latest_cycle_manifest.json`
- `runtime_logs/faz2c_cycles/latest_rollup.json`
- `runtime_logs/faz2c_cycles/latest_pilot_status_report.md`
- `runtime_logs/faz2c_cycles/latest_cycle_index.json`

It also refreshes the canonical operator surfaces so one integrated cycle keeps the top-level read current:
- `runtime_logs/faz2c_narrow_pilot_snapshot.json`
- `runtime_logs/faz2c_watch_rollup.json`
- `runtime_logs/faz2c_pilot_status_report.md`

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
- watch rollup:
  - `runtime_logs/faz2c_watch_rollup.json`
- pilot status report:
  - `runtime_logs/faz2c_pilot_status_report.md`
- full monitoring cycle bundle:
  - `runtime_logs/faz2c_cycles/<label>_<timestamp>/cycle_manifest.json`
  - `runtime_logs/faz2c_cycles/<label>_<timestamp>/rollup.json`
  - `runtime_logs/faz2c_cycles/<label>_<timestamp>/pilot_status_report.md`
- latest cycle aliases:
  - `runtime_logs/faz2c_cycles/latest_cycle_manifest.json`
  - `runtime_logs/faz2c_cycles/latest_rollup.json`
  - `runtime_logs/faz2c_cycles/latest_pilot_status_report.md`
  - `runtime_logs/faz2c_cycles/latest_cycle_index.json`
- rollback summary if rollback is executed:
  - `runtime_logs/faz2c_controlled_rollback_summary.json`

## Known Boundary
- This runbook covers narrow-pilot live monitoring on the DGX-native lane.
- It does not expand approval to broad production or customer-appliance scope.
