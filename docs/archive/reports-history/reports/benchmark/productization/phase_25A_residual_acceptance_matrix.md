# Phase 25A Residual Acceptance Matrix

Generated: 2026-05-08

## Decision Rule

Residuals are no longer treated as a runtime patch queue in Phase25A. They are product risks that must be accepted, blocked, or routed to manual review.

Default productization decision:

```text
not_productization_acceptable
```

No row is approved for serving-candidate or productization exposure. Reviewer-only exposure means a controlled legal/product reviewer may inspect the case as evidence; it does not authorize internal broad eval, serving, or public productization.

CSV artifact: `reports/benchmark/productization/phase_25A_residual_acceptance_matrix.csv`

## Matrix

| residual_id | qid_or_family | residual_class | exposure decision | owner_decision |
| --- | --- | --- | --- | --- |
| `R25A-001` | `KANUN-08 / regression slice` | `wrong_document` | internal=no; serving=no; productization=no | `blocked_until_runtime_fix` |
| `R25A-002` | `CBY-04 / TUZUK-05` | `hallucinated_identifier` | internal=no; serving=no; productization=no | `blocked_until_policy` |
| `R25A-003` | `KKY-01 / CBY-04` | `wrong_family` | internal=reviewer_only; serving=no; productization=no | `blocked_until_policy` |
| `R25A-004` | `CBY-06` | `missing_required_content_signal` | internal=no; serving=no; productization=no | `blocked_until_source_review` |
| `R25A-005` | `KANUN-12 / KKY-03 / YON-04` | `partial_grounding_only` | internal=reviewer_only; serving=no; productization=no | `blocked_until_runtime_fix` |
| `R25A-006` | `TUZUK-05` | `source_not_found` | internal=reviewer_only; serving=no; productization=no | `blocked_until_policy` |
| `R25A-007` | `KKY-01` | `benchmark_ambiguous` | internal=reviewer_only; serving=no; productization=no | `accepted_with_manual_review` |
| `R25A-008` | `TUZUK-05` | `scorer_rubric_mismatch` | internal=reviewer_only; serving=no; productization=no | `accepted_with_manual_review` |
| `R25A-009` | `TUZUK-04 / TEB-04` | `current_law_uncertainty` | internal=no; serving=no; productization=no | `blocked_until_policy` |
| `R25A-010` | `TEB-04` | `wrong_document` | internal=no; serving=no; productization=no | `blocked_until_runtime_fix` |
| `R25A-011` | `All residual classes` | `not_productization_acceptable` | internal=no; serving=no; productization=no | `not_productization_acceptable` |

## Product Risk Interpretation

The highest-risk classes remain `wrong_document`, `hallucinated_identifier`, `wrong_family`, and `current_law_uncertainty`. These cannot be exposed to a serving candidate without live-evidenced guardrails, claim-level verification, source-family checks, and temporal/current-law validation.

`benchmark_ambiguous` and `scorer_rubric_mismatch` can be inspected in a reviewer-only workflow because the risk is partly evaluation-policy alignment. That is not an authorization for broad internal eval.

## Required Mitigation Pattern

Allowed next work:

- product policy and manual review workflow refinement
- claim-level verification design
- source-family and temporal evidence policy
- non-live diagnostic documentation
- judicial corpus dry-run architecture

Closed work:

- QID-specific runtime fixes
- new source-selection heuristic loops
- public/product serving
- internal eval opening
- fine-tuning as a substitute for product controls
