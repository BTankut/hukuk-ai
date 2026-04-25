# Phase 18C Claim-Level Confidence Calibration Report

Date: 2026-04-25

## Scope

Implemented claim-level confidence ceilings driven by Phase 18B `answer_slots`.

The policy is systemic and does not branch on benchmark QID or question text. It uses required slot fill state, critical slot misses, source identity uncertainty, temporal uncertainty and canonical evidence quality.

## Phase 17F Unsupported Confident Audit

Input run:

- `reports/benchmark/runs/20260424T212636_phase17f_full/scored.csv`
- `reports/benchmark/runs/20260424T212636_phase17f_full/candidate_answers.csv`

Phase 17F had 8 scorer-level `unsupported_confident_claim` rows while runtime `unsupported_confident_answer=0`. In all 8 rows, runtime contract was overconfident: `answer_mode=direct_answer`, `grounding_status=fully_grounded`, `confidence_0_100=82`.

| qid | answer_mode | confidence_0_100 | grounding_status | unsupported_claim_reason | should_degrade_confidence | proposed_confidence_ceiling |
|---|---|---:|---|---|---|---:|
| CBK-06 | direct_answer | 82 | fully_grounded | private grounding/must-include support low despite document hit | true | 65 |
| CBY-02 | direct_answer | 82 | fully_grounded | private grounding/must-include support low despite document hit | true | 65 |
| CBY-04 | direct_answer | 82 | fully_grounded | wrong family plus hallucinated identifier signal | true | 40 |
| KANUN-18 | direct_answer | 82 | fully_grounded | wrong document plus hallucinated identifier signal | true | 40 |
| KKY-05 | direct_answer | 82 | fully_grounded | partial document hit and low grounding support | true | 60 |
| TEB-05 | direct_answer | 82 | fully_grounded | partial document hit and low grounding support | true | 60 |
| YON-03 | direct_answer | 82 | fully_grounded | partial document hit and low grounding support | true | 60 |
| YON-09 | direct_answer | 82 | fully_grounded | partial document hit and low grounding support | true | 60 |

Pre-Phase18B audit limitation:

- `filled_slots`, `missing_required_slots`, and `evidence_span_keys` were not available in Phase 17F candidate rows.
- Phase 18B now emits those fields as `answer_slots`, `answer_slot_missing_count`, `answer_slot_verified_count`, and `critical_answer_slots_missing`.

## Policy

The runtime now applies these claim-level ceilings:

- all required slots verified: max `90`
- one required non-critical slot missing: max `75`
- multiple required slots missing or unsupported: max `65`
- critical required slot missing: max `60`
- transition/current relation missing when required: max `55`
- title-only or insufficient canonical evidence: max `45`
- source identity uncertain: max `40`
- temporal state uncertain: max `40`

If the ceiling is below `70` and the answer was nominally `fully_grounded`, the contract is downgraded to:

- `grounding_status=partially_grounded`
- `answer_mode=qualified_answer`
- `confidence_policy_adjusted=True`

The policy also emits:

- `claim_level_confidence_policy_version`
- `confidence_policy_ceiling`
- `confidence_policy_ceiling_reasons`

## Verification

Commands run:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/answer_contract_v2.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_answer_contract_v2.py -k "phase18c or confidence_policy or unsupported_confident"
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_answer_contract_v2.py
```

Result:

- Targeted confidence tests passed: `3 passed`.
- Full `test_answer_contract_v2.py` passed: `28 passed`.
- Syntax/import checks passed.

## Status

Phase 18C Commit 3 is complete. The next full benchmark should verify whether scorer-level `unsupported_confident_claim` drops toward the `<=3` target.
