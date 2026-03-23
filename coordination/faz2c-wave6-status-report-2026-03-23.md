# FAZ 2C Wave 6 - pilot status report

## Scope
- Objective: render a single markdown handoff/status surface from the latest snapshot and archived watch rollup.

## Implemented artefacts
- status report builder:
  - `scripts/faz2c/build_pilot_status_report.py`
- tests:
  - `tests/test_faz2c_pilot_status_report.py`
- runbook refresh:
  - `docs/faz2c-narrow-pilot-monitoring-runbook.md`

## Verification
- `python3 -m py_compile scripts/faz2c/build_pilot_status_report.py` passed
- `pytest tests/test_faz2c_pilot_status_report.py -q` passed

## Live report result
- markdown report:
  - `runtime_logs/faz2c_pilot_status_report.md`
- executive read:
  - latest rollup status = `clean`
  - latest snapshot rollback recommended = `False`
  - current live read = `stay on promoted lane`
- latest archived job:
  - `runtime_logs/faz2c_watch_jobs/narrow_pilot_watch_20260323T091116Z`
- operator action:
  - stay on promoted lane
  - continue periodic archived watch jobs

## Decision
- Wave 6 adds a human-readable handoff surface on top of:
  - latest live snapshot
  - archived watch rollup
  - latest archived job summary
- The operator can now read one markdown file instead of raw JSON surfaces.
