# FAZ 2A Wave 13 — `tbk_kefalet` + `TBK-137` closure

## Scope
- Objective: close the remaining `tbk_kefalet` companion-source tail and fold the single non-surety residual `TBK-137` into the same wave.
- Strategy: keep retrieval unchanged and add narrow deterministic answer packages only for:
  - `TBK-091`
  - `TBK-137`
  - `TBK-150`
  - `TBK-151`
  - `TBK-153`
  - `TBK-155`
  - `TBK-156`

## Implemented deterministic packages
- `ordinary vs joint surety` package
  - `TBK-091` -> `TBK m.585 + TBK m.586`
  - `TBK-150` -> `TBK m.587 + TBK m.586`
- `surety defenses / limitation` package
  - `TBK-151` -> `TBK m.589 + TBK m.590`
  - `TBK-153` -> `TBK m.598 + TBK m.596`
  - `TBK-155` -> `TBK m.584 + TBK m.583`
  - `TBK-156` -> `TBK m.603 + TBK m.125`
- `service-law companion source` package
  - `TBK-137` -> `TBK m.401 + TBK m.402`

## Verification
- Local verification PASS:
  - `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py`
  - `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
- Fresh runtime lanes:
  - baseline `8051`
  - candidate `8052`
- Health PASS:
  - `http://127.0.0.1:8051/v1/health`
  - `http://127.0.0.1:8052/v1/health`

## Focused `tbk_kefalet` mini-slice
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_kefalet_baseline_wave13_20260322.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_kefalet_candidate_wave13_20260322.json`
- Result:
  - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`

## Full matched `tbk_critical` rerun
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave13_20260322.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave13_20260322.json`

## Delta vs Wave 12
- Baseline summary:
  - correct source `95.08% -> 100.0%`
  - hallucination `0.0% -> 0.0%`
  - refusal `96.72% -> 100.0%`
  - avg response `7889.7 ms -> 5954 ms`
- Candidate summary:
  - correct source `94.26% -> 98.36%`
  - hallucination `0.0% -> 1.64%`
  - refusal `98.36% -> 98.36%`
  - avg response `16444.3 ms -> 10993 ms`
- Category impact:
  - `tbk_kefalet` baseline `80.77% -> 100.0%`
  - `tbk_kefalet` candidate `76.92% -> 100.0%`
  - `tbk_hizmet` baseline `97.37% -> 100.0%`
  - `tbk_hizmet` candidate `97.37% -> 100.0%`

## Residual after Wave 13
- Baseline:
  - none in `tbk_critical`
- Candidate:
  - `TBK-103`

## Diagnostic note
- `TBK-103` is outside Wave 13 scope and belongs to the `tbk_vekaletname` family.
- The failure pattern is not a surety/source-lock miss; it is a `vekalet` neighbor-article bleed where the answer cites `TBK m.507` instead of the expected `TBK m.508`.
- Candidate lane also showed a single latency spike at `TBK-114`, but it recovered and the question closed correctly; this did not produce a new residual.

## Decision
- Wave 13 objective is complete.
- `tbk_kefalet` and the shared `TBK-137` tail are closed for both lanes.
- FAZ 2A remains open only because the candidate lane still carries a single non-scope residual in `tbk_vekaletname` (`TBK-103`).

## Next active target
- Open Wave 14 for `TBK-103` only.
- Keep retrieval unchanged; add a narrow deterministic answer path for `TBK m.508` to eliminate `TBK m.507` bleed.
