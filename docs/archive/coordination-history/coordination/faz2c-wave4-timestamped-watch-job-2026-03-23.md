# FAZ 2C Wave 4 - timestamped watch job

## Scope
- Objective: turn bounded watch proof into a timestamped operator job that archives each run as a bundle.

## Implemented artefacts
- timestamped watch job:
  - `scripts/faz2c/run_narrow_pilot_watch_job.py`
- tests:
  - `tests/test_faz2c_pilot_watch_job.py`
- runbook refresh:
  - `docs/faz2c-narrow-pilot-monitoring-runbook.md`

## Verification
- `python3 -m py_compile scripts/faz2c/run_narrow_pilot_watch_job.py` passed
- `pytest tests/test_faz2c_pilot_watch_job.py -q` passed

## Live proof result
- manifest:
  - `runtime_logs/faz2c_watch_jobs/narrow_pilot_watch_20260323T091116Z/manifest.json`
- summary:
  - `runtime_logs/faz2c_watch_jobs/narrow_pilot_watch_20260323T091116Z/summary.json`
- ledger:
  - `runtime_logs/faz2c_watch_jobs/narrow_pilot_watch_20260323T091116Z/watch.jsonl`
- sampled rows:
  - `2`
- clean rows:
  - `2`
- rollback rows:
  - `0`
- latency:
  - `avg = 9389.92ms`
  - `max = 9472.84ms`
- archived job decision:
  - `final_status = clean`

## Live proof target
- live promoted lane:
  - `http://127.0.0.1:8000`

## Decision
- Wave 4 converts narrow-pilot monitoring into a repeatable archived operator job.
- Each run now emits:
  - `watch.jsonl`
  - `summary.json`
  - `manifest.json`
- Exit code stays binary:
  - `0` when the sampled run stays clean
  - `1` when any sampled row recommends rollback
- First archived live job bundle stayed green.
