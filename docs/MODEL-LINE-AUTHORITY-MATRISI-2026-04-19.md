# Model-Line Authority Matrisi 2026-04-19

| lane_name | lane_type | authoritative_status | allowed_usage | forbidden_usage |
| --- | --- | --- | --- | --- |
| `merged_lane` | `merged` | `authoritative_target_active` | `active runtime`, `merged-first integration`, `new major acceptance candidate`, `same-pack acceptance`, `authoritative smoke` | `baseline-only parity rolea indirmek`, `etiketsiz acceptance`, `case-law authority gibi sunmak` |
| `baseline_lane` | `baseline` | `preserved_but_non_authoritative_for_new_major_acceptance` | `matched parity rerun`, `fallback`, `regression comparison`, `rollback preparedness` | `new major acceptance closure`, `authoritative merged substitute`, `etiketsiz final acceptance` |

## Matrix Rule

- `merged_first_rule = true`
- `baseline_second_parity_rule = true`
- `acceptance_without_model_line_label = forbidden`
