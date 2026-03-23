# FAZ 2C Wave 8 - latest monitoring surface

## Scope
- Objective: expose the newest integrated monitoring cycle through stable operator-facing paths.

## Implemented artefacts
- latest surface refresh in:
  - `scripts/faz2c/run_pilot_monitoring_cycle.py`
- tests:
  - `tests/test_faz2c_pilot_monitoring_cycle.py`
- runbook refresh:
  - `docs/faz2c-narrow-pilot-monitoring-runbook.md`

## Verification
- `python3 -m py_compile scripts/faz2c/run_pilot_monitoring_cycle.py` passed
- `pytest tests/test_faz2c_pilot_monitoring_cycle.py -q` passed

## Live result
- newest cycle still produces a timestamped bundle under:
  - `runtime_logs/faz2c_cycles/<label>_<timestamp>/`
- the same run now refreshes stable aliases:
  - `runtime_logs/faz2c_cycles/latest_cycle_manifest.json`
  - `runtime_logs/faz2c_cycles/latest_rollup.json`
  - `runtime_logs/faz2c_cycles/latest_pilot_status_report.md`
  - `runtime_logs/faz2c_cycles/latest_cycle_index.json`

## Decision
- Wave 8 removes the remaining operator lookup friction.
- A pilot operator can now read the newest cycle decision without resolving a timestamped directory first.
