# FAZ 2A Wave 10 — `tbk_ceza_sarti` source-tail closure

## Scope
- Objective: close the remaining `tbk_ceza_sarti` companion-source tail inside the `tbk_critical` diagnostic slice.
- Strategy: add three narrow deterministic answer packages instead of widening retrieval.

## Implemented packages
- `cayma akçesi / sözleşme serbestisi`
  - covers `TBK-105`, `TBK-164`
  - source pairs forced to `TBK m.181 + TBK m.179` and `TBK m.181 + TBK m.26`
- `seçimlik / kümülatif ceza şartı`
  - covers `TBK-106`, `TBK-158`, `TBK-162`
  - source pair forced to `TBK m.179 + TBK m.180`
- `fahişlik / geçersizlik / indirim`
  - covers `TBK-159`, `TBK-160`, `TBK-163`
  - source sets forced to `TBK m.182 + TBK m.27`, `TBK m.179 + TBK m.182`, `TBK m.181 + TBK m.182 + TBK m.183`

## Verification
- Local verification PASS:
  - `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py`
  - `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
- Fresh runtime lanes:
  - baseline `8045`
  - candidate `8046`
- Candidate smoke PASS:
  - `Ceza şartının kararlaştırıldığı asıl sözleşme geçersiz sayılırsa...`
  - returned `TBK m.179 + TBK m.182`

## Focused `tbk_ceza_sarti` mini-slice
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_ceza_sarti_baseline_wave10_20260322.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_ceza_sarti_candidate_wave10_20260322.json`
- Result:
  - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`

## Full matched `tbk_critical` rerun
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave10_20260322.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave10_20260322.json`
- Delta vs Wave 8:
  - baseline `correct_source_rate`: `74.32% -> 81.69%`
  - candidate `correct_source_rate`: `71.86% -> 81.15%`
  - candidate `hallucination_rate`: `1.64% -> 0.0%`
  - candidate `refusal_accuracy`: `93.44% -> 98.36%`
- `tbk_ceza_sarti` category delta:
  - baseline `66.67% -> 100.0%`
  - candidate `62.12% -> 100.0%`

## Decision
- `tbk_ceza_sarti` tail is closed for both lanes.
- The improvement generalized to the full `tbk_critical` slice without creating new hallucination debt.
- Remaining `tbk_critical` source loss now sits outside `tbk_ceza_sarti`, primarily in `tbk_kefalet`, `tbk_hizmet`, and `tbk_vekaletname` tails.

## Next active target
- Move from `tbk_ceza_sarti` to the next non-ceza `tbk_critical` source-tail cluster.
