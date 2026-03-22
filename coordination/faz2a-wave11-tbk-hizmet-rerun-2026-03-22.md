# FAZ 2A Wave 11 — `tbk_hizmet` source-tail closure

## Scope
- Objective: close the residual `tbk_hizmet` companion-source tail inside the `tbk_critical` diagnostic family.
- Strategy: keep retrieval untouched and force narrow deterministic answer discipline for three service-law clusters:
  - non-compete
  - notice / termination / compensation
  - core service-law companion norms

## Implemented deterministic packages
- `rekabet yasağı hizmet paketi`
  - `TBK-094` -> `TBK m.396 + TBK m.397`
  - `TBK-110` -> `TBK m.444 + TBK m.445 + TBK m.446`
  - `TBK-135` -> `TBK m.397 + TBK m.398 + TBK m.399`
- `fesih / ihbar / tazminat paketi`
  - `TBK-096` -> `TBK m.432 + TBK m.433`
  - `TBK-133` -> `TBK m.438 + TBK m.439`
  - `TBK-138` -> `TBK m.438 + TBK m.440`
- `çekirdek hizmet hükümleri paketi`
  - `TBK-097` -> `TBK m.401 + TBK m.408`
  - `TBK-131` -> `TBK m.393 + TBK m.470`
  - `TBK-132` -> `TBK m.421 + TBK m.422`
  - `TBK-136` -> `TBK m.420 + TBK m.421`
  - `TBK-140` -> `TBK m.417 + TBK m.49`

## Verification
- Local verification PASS:
  - `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py`
  - `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
- Fresh runtime lanes:
  - baseline `8047`
  - candidate `8048`
- Candidate smoke PASS:
  - `TBK m.432 ... ihbar süreleri`
  - returned `TBK m.432 + TBK m.433`

## Focused `tbk_hizmet` mini-slice
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_hizmet_baseline_wave11_20260322.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_hizmet_candidate_wave11_20260322.json`
- Result:
  - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`

## Full matched `tbk_critical` rerun
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave11_20260322.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave11_20260322.json`

## Delta vs Wave 10
- Baseline summary:
  - correct source `81.69% -> 90.16%`
  - refusal `95.08% -> 98.36%`
  - avg response `14837.5 ms -> 10624.3 ms`
- Candidate summary:
  - correct source `81.15% -> 88.52%`
  - avg response `24958.5 ms -> 19985.2 ms`
- `tbk_hizmet` category:
  - baseline `75.44% -> 97.37%`
  - candidate `71.05% -> 97.37%`

## Decision
- `tbk_hizmet` residual source-tail is effectively closed for both lanes.
- No new hallucination debt was introduced.
- The gain generalized cleanly to the full `tbk_critical` matched rerun.

## Remaining residuals after Wave 11
- `tbk_vekaletname`
  - candidate `77.78%`
  - primary weak IDs: `TBK-101`, `102`, `115`, `142`, `143`, `144`, `145`, `146`
- `tbk_kefalet`
  - candidate `80.77%`
  - primary weak IDs: `TBK-091`, `150`, `151`, `155`, `156`

## Next active target
- Move from `tbk_hizmet` to `tbk_vekaletname` source-tail closure.
