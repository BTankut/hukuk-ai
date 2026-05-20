# FAZ 2C Wave 5 - watch rollup

## Scope
- Objective: build a single rollup surface across archived narrow-pilot watch jobs.

## Implemented artefacts
- rollup builder:
  - `scripts/faz2c/build_pilot_watch_rollup.py`
- tests:
  - `tests/test_faz2c_pilot_watch_rollup.py`
- runbook refresh:
  - `docs/faz2c-narrow-pilot-monitoring-runbook.md`

## Verification
- `python3 -m py_compile scripts/faz2c/build_pilot_watch_rollup.py` passed
- `pytest tests/test_faz2c_pilot_watch_rollup.py -q` passed

## Live rollup result
- rollup:
  - `runtime_logs/faz2c_watch_rollup.json`
- archived job count:
  - `1`
- clean job count:
  - `1`
- rollback job count:
  - `0`
- latest status:
  - `clean`
- latest bundle:
  - `runtime_logs/faz2c_watch_jobs/narrow_pilot_watch_20260323T091116Z`
- aggregated latency:
  - `avg = 9389.92ms`
  - `max = 9389.92ms`

## Decision
- Wave 5 adds a repo-native trend/rollup surface on top of archived watch jobs.
- The operator no longer needs to open individual bundles to see:
  - latest status
  - clean vs rollback job count
  - aggregated latency read
- First live rollup stayed green.
