# Phase 24HY Replacement Guard Program Report

Generated: 2026-05-08

## 1. Commit SHA List

| phase | commit | message |
| --- | --- | --- |
| A | `d349d88` | Audit Phase24HY source-selection replacement failures |
| B | `f86cd7f` | Design Phase24HY source-selection replacement guard |
| C | `4656627` | Instrument Phase24HY replacement guard trace |
| D | `904eaf2` | Prototype Phase24HY replacement guard |
| E | `98febd5` | Run Phase24HY family-slice validation smoke |
| F | `448f658` | Record Phase24HY full candidate not run |
| G | `50db3f1` | Record Phase24HY product stop-loss decision |
| H | `346f862` | Update product readiness after Phase24HY |

## 2. Replacement Failure Audit

Output:

```text
reports/benchmark/phase_24HY_A_source_selection_replacement_failure_audit.md
reports/benchmark/phase_24HY_A_source_selection_replacement_failure_audit.csv
```

Audit summary:

```text
audited_rows = 29
source_replaced_rows = 1
wrong_document_after_replacement_rows = 13
hallucinated_identifier_after_replacement_rows = 17
dominant_class = no_replacement_but_claim_surface_drift
```

Interpretation: the observed failures are not mostly clean candidate-over-base source replacements. The dominant failure class is primary source / claimed family / claimed identifier / claimed article drift even when selected-document surface appears unchanged.

## 3. Replacement Guard Design

Output:

```text
reports/benchmark/phase_24HY_B_replacement_guard_design.md
```

Design rule:

```text
candidate may replace base primary only with strong metadata lock,
compatible family/domain, stronger identity/domain evidence,
primary_source role, preserved/improved span support,
and no increased identifier/article ambiguity.
```

Fail-closed behavior:

```text
if any condition is missing:
  keep base primary source
  add candidate only as role-compatible supporting evidence
  otherwise discard candidate from primary selection
```

## 4. Trace Instrumentation

Output:

```text
reports/benchmark/phase_24HY_C_replacement_guard_trace_report.md
```

Code:

```text
api-gateway/src/rag/phase24hy_replacement_guard.py
api-gateway/src/routers/chat.py
```

Trace fields are emitted under:

```text
trace.parsed_query.phase24hy_replacement_guard
trace.parsed_query.source_identity_reranker.phase24hy_replacement_guard
```

Required fields were present in the Phase24HY-E trace:

```text
phase24hy_replacement_guard
base_primary_source_key
candidate_primary_source_key
replacement_attempted
replacement_allowed
replacement_block_reason
candidate_role
candidate_metadata_lock_strength
candidate_domain_score
base_domain_score
identifier_drift_blocked
article_drift_blocked
supporting_only_added
primary_source_preserved
```

## 5. Prototype Run

Output:

```text
reports/benchmark/phase_24HY_D_non_live_prototype_report.md
```

Feature flag:

```text
ENABLE_PHASE24HY_REPLACEMENT_GUARD=true
```

Behavior:

- Metadata-first primary focus is suppressed when the candidate lacks strong identity, compatible family/domain, or primary role.
- Source-identity rerank cannot replace original/base primary unless the guard allows it.
- Old broad HS/HT/HU behavior was not globally activated.

Verification:

```text
test_phase24hy_replacement_guard.py = 8 passed
test_phase24hx_constrained_routing.py + test_phase22f_s7_teb_source_identity.py = 16 passed
py_compile = passed
```

## 6. Family-Slice Validation Result

Output:

```text
reports/benchmark/phase_24HY_E_family_slice_validation_smoke.md
reports/benchmark/phase_24HY_E_family_slice_validation_smoke.csv
```

Run:

```text
api_url = http://127.0.0.1:8045/v1
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
live_8000_modified = false
```

Result:

| Slice | Base | Phase24HX | Phase24HY |
| --- | ---: | ---: | ---: |
| All 29 score/pass | 214.40 / 23 | 160.64 / 11 | 152.42 / 11 |
| Target 4 score/pass | 10.45 / 0 | 25.35 / 2 | 28.25 / 3 |
| Regression 16 score/pass | 133.04 / 16 | 64.38 / 2 | 55.06 / 1 |
| Guard 9 score/pass | 70.91 / 7 | 70.91 / 7 | 69.11 / 7 |

Hard counters:

```text
contract_invalid = 0
unsupported_confident_answer = 0
source_key_v2_collision = 0
binding_collision = 0
```

Gate result: `FAIL`.

Reason:

```text
wrong_document: Phase24HX 13, Phase24HY 13
hallucinated_identifier: Phase24HX 16, Phase24HY 16
regression_slice_pass: Phase24HX 2/16, Phase24HY 1/16
```

## 7. Full Candidate Result

Output:

```text
reports/benchmark/phase_24HY_F_full_candidate_not_run.md
```

Full candidate benchmark was not run because Phase24HY-E failed the family-slice gate. This follows the program stop rule and avoids spending a full run on an already failed candidate.

## 8. Product Stop-Loss Decision

Output:

```text
reports/benchmark/phase_24HY_G_product_stop_loss_decision.md
```

Decision: `Option C`.

```text
Stop runtime recovery line.
Move to product policy / residual acceptance.
No further source-selection feature work.
```

Reason: Phase24HY target recovery improved, but broad wrong-document and hallucinated-identifier classes did not improve. Trace also showed `replacement_attempted=0/29`, so the remaining failure is not the replacement behavior that this phase was designed to guard.

## 9. Product Readiness Update

Output:

```text
reports/benchmark/productization/product_level_completion_report_after_phase24HY.md
```

Status:

```text
benchmark_status = FAIL
residual_status = OPEN
runtime_recovery_status = STOP_LOSS
guardrails_status = DISABLED
verification_status = DISABLED
privacy_status = NOT_EVIDENCED
audit_logging_status = NOT_EVIDENCED
rollback_status = RUNBOOK_ONLY
internal_eval_decision = closed
productization_decision = not_productization_ready
fine_tuning_decision = closed
```

## 10. Final Live 8000 State

Latest verified live health:

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Live `8000` was not modified by Phase24HY.

## 11. Next Recommended Action

Stop source-selection runtime patching for this line and move to product policy / residual acceptance.

Recommended next packet:

```text
Phase24HZ product policy / residual acceptance decision brief
```

The brief should ask product/legal owners to decide whether the remaining wrong-document and hallucinated-identifier classes block any customer-safe pilot, or whether they can be handled through confidence UX, manual review, scoped disclaimers, and residual exclusion policy.

No additional human lawyer review is required for another QID-specific runtime fix. If human input is needed, it should be framed as residual acceptance / product-risk policy, not source-selection patch guidance.

## Safety Closure

- No live cutover.
- No productization opening.
- No internal eval opening.
- No fine-tuning.
- No model, prompt, top-k, base/live collection, or answer-key change.
- Large run traces and runtime logs were not committed.
