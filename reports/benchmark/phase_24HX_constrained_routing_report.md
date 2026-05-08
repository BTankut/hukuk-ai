# Phase 24HX Constrained Routing Report

Generated: 2026-05-08

## Executive Result

Phase24HX is complete.

Outcome: constrained routing prototype is safe as a diagnostic line, but it failed family-slice validation and must not be integrated.

No live cutover. No productization. No internal eval. No fine-tuning.

## Commit SHA List

- `0a0373d` Audit Phase 24HX regression slices
- `fae1f00` Design Phase 24HX constrained routing
- `221599c` Instrument Phase 24HX feature attribution trace
- `daa831e` Prototype Phase 24HX constrained routing
- `4bba32f` Run Phase 24HX family-slice validation smoke
- `3e71b62` Record Phase 24HX integration decision

## A: Regression Slice Audit

Output:

- `reports/benchmark/phase_24HX_A_regression_slice_audit.md`
- `reports/benchmark/phase_24HX_A_regression_slice_audit.csv`

Findings:

- 16 Phase24HW pass-to-fail regressions were audited.
- Largest slice: `KANUN`, 9 rows.
- Other slices: `CBY` 3, `KKY` 1, `TEBLIGLER` 1, `UY` 1, `OTHER` 1.
- Existing Phase24HW trace showed broad attribution but lacked a consolidated `phase24hx_feature_trace`; this was addressed in C.

## B: Constrained Routing Design

Output:

- `reports/benchmark/phase_24HX_B_constrained_routing_design.md`

Design decision:

- Replace broad HS/HT/HU global activation with explicit source-role trigger, strong metadata identity lock, fail-closed replacement, per-family guard, and role-aware evidence separation.
- Old broad flags must remain off unless a future diagnostic explicitly scopes them.

## C: Feature Attribution Trace

Output:

- `reports/benchmark/phase_24HX_C_feature_attribution_trace_report.md`

Implementation:

- Added `api-gateway/src/rag/phase24hx_constrained_routing.py`.
- Added `phase24hx_feature_trace` into chat trace payload.
- Trace is attached at top-level, `parsed_query`, `query_signals`, `retrieval`, and `context_assembly`.

Verification:

```text
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/rag/phase24hx_constrained_routing.py \
  api-gateway/src/routers/chat.py
```

Result: PASS.

## D: Non-Live Prototype

Output:

- `reports/benchmark/phase_24HX_D_non_live_prototype_report.md`

Implementation:

- Added `ENABLE_PHASE24HX_CONSTRAINED_ROUTING=true`.
- The prototype only enables the existing HU secondary-family recall path through its existing source-role gate.
- HS and HT broad behavior remain off.
- Added fail-closed `evaluate_phase24hx_replacement(...)` policy tests.

Verification:

- `api-gateway/tests/test_phase24hx_constrained_routing.py`: PASS, `8/8`.
- `api-gateway/tests/test_phase22f_s7_teb_source_identity.py`: PASS, `8/8`.

## E: Family-Slice Validation Smoke

Output:

- `reports/benchmark/phase_24HX_E_family_slice_validation_smoke.md`
- `reports/benchmark/phase_24HX_E_family_slice_validation_smoke.csv`

Run:

- Candidate endpoint: `127.0.0.1:8045`
- Run dir: `reports/benchmark/runs/phase_24HX_E_family_slice_validation_smoke`
- QID count: 29

Result:

| Metric | Base | Phase24HW selected | Phase24HX constrained |
| --- | ---: | ---: | ---: |
| 29-row score | 214.40 | 153.59 | 160.64 |
| 29-row pass | 23/29 | 11/29 | 11/29 |
| Target pass | 0/4 | 4/4 | 2/4 |
| Regression-slice pass | 16/16 | 0/16 | 2/16 |
| Guard pass | 7/9 | 7/9 | 7/9 |
| Wrong-document count | 2 | 13 | 13 |
| Hallucinated-identifier count | 4 | 15 | 16 |

Gate decision: FAIL.

Reason: wrong-document explosion persisted in the family-slice smoke.

## F: Full Candidate Result

Output:

- `reports/benchmark/phase_24HX_F_full_candidate_not_run.md`

Full candidate benchmark was not run because E failed.

## G: Integration Decision

Output:

- `reports/benchmark/phase_24HX_G_integration_decision.md`

Decision:

- Option B/C hybrid.
- Keep constrained routing as diagnostic code.
- Do not integrate.
- Continue scoped redesign only if the next phase directly addresses primary source-selection replacement and claimed identifier/article drift.

## Productization Decision

Closed.

## Internal Eval Decision

Closed.

## Fine-Tuning Decision

Closed.

## Final Live 8000 State

Live endpoint was not modified.

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Candidate `8045` was stopped after the E smoke run.

## Next Recommended Phase

Recommended next phase: Phase24HY source-selection replacement guard redesign.

Phase24HY should target the unresolved source-selection failure mode:

- retain base primary source when the candidate is not stronger
- prevent claimed identifier/article drift when the selected document is unchanged
- separate primary/supporting/current-law/historical roles before answer contract synthesis
- validate KANUN and CBY family slices before any full benchmark

