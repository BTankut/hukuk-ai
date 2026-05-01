# Phase 22F-R Targeted Smoke Report

Date: 2026-05-01

## Scope

Phase 22F-R-D targeted smoke was run after relation metadata source-chain evidence assembly implementation.

Runtime:

```text
api_url: http://127.0.0.1:8018/v1
lane: phase22f_shadow
collection: mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
git_sha: 310d898ad71bcd4319786a8421b008aab646863b
DGX_MODEL: /models/merged_model_fabric_stage_20260321
live_8000_untouched: true
```

Run artifacts:

```text
reports/benchmark/runs/phase_22F_R_targeted_smoke_20260501T184012Z
```

Implementation commit:

```text
310d898 Implement relation metadata source-chain evidence assembly
```

Unit verification before smoke:

```text
api-gateway/.venv/bin/python -m pytest \
  tests/test_retrieval_relation_chain.py \
  tests/test_chat_router.py::TestConversationStore::test_empty_store_returns_empty_list

5 passed
```

## Targeted Smoke Result

Runner:

```text
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8018/v1 \
  --out-dir reports/benchmark/runs/phase_22F_R_targeted_smoke_20260501T184012Z \
  --qids MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 \
         TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08
```

Scorer:

```text
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/phase_22F_R_targeted_smoke_20260501T184012Z/candidate_answers.csv \
  --out-dir reports/benchmark/runs/phase_22F_R_targeted_smoke_20260501T184012Z
```

System contract:

```text
total: 13
answered: 13
refused_or_empty: 0
errors: 0
missing_trace: 0
contract_valid: 13
unsupported_confident_answer: 0
answer_contract_invalid_count: 0
source_key_collision_detected_count: 0
source_key_v2_collision_detected_count: 0
binding_source_key_collision_detected_count: 0
```

Proxy scoring:

```text
pass_proxy: 7/13
fail_proxy: 6/13
average_score_0_10_proxy: 6.63
TEBLIGLER: 7/8 PASS
MULGA: 0/5 FAIL
repealed_as_active_count: 1
TEB-06: PASS
```

## Acceptance Gate

| Gate | Required | Observed | Status |
|---|---:|---:|---|
| MULGA | >= 4/5 | 0/5 | FAIL |
| TEBLIGLER | >= 6/8, preferred >= 7/8 | 7/8 | PASS |
| MULGA-01 improves or passes | improves or pass | relation-chain applied but still FAIL | FAIL |
| TEB-06 remains pass | pass | pass | PASS |
| unsupported | 0 | 0 | PASS |
| contract invalid | 0 | 0 | PASS |
| collisions | 0 | 0 | PASS |
| repealed_as_active_count | 0 | 1 | FAIL |
| relation_chain_expansion_applied where applicable | true for relation-backed historical question | true for MULGA-01 | PASS |

Decision:

```text
FAIL
STOP
NO R-E REGRESSION
NO R-F FULL BENCHMARK
NO CUTOVER
```

## Row-Level Result

| QID | Result | Score | Key failure classes |
|---|---:|---:|---|
| MULGA-01 | FAIL | 6.72 | missing_required_content_signal, wrong_article, partial_grounding_only |
| MULGA-02 | FAIL | 0.00 | auto_fail_triggered, wrong_family, repealed_source_used_as_active, hallucinated_identifier |
| MULGA-03 | FAIL | 6.85 | wrong_family, hallucinated_identifier, partial_grounding_only |
| MULGA-04 | FAIL | 5.75 | wrong_family, hallucinated_identifier, partial_grounding_only |
| MULGA-05 | FAIL | 6.05 | wrong_article, partial_grounding_only |
| TEB-01 | PASS | 8.80 | residual missing_required_content_signal |
| TEB-02 | PASS | 9.10 | residual partial_grounding_only |
| TEB-03 | PASS | 8.00 | residual partial_grounding_only |
| TEB-04 | FAIL | 0.00 | auto_fail_triggered, missing_required_content_signal |
| TEB-05 | PASS | 8.99 | residual partial_grounding_only |
| TEB-06 | PASS | 8.90 | none |
| TEB-07 | PASS | 7.52 | residual partial_grounding_only |
| TEB-08 | PASS | 9.55 | residual partial_grounding_only |

## Relation-Chain Verification

For `MULGA-01`, relation-chain expansion did work at retrieval/trace level:

```text
relation_chain_expansion_applied: true
relation_chain_source_key: phase22f:yonetmelik:16532:m18:f0:from2012-08-18:to2023-03-11
relation_chain_repeal_source_key: phase22f:yonetmelik_repeal:rg20230311-4:m1:f0:from2023-03-11:to9999-12-31
relation_chain_current_basis_source_key: phase22f:kanun:2547:m54:f0:from1981-11-06:to9999-12-31
current_law_basis_added: true
repeal_instrument_added: true
repealed_as_active_count in relation policy: 0
```

However, the answer/scoring surface still failed:

```text
selected_main_span_id: YOK_DISIPLIN_2012 m.22/f.0
claimed_source_identifier: rg20230311-4
claimed_article_or_section: m.1
failure: wrong_article + missing_required_content_signal
```

This means the Phase 22F-R retrieval expansion solved the raw source-chain absence for `MULGA-01`, but did not make synthesis/claim selection align the historical rule, repeal instrument, and current-law basis into the expected final answer contract.

## Diagnosis

The targeted smoke failure is no longer primarily a Phase 22F corpus absence issue for `MULGA-01`.

Confirmed fixed:

```text
relation metadata is queryable
repeal instrument is added
current-law basis is added
trace exposes relation_chain_* fields
historical source is not marked active by relation-chain policy
```

Still failing:

```text
MULGA family behavior remains below gate
MULGA-02 still triggers repealed_source_used_as_active
answer synthesis/claim extraction does not consistently express currentness/repeal/current-basis chain
MULGA rows without relation metadata still depend on legacy temporal/currentness handling
```

Important boundary:

```text
Do not proceed to regression or full benchmark.
Do not cut over.
Do not add QID-specific rules.
```

## Recommended Next Phase

Open a new remediation phase focused on general historical/repealed answer-contract synthesis and temporal claim binding, not additional source acquisition.

Candidate scope:

```text
1. Audit MULGA-01..05 answer_contract claimed source/effective_state vs selected evidence.
2. Ensure historical/repealed selected evidence cannot produce an "active" claim unless an active current-law basis is the claimed controlling source.
3. Teach synthesis to express three-part chain when relation_chain_expansion_applied=true:
   historical rule -> repeal/currentness instrument -> current-law basis.
4. Add a general temporal claim consistency guard for historical/repealed questions.
5. Preserve TEBLIGLER 7/8 and TEB-06 pass.
```

This should remain metadata-driven and must not use QID-specific branches.
