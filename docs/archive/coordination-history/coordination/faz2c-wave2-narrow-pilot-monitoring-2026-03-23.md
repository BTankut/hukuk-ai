# FAZ 2C Wave 2 — narrow pilot monitoring

## Scope
- Objective: close the first live monitoring row after the controlled cutover.

## Implemented artefacts
- monitoring script:
  - `scripts/faz2c/capture_narrow_pilot_snapshot.py`
- monitoring runbook:
  - `docs/faz2c-narrow-pilot-monitoring-runbook.md`
- tests:
  - `tests/test_faz2c_pilot_monitoring.py`

## Verification
- `python3 -m py_compile scripts/faz2c/capture_narrow_pilot_snapshot.py` passed
- `pytest tests/test_faz2c_pilot_monitoring.py -q` passed
- `pytest api-gateway/tests/test_llm_client.py api-gateway/tests/test_guardrails_pipeline_smoke.py tests/test_faz2c_pilot_monitoring.py -q` passed

## Live monitoring target
- live promoted lane:
  - `http://127.0.0.1:8000`

## Live snapshot result
- snapshot:
  - `runtime_logs/faz2c_narrow_pilot_snapshot.json`
- status:
  - `rollback_recommended = false`
- health:
  - `ok`
- smoke:
  - cited legal answer returned cleanly
  - wrapper leakage fixed on live `8000` lane
  - latency: `10357.38ms`
- metrics delta:
  - `audit_events_delta = 1`
  - `upstream_usage_delta = 1`
  - `successful_chat_delta = 1`
  - `refusal_delta = 0`

## Live parsing hardening
- root issue:
  - NeMo `GenerationResponse(response=[...])` wrapper text could leak into final user-facing `content`
- fix applied:
  - `api-gateway/src/llm/client.py`
  - `api-gateway/src/guardrails/pipeline.py`
- protection added:
  - metadata-tail wrapper parsing
  - object/dict nested `content` and `response` parsing
  - direct `GenerationResponse.response` list parsing
  - regression tests for those branches

## Decision
- Wave 2 closes the repo-native monitoring package milestone.
- Live lane remains on promoted `dgx1 merged` candidate.
- The next live operator action remains binary:
  - continue narrow pilot while snapshots stay clean
  - execute rollback if a future snapshot recommends rollback
