# FAZ 2C Wave 3 - bounded pilot watch proof

## Scope
- Objective: move narrow-pilot monitoring from a single snapshot into a bounded multi-sample watch proof.

## Implemented artefacts
- bounded watch runner:
  - `scripts/faz2c/run_narrow_pilot_watch.py`
- tests:
  - `tests/test_faz2c_pilot_watch.py`
- runbook refresh:
  - `docs/faz2c-narrow-pilot-monitoring-runbook.md`

## Verification
- `python3 -m py_compile scripts/faz2c/run_narrow_pilot_watch.py` passed
- `pytest tests/test_faz2c_pilot_watch.py -q` passed

## Live proof result
- summary:
  - `runtime_logs/faz2c_narrow_pilot_watch_summary.json`
- ledger:
  - `runtime_logs/faz2c_narrow_pilot_watch.jsonl`
- sampled rows:
  - `3`
- clean rows:
  - `3`
- rollback rows:
  - `0`
- latency:
  - `avg = 9787.34ms`
  - `max = 10370.98ms`
- watch decision:
  - `final_status = clean`
  - `first_rollback_sample = null`

## Live proof target
- live promoted lane:
  - `http://127.0.0.1:8000`

## Decision
- Wave 3 adds a bounded watch surface for dar kapsam pilot operations.
- The watch remains intentionally narrow:
  - repeated snapshot capture
  - ledger + summary output
  - rollback recommendation if any sampled row turns red
- The first bounded live proof stayed green across all three samples.
