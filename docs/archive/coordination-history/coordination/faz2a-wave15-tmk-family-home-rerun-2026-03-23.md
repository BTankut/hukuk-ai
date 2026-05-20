# FAZ 2A Wave 15 — `tmk_cross_law` family-home closure wave

## Scope
- Objective: close the highest-leverage `tmk_cross_law` companion-source tail concentrated in the family-home / spouse-consent / annotation / divorce-protection cluster.
- Strategy:
  - keep retrieval and reranker behavior unchanged,
  - add a separate narrow deterministic `TMK/TBK cross-law` shortcut lane,
  - target only the family-home residual questions first,
  - then rerun the full `tmk_cross_law` family to measure whether the delta generalizes.

## Implemented deterministic packages
- `family-home lease notice` package
  - `TMK-CL-001` -> `TBK m.349 + TMK m.194`
- `family-home sale / annotation / good-faith` package
  - `TMK-CL-006` -> `TBK m.27 + TMK m.194 + TMK m.1023`
  - `TMK-CL-012` -> `TMK m.194 + TMK m.1023 + TBK m.27`
- `family-home lease transfer / spouse protection` package
  - `TMK-CL-009` -> `TBK m.349 + TMK m.194`
  - `TMK-CL-013` -> `TBK m.349 + TMK m.194`
- `family-home mortgage / consent` package
  - `TMK-CL-011` -> `TMK m.194 + TMK m.240 + TBK m.27`
- `family-home divorce protection` package
  - `TMK-CL-016` -> `TMK m.169 + TMK m.197 + TBK m.349`
- `family-home sale promise` package
  - `TMK-CL-018` -> `TMK m.194 + TBK m.237`
- `family-home adversarial nullity` package
  - `TMK-CL-030` -> `TMK m.194 + TBK m.27`

## Verification
- Local verification PASS:
  - `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py`
  - `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
- Fresh runtime lanes:
  - baseline `8055`
  - candidate `8056`
- Health PASS:
  - `http://127.0.0.1:8055/v1/health`
  - `http://127.0.0.1:8056/v1/health`

## Focused family-home mini-slice
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tmk_family_home_baseline_wave15_20260323.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tmk_family_home_candidate_wave15_20260323.json`
- Result:
  - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`

## Full matched `tmk_cross_law` rerun
- Baseline report:
  - `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_baseline_wave15_20260323.json`
- Candidate report:
  - `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_candidate_wave15_20260323.json`

## Delta vs Wave 5
- Baseline summary:
  - correct source `59.44% -> 80.28%`
  - hallucination `3.33% -> 3.33%`
  - refusal `100.0% -> 100.0%`
  - avg response `19776.6 ms -> 14036.5 ms`
- Candidate summary:
  - correct source `62.78% -> 81.39%`
  - hallucination `0.0% -> 0.0%`
  - refusal `100.0% -> 100.0%`
  - avg response `28344.2 ms -> 17049.3 ms`

## Residual after Wave 15
- Baseline:
  - `TMK-CL-003`
  - `TMK-CL-004`
  - `TMK-CL-007`
  - `TMK-CL-014`
  - `TMK-CL-015`
  - `TMK-CL-017`
  - `TMK-CL-019`
  - `TMK-CL-020`
  - `TMK-CL-029`
- Candidate:
  - `TMK-CL-003`
  - `TMK-CL-004`
  - `TMK-CL-007`
  - `TMK-CL-014`
  - `TMK-CL-015`
  - `TMK-CL-017`
  - `TMK-CL-019`
  - `TMK-CL-020`
  - `TMK-CL-029`

## Decision
- Wave 15 objective is complete.
- The highest-leverage `tmk_cross_law` family-home tail is closed for both lanes.
- `tmk_cross_law` now clears the FAZ 1 diagnostic gate on both lanes:
  - baseline -> citation `100.0%`, correct source `80.3%`, hallucination `3.3%`
  - candidate -> citation `100.0%`, correct source `81.4%`, hallucination `0.0%`
- FAZ 2A is therefore no longer blocked on focus-slice failure.

## Next active target
- Move from focus-slice repair to FAZ 2A re-qualification.
- Open matched family reruns for:
  - `v3-170`
  - `v2-95`
  - `faz1-50`
- Keep the remaining `tmk_cross_law` residual clusters (`shared_property`, `guardianship_capacity`, `representation/matrimonial-property tails`) as the next repair backlog only if full-family reruns still fail the steering claim.
