# FAZ 2C Wave 9 - canonical surface refresh

## Scope
- Objective: remove drift between cycle-local monitoring artefacts and the canonical top-level operator surfaces.

## Problem
- Integrated cycle was producing a fresh rollup and status report inside the timestamped cycle bundle.
- Canonical files under `runtime_logs/` could stay stale if the operator only ran the integrated cycle.

## Implemented artefacts
- canonical refresh in:
  - `scripts/faz2c/run_pilot_monitoring_cycle.py`
- tests:
  - `tests/test_faz2c_pilot_monitoring_cycle.py`
- runbook refresh:
  - `docs/faz2c-narrow-pilot-monitoring-runbook.md`

## Verification
- `python3 -m py_compile scripts/faz2c/run_pilot_monitoring_cycle.py` passed
- `pytest tests/test_faz2c_pilot_monitoring_cycle.py -q` passed

## Live result
- after the live integrated cycle, these top-level operator paths were refreshed by the same run:
  - `runtime_logs/faz2c_narrow_pilot_snapshot.json`
  - `runtime_logs/faz2c_watch_rollup.json`
  - `runtime_logs/faz2c_pilot_status_report.md`
- canonical read now matches the newest cycle bundle instead of an older archived job.
- refreshed canonical rollup:
  - `job_count = 4`
  - `latest_status = clean`
- refreshed canonical snapshot:
  - `rollback_recommended = false`
  - smoke latency `9152.60ms`

## Decision
- Wave 9 makes the integrated cycle the single canonical refresh path for dar kapsam pilot monitoring.
