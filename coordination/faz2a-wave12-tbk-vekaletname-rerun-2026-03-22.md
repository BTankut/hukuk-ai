# FAZ 2A Wave 12 — `tbk_vekaletname` source-tail closure

## Scope
- Objective: close the residual `tbk_vekaletname` companion-source tail inside the `tbk_critical` diagnostic family.
- Strategy: keep retrieval untouched and force narrow deterministic answer discipline for eight mandate-law residual questions:
  - `TBK-101`
  - `TBK-102`
  - `TBK-115`
  - `TBK-142`
  - `TBK-143`
  - `TBK-144`
  - `TBK-145`
  - `TBK-146`

## Implemented deterministic packages
- `termination pair` package
  - `TBK-101` -> `TBK m.512 + TBK m.513`
  - `TBK-115` -> `TBK m.512 + TBK m.513`
  - `TBK-144` -> `TBK m.513 + TBK m.512`
  - `TBK-145` -> `TBK m.514 + TBK m.512`
- `duty / scope split` package
  - `TBK-102` -> `TBK m.509 + TBK m.504`
  - `TBK-146` -> `TBK m.503 + TBK m.509`
- `authority / third-party effect` package
  - `TBK-142` -> `TBK m.507 + TBK m.162`
  - `TBK-143` -> `TBK m.504 + TBK m.46`

## Verification
- Local verification PASS:
  - `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py`
  - `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
- Fresh runtime lanes:
  - baseline `8049`
  - candidate `8050`
- Health PASS:
  - `http://127.0.0.1:8049/v1/health`
  - `http://127.0.0.1:8050/v1/health`

## Focused `tbk_vekaletname` mini-slice
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_vekaletname_baseline_wave12_20260322.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_vekaletname_candidate_wave12_20260322.json`
- Result:
  - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`

## Full matched `tbk_critical` rerun
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave12_20260322.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave12_20260322.json`

## Delta vs Wave 11
- Baseline summary:
  - correct source `90.16% -> 95.08%`
  - avg keyword coverage `35.60% -> 38.99%`
  - avg response `10624.3 ms -> 7889.7 ms`
- Candidate summary:
  - correct source `88.52% -> 94.26%`
  - phrase hit rate `36.36% -> 45.45%`
  - avg response `19985.2 ms -> 16444.3 ms`
- `tbk_vekaletname` category:
  - baseline `80.56% -> 100.0%`
  - candidate `77.78% -> 100.0%`

## Decision
- `tbk_vekaletname` residual source-tail is closed for both lanes.
- No new hallucination debt was introduced.
- The gain generalized cleanly to the full `tbk_critical` matched rerun.
- The active residual set is now concentrated in `tbk_kefalet` plus one service-law companion-source miss (`TBK-137`).

## Remaining residuals after Wave 12
- Baseline:
  - `TBK-091`
  - `TBK-137`
  - `TBK-151`
  - `TBK-153`
  - `TBK-155`
  - `TBK-156`
- Candidate:
  - `TBK-091`
  - `TBK-137`
  - `TBK-150`
  - `TBK-151`
  - `TBK-153`
  - `TBK-155`
  - `TBK-156`

## Next active target
- Move from `tbk_vekaletname` to `tbk_kefalet` source-tail closure.
- Fold `TBK-137` into the same wave as the only non-kefalet residual companion-source miss.
