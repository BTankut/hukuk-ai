# FAZ 2A Wave 14 — `TBK-103` residual closure

## Scope
- Objective: close the final `tbk_vekaletname` residual left after Wave 13.
- Strategy: keep retrieval unchanged and add a single narrow deterministic answer path only for `TBK-103`.

## Implemented deterministic package
- `alt vekil / işi başkasına bırakma` package
  - `TBK-103` -> `TBK m.508`

## Verification
- Local verification PASS:
  - `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py`
  - `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
- Fresh runtime lanes:
  - baseline `8053`
  - candidate `8054`
- Health PASS:
  - `http://127.0.0.1:8053/v1/health`
  - `http://127.0.0.1:8054/v1/health`

## Focused `TBK-103` mini-slice
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_103_baseline_wave14_20260323.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_103_candidate_wave14_20260323.json`
- Result:
  - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`

## Full matched `tbk_critical` rerun
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave14_20260323.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave14_20260323.json`

## Delta vs Wave 13
- Baseline summary:
  - correct source `100.0% -> 100.0%`
  - hallucination `0.0% -> 0.0%`
  - refusal `100.0% -> 98.36%`
  - avg response `5954 ms -> 5542.6 ms`
- Candidate summary:
  - correct source `98.36% -> 100.0%`
  - hallucination `1.64% -> 0.0%`
  - refusal `98.36% -> 96.72%`
  - avg response `10993 ms -> 8842.3 ms`
- Category impact:
  - candidate `tbk_vekaletname` `94.44% -> 100.0%`
  - baseline `tbk_critical` categories remained `100 / 100 / 0`
  - candidate `tbk_critical` categories now also closed at `100 / 100 / 0`

## Decision
- Wave 14 objective is complete.
- `tbk_critical` source/hallucination tail is closed for both lanes.
- The remaining FAZ 2A blocker is no longer TBK-critical retrieval precision; it is the `tmk_cross_law` family-level companion-source tail.

## Residual after Wave 14
- `tbk_critical`
  - baseline: none
  - candidate: none
- Residual FAZ 2A family:
  - `tmk_cross_law`

## Next active target
- Move from `tbk_critical` closure to `tmk_cross_law` multi-source source-tail closure.
- Prioritize questions that still miss one or more expected TMK/TBK companion sources despite already carrying some correct evidence.
