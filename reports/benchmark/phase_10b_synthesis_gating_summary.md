# Phase 10B Synthesis Completeness Gating

## Change
- Runtime completeness now derives task-type must-have fact slots before marking an answer `complete_enough`.
- The answer contract now exposes `must_have_fact_slots`, `satisfied_fact_slots`, `missing_fact_slots`, and `rubric_aligned_completeness_class`.
- `complete_enough` is reserved for rows where all required slots are satisfied; structurally long answers with missing legal slots are classified separately.

## Slot Families
- Result / holding
- Governing source
- Exact source identity
- Article / span
- Temporal validity
- Exception / limitation
- Procedure / consequence
- Scenario applicability
- Hierarchy / conflict rule
- Document selection reason

## Verification
- `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/src/llm/client.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py`
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "completeness_synthesis" -q`
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_llm_client.py api-gateway/tests/test_chat_router.py -k "completeness_synthesis or rag_messages" -q`
- `python3 -m pytest tests/test_hukuk_ai_100_scorer.py tests/test_phase10_metric_registry.py tests/test_phase10_completeness_calibration.py -q`

## Expected Effect
- `complete_enough=100` should disappear on the next full runtime rerun.
- Runtime structural completeness should move directionally closer to private-rubric completeness.
- This is systemic task-type gating; it does not encode any benchmark QID-specific rule.
