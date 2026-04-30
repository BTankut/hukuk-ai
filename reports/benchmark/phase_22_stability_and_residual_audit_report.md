# Phase 22 Stability and Residual Audit Report

Status: STABILITY_PASS_RESIDUAL_P0_REMAINS

Phase22A run: `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`
Phase21F baseline: `reports/benchmark/runs/20260429T174747Z_phase21F_full`

## 1. Phase 22A Full Benchmark Metrics

| Metric | Phase22A | Phase21F | Delta | Gate | Result |
| --- | ---: | ---: | ---: | ---: | ---: |
| raw_score_proxy | 800.55 | 800.55 | +0.00 | >=790 | PASS |
| pass_proxy | 89/100 | 89/100 | +0 | >=87/100 | PASS |
| wrong_family | 6 | 6 | +0 | <=8 | PASS |
| wrong_document | 5 | 5 | +0 | <=7 | PASS |
| hallucinated_identifier | 5 | 5 | +0 | <=7 | PASS |
| unsupported_confident_claim | 0 | 0 | +0 | <=2 | PASS |
| contract_valid | 100/100 | 100/100 | 0 | 100/100 | PASS |
| source_key_v2_collision | 0 | 0 | +0 | 0 | PASS |
| binding_source_key_collision | 0 | 0 | +0 | 0 | PASS |
| green_lane | pass | pass | - | PASS | PASS |

## 2. Runtime / Green Lane

- model: `hukuk-ai-poc`
- dgx_model: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- guardrails: `false`
- green_lane_status: `pass`
- green_lane_run_validation: `pass`

## 3. Family-Level Stability

| Family | Phase22A Pass/Total | Phase21F Pass/Total | Phase22A Raw | Phase21F Raw | Floor | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CB_GENELGE | 4/4 | 4/4 | 35.20 | 35.20 | >=4/4 | PASS |
| CB_KARAR | 8/8 | 8/8 | 68.14 | 68.14 | >=7/8 | PASS |
| CB_KARARNAME | 6/6 | 6/6 | 52.07 | 52.07 | >=6/6 | PASS |
| CB_YONETMELIK | 4/6 | 4/6 | 46.85 | 46.85 | not specified | - |
| KANUN | 19/21 | 19/21 | 165.28 | 165.28 | >=19/21 | PASS |
| KHK | 6/6 | 6/6 | 53.15 | 53.15 | >=6/6 | PASS |
| KKY | 9/11 | 9/11 | 89.61 | 89.61 | >=9/11 | PASS |
| MULGA | 4/5 | 4/5 | 32.12 | 32.12 | >=4/5 | PASS |
| TEBLIGLER | 7/8 | 7/8 | 62.01 | 62.01 | >=6/8 | PASS |
| TUZUK | 3/5 | 3/5 | 31.15 | 31.15 | not specified | - |
| UY | 10/10 | 10/10 | 88.32 | 88.32 | >=9/10 | PASS |
| YONETMELIK | 9/10 | 9/10 | 76.65 | 76.65 | >=7/10 | PASS |

## 4. Residual Backlog Audit

| QID | Family | Pass | Score | Root Cause | Safe Action | Priority |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CBG-02 | CB_GENELGE | PASS | 8.65 | span_materialization | watch_only_pass_row | P2_watchlist |
| CBKAR-05 | CB_KARAR | PASS | 7.19 | family_boundary | watch_only_pass_row | P2_watchlist |
| CBY-01 | CB_YONETMELIK | PASS | 7.75 | family_boundary | watch_only_pass_row | P2_watchlist |
| CBY-04 | CB_YONETMELIK | FAIL | 6.85 | source_identity | fix_now_generalizable | P1_high_value_next_iteration |
| KANUN-12 | KANUN | FAIL | 1.45 | document_identity | fix_now_generalizable | P1_high_value_next_iteration |
| KKY-01 | KKY | FAIL | 6.65 | source_identity | fix_now_generalizable | P1_high_value_next_iteration |
| KKY-03 | KKY | FAIL | 1.45 | document_identity | fix_now_generalizable | P1_high_value_next_iteration |
| MULGA-01 | MULGA | FAIL | 0.00 | span_materialization | defer_needs_corpus | P0_blocks_productization |
| TEB-06 | TEBLIGLER | FAIL | 3.25 | span_materialization | defer_needs_corpus | P0_blocks_productization |
| TUZUK-05 | TUZUK | FAIL | 3.25 | document_identity | fix_now_generalizable | P1_high_value_next_iteration |
| YON-04 | YONETMELIK | FAIL | 3.25 | document_identity | fix_now_generalizable | P1_high_value_next_iteration |

## 5. P0/P1/P2/P3 Counts

- `P0_blocks_productization`: 2
- `P1_high_value_next_iteration`: 6
- `P2_watchlist`: 3
- `P3_acceptable_residual`: 0

## 6. Root Cause Counts

- `document_identity`: 4
- `family_boundary`: 2
- `source_identity`: 2
- `span_materialization`: 3

## 7. Safe Action Counts

- `defer_needs_corpus`: 2
- `fix_now_generalizable`: 6
- `watch_only_pass_row`: 3

## 8. Recommendation

Recommendation: `Open Phase 22D residual targeted remediation`. Stability passed exactly, but residual audit still has `2` P0 blockers (`MULGA-01`, `TEB-06`). Therefore this is not yet Phase 23 productization readiness. The next phase should remediate P0/P1 residuals only through generalizable retrieval/source-span improvements, with no QID-specific branching.

## 9. Productization Gate Decision

Productization gate: `CLOSED`.
Reason: two stable full runs now exist, but residual P0 blockers are not zero. Productization should remain closed until P0 blockers are resolved or accepted through manual legal review and a follow-up stability run remains clean.

## 10. Fine-Tuning Gate Decision

Fine-tuning gate: `CLOSED`.
Reason: residual source/span blockers are still retrieval and corpus/materialization problems. Training should not be opened until productization-readiness audit is complete, benchmark contamination controls are explicit, and hard-negative source/document sets are prepared.
