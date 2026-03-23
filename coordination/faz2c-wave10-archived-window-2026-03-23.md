# FAZ 2C Wave 10 - archived monitoring window

## Scope
- Objective: package repeated narrow-pilot monitoring cycles into one archived operator window.

## Implemented artefacts
- archived window runner:
  - `scripts/faz2c/run_pilot_monitoring_window.py`
- tests:
  - `tests/test_faz2c_pilot_monitoring_window.py`
- runbook refresh:
  - `docs/faz2c-narrow-pilot-monitoring-runbook.md`

## Verification
- `python3 -m py_compile scripts/faz2c/run_pilot_monitoring_window.py` passed
- `pytest tests/test_faz2c_pilot_monitoring_window.py -q` passed

## Live result
- one archived operator window now emits:
  - `runtime_logs/faz2c_window_jobs/<label>_<timestamp>/cycle_manifests.jsonl`
  - `runtime_logs/faz2c_window_jobs/<label>_<timestamp>/window_summary.json`
  - `runtime_logs/faz2c_window_jobs/<label>_<timestamp>/window_report.md`
  - `runtime_logs/faz2c_window_jobs/<label>_<timestamp>/window_manifest.json`
- the same run refreshes stable latest aliases:
  - `runtime_logs/faz2c_window_jobs/latest_window_summary.json`
  - `runtime_logs/faz2c_window_jobs/latest_window_report.md`
  - `runtime_logs/faz2c_window_jobs/latest_window_manifest.json`

## Decision
- Wave 10 turns periodic narrow-pilot operation into a repo-native archived window instead of a series of unrelated manual cycles.
