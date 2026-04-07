# Hat-B Case-Law Full Decision-Row Materialization Ve Completeness Gate Raporu 2026-04-07

## Official Decision

- decision = `NO-GO - Hat-B Full Decision-Row Materialization Or Completeness`

## PASS Criteria Contrast

| criterion | required | observed | result |
| --- | --- | --- | --- |
| Yargitay row_materialization_completed | `true` | `false` | FAIL |
| Danistay row_materialization_completed | `true` | `false` | FAIL |
| Anayasa Mahkemesi row_materialization_completed | `true` | `false` | FAIL |
| canonical_parse_complete for all | `true` | `false` | FAIL |
| parse_error_count for all | `0` | `11 / 3 / 0` | FAIL |
| duplicate_record_count for all | `0 or normalized explanation` | `0 / 0 / 0` | PASS |
| id_integrity_status for all | `true` | `true / true / true` | PASS |
| unexplained_gap_count for all | `0` | `1 / 1 / 1` | FAIL |
| completeness_status for all | `FULL_AND_PROVEN` | `PARTIAL_OR_UNPROVEN` | FAIL |
| runtime_integration_authorized | `false` | `false` | PASS |
| vector_write_authorized | `false` | `false` | PASS |
| serving_authorized | `false` | `false` | PASS |

## Decisive Findings

- Yargitay current phase'de `3940` repo-local karar satiri materialize etti; official total signal `9851892` oldugu icin coverage ratio `0.00039992` seviyesinde kaldi.
- Danistay current phase'de `1365` repo-local karar satiri materialize etti; official total signal `382739` oldugu icin coverage ratio `0.00356640` seviyesinde kaldi.
- Anayasa Mahkemesi current phase'de bundle-visible `20` repo-local karar satiri materialize etti; official total signal `22271` oldugu icin coverage ratio `0.00089803` seviyesinde kaldi.
- Bu nedenle talimatin aradigi full repo-local decision-row corpus ve `FULL_AND_PROVEN` completeness hukmu kapanmadi.

## Runtime Evidence

- summary_path = `runtime_logs/hat_b_full_materialization_v2_20260407/hat_b_full_materialization_v2_summary.json`
- yargitay_rowset = `runtime_logs/hat_b_full_materialization_v2_20260407/yargitay_decision_rows_partial.jsonl.gz`
- yargitay_unit_summary = `runtime_logs/hat_b_full_materialization_v2_20260407/yargitay_unit_materialization_summary.json`
- danistay_rowset = `runtime_logs/hat_b_full_materialization_v2_20260407/danistay_decision_rows_partial.jsonl.gz`
- danistay_unit_summary = `runtime_logs/hat_b_full_materialization_v2_20260407/danistay_unit_materialization_summary.json`
- anayasa_mahkemesi_rowset = `runtime_logs/hat_b_full_materialization_v2_20260407/anayasa_mahkemesi_decision_rows_bundle_visible.jsonl.gz`

## Boundary Preservation

- runtime_integration_authorized = `false`
- vector_write_authorized = `false`
- serving_authorized = `false`
- answer_path_changed = `false`
- model_changed = `false`
- prompt_changed = `false`
- retrieval_logic_changed = `false`
- reranker_changed = `false`
- guardrail_changed = `false`
- release_controls_topology_changed = `false`

## Conclusion

- official gate result = `NO-GO`
- blocker_class = `full decision-row materialization and completeness gap`
