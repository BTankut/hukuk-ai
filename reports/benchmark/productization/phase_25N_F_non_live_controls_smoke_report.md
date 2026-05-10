# Phase25N-F Non-Live Product Controls Smoke Report

Generated: 2026-05-10

## Decision

PASS - non-live product controls smoke scenarios completed.

## Command

```text
python3 scripts/product_controls/run_non_live_controls_smoke.py
```

## Acceptance

- all scenarios pass = true
- all flags default off outside smoke = true
- live 8000 unchanged = true
- no productization opened = true
- no eval opened = true

## Results

| scenario | status | notes |
|---|---|---|
| safe_answer_with_valid_sources | PASS | flags_default_off=True |
| unsupported_confident_answer | PASS | unsupported confident answer blocked in preview |
| insufficient_evidence_answer | PASS | insufficient evidence safe mode preview |
| repealed_source_current_law_uncertainty | PASS | historical warning and effective-state mismatch detected |
| PII_in_query | PASS | email and phone redaction preview |
| external_user_trace_access_denied | PASS | external user denied trace access |
| legal_reviewer_manual_review_allowed | PASS | legal reviewer allowed review queue |
| claim_source_identifier_mismatch | PASS | source identifier mismatch detected |

## CSV

```text
reports/benchmark/productization/phase_25N_F_non_live_controls_smoke.csv
```
