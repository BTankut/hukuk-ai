# Phase 24HW-A Pass-to-Fail Regression Audit

## Source Runs

- base: `reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z`
- candidate: `reports/benchmark/runs/phase_24HV_C_full_candidate`

## Summary

- pass_to_fail_count: `19`
- new_wrong_document_count: `16`
- new_hallucinated_identifier_count: `15`

## Likely Regressing Feature Counts

- HS_family_domain_gate: `14`
- HT_same_family_domain_scoring: `1`
- HU_secondary_family_recall: `1`
- feature_interaction: `1`
- scorer_trace_artifact: `2`

## Findings

- The combined Phase24HV feature set recovers target rows but creates broad non-target degradation.
- Only one pass-to-fail row has `secondary_family_recall_applied=true`; several KANUN/non-KANUN rows regress under HS/HT or broader feature interaction signals.
- The next safe action is matrix ablation, not code changes or integration.

## Pass-to-Fail Rows

| QID | Base | Candidate | Delta | New Wrong Document | New Hallucinated Identifier | Likely Feature |
| --- | ---: | ---: | ---: | --- | --- | --- |
| CBKAR-06 | 9.32 | 0.00 | -9.32 | `False` | `False` | `scorer_trace_artifact` |
| CBY-01 | 7.75 | 1.45 | -6.30 | `True` | `False` | `HS_family_domain_gate` |
| CBY-02 | 8.65 | 1.45 | -7.20 | `True` | `True` | `HS_family_domain_gate` |
| CBY-04 | 7.12 | 6.85 | -0.27 | `False` | `False` | `feature_interaction` |
| KANUN-01 | 9.55 | 3.25 | -6.30 | `True` | `True` | `HU_secondary_family_recall` |
| KANUN-04 | 8.00 | 3.70 | -4.30 | `True` | `True` | `HS_family_domain_gate` |
| KANUN-05 | 8.17 | 2.77 | -5.40 | `True` | `True` | `HS_family_domain_gate` |
| KANUN-06 | 9.32 | 3.93 | -5.39 | `True` | `True` | `HS_family_domain_gate` |
| KANUN-11 | 8.65 | 3.25 | -5.40 | `True` | `True` | `HT_same_family_domain_scoring` |
| KANUN-14 | 8.24 | 3.18 | -5.06 | `True` | `True` | `HS_family_domain_gate` |
| KANUN-16 | 8.65 | 3.25 | -5.40 | `True` | `True` | `HS_family_domain_gate` |
| KANUN-17 | 7.55 | 3.25 | -4.30 | `True` | `True` | `HS_family_domain_gate` |
| KANUN-18 | 8.65 | 3.25 | -5.40 | `True` | `True` | `HS_family_domain_gate` |
| KANUN-20 | 8.99 | 3.59 | -5.40 | `True` | `True` | `HS_family_domain_gate` |
| KKY-10 | 8.90 | 3.59 | -5.31 | `True` | `True` | `HS_family_domain_gate` |
| KKY-11 | 7.89 | 3.25 | -4.64 | `True` | `True` | `HS_family_domain_gate` |
| TEB-03 | 8.00 | 0.00 | -8.00 | `False` | `False` | `scorer_trace_artifact` |
| UY-02 | 8.65 | 3.25 | -5.40 | `True` | `True` | `HS_family_domain_gate` |
| UY-07 | 8.09 | 3.79 | -4.30 | `True` | `True` | `HS_family_domain_gate` |

## Decision

Proceed to Phase 24HW-B/C feature isolation matrix. No runtime feature is integration-ready from this audit alone.
