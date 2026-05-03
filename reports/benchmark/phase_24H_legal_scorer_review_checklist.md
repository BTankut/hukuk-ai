# Phase 24H Legal / Scorer Review Checklist

Generated: 2026-05-03T12:31:00Z

Reviewer return file required:

`reports/benchmark/legal_review_returns/filled_phase_24H_legal_scorer_review_return.csv`

## Required Return Columns

```text
qid
reviewer_name
review_date
primary_decision_enum
secondary_tags
legal_source_expected
scorer_expectation
runtime_fix_allowed_if_systemic
manual_residual_accepted_for_internal_eval
manual_residual_accepted_for_productization
notes
```

## Row Checklist

| QID | Required Reviewer Decision | Internal Eval Impact | Productization Impact |
|---|---|---|---|
| CBY-04 | decide legal taxonomy and primary/supporting source relationship | no direct blocker unless review escalates | blocks until reviewed |
| CBY-06 | decide amended provision/scorer slot completeness | no direct blocker unless review escalates | blocks until reviewed |
| KKY-01 | decide KKY vs YONETMELIK compatibility | no direct blocker unless review escalates | blocks until reviewed |
| TEB-04 | decide KDV tebliğ source sufficiency and auto-fail/rubric policy | blocks until fixed or manually accepted | blocks until reviewed |
| TUZUK-04 | decide current-law/tüzük framing sufficiency | no direct blocker unless review escalates | blocks until reviewed |

## Allowed Primary Decisions

| Decision Enum | Meaning |
|---|---|
| runtime_fix_allowed | A systemic runtime/source fix may be designed; QID-specific patch still forbidden. |
| runtime_fix_not_allowed | Do not change runtime; handle as benchmark/legal/scorer issue. |
| scorer_rubric_mismatch | Scorer/rubric expectation needs revision or explicit acceptance. |
| legal_taxonomy_confirmed | Legal taxonomy issue is confirmed and should guide systemic source classification. |
| manual_residual_accepted | Reviewer accepts residual risk for a named gate. Must specify which gate. |
| needs_more_review | Insufficient review basis; row remains blocked. |

## Hard Rules For Reviewers

- Do not provide private answer key text.
- Do not request QID-specific runtime branches.
- If a runtime change is allowed, it must be systemic and source-policy based.
- Productization acceptance must be explicit; silence means blocked.
- Internal-eval acceptance must be explicit; silence means blocked.

## Return Status

Current status: pending return.
