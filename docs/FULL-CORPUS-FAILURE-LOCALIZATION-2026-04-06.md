# Full Corpus Failure Localization 2026-04-06

## Bound Legacy Failure Set

- total_eval_row_count = `57`
- reject_count = `9`
- runtime_error_count = `0`
- unexplained_count = `0`
- cross_law_confusion_count = `1`
- wrong_primary_source_count = `8`

## Legacy Per-Source Failure Table

| source_class | row_count | reject_count | cross_law_confusion_count | wrong_primary_source_count | correct_source_rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| TMK core corpus | 9 | 1 | 0 | 3 | 55.6% |
| TCK | 9 | 3 | 0 | 2 | 44.4% |
| HMK | 9 | 1 | 0 | 0 | 88.9% |
| CMK | 9 | 2 | 1 | 0 | 66.7% |
| TTK | 9 | 0 | 0 | 2 | 77.8% |
| IK | 9 | 2 | 0 | 1 | 66.7% |

## Localization Decision

- failure_surface_localized_to_legacy_eval_lineage = `true`
- legacy_pack_canonical_acceptance_surface = `false`
- full_primary_law_runtime_mutation_required = `false`
- remediation_axis = `eval_rigor_reset_and_canonical_pack_replacement_only`
