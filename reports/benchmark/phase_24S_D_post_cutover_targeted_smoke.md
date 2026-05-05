# Phase 24S-D Post-Cutover Targeted Smoke

Generated at UTC: `2026-05-05T07:19:01Z`  
Git HEAD before D commit: `af4b869ecc26f6986af758602643e4f2040ab9fa`  
Run dir: `reports/benchmark/runs/phase_24S_D_post_cutover_targeted_20260505T070913Z`  
Reference run: `reports/benchmark/runs/phase_24R_C_cby_targeted_20260504T2020Z`  
API URL: `http://127.0.0.1:8000/v1`  
Model: `hukuk-ai-poc`

## Runtime Provenance

- Runtime provenance git SHA: `af4b869ecc26f6986af758602643e4f2040ab9fa`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06`
- Milvus entity count: `349405`
- Vector dimension: `1024`

## Score Summary

- total: `11`
- raw_score_proxy: `85.41 / 110`
- average_score_0_10_proxy: `7.76`
- pass_proxy: `9`
- fail_proxy: `2`
- contract_valid: `11/11`
- refused_or_empty: `0`
- errors: `0`
- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`

## Acceptance

| Check | Result |
| --- | --- |
| CBY-06 PASS or score >= 8.5 | PASS |
| critical guards no regression vs Phase24R CBY targeted | PASS |
| contract_valid all | PASS |
| unsupported_confident_answer = 0 | PASS |
| answer_contract_invalid = 0 | PASS |
| source_key_v2_collision = 0 | PASS |
| binding_collision = 0 | PASS |
| TUZUK-04 not active-current-law claim | PASS |

## QID Results

| QID | Score | Pass | Delta vs Phase24R CBY | Family | Document | Failure classes |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| CBY-06 | 8.58 | PASS | +0.00 | 1.00 | 1.00 | missing_required_content_signal \| partial_grounding_only |
| CBY-05 | 8.00 | PASS | +0.00 | 1.00 | 0.50 | missing_required_content_signal \| partial_grounding_only |
| MULGA-01 | 8.37 | PASS | +0.00 | 1.00 | 0.67 | missing_required_content_signal \| partial_grounding_only |
| MULGA-05 | 4.00 | FAIL | +0.00 | 1.00 | 0.00 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| TEB-06 | 8.90 | PASS | +0.00 | 1.00 | 0.50 | - |
| KANUN-12 | 8.99 | PASS | +0.00 | 1.00 | 1.00 | missing_required_content_signal \| partial_grounding_only |
| YON-04 | 8.22 | PASS | +0.00 | 1.00 | 0.50 | missing_required_content_signal \| partial_grounding_only |
| TUZUK-04 | 4.63 | FAIL | +0.00 | 0.00 | 0.33 | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |
| CBG-01 | 8.65 | PASS | +0.00 | 1.00 | 1.00 | missing_required_content_signal \| partial_grounding_only |
| CBKAR-08 | 9.25 | PASS | +0.00 | 1.00 | 1.00 | - |
| UY-01 | 7.82 | PASS | +0.00 | 1.00 | 0.50 | missing_required_content_signal \| partial_grounding_only |

## Gate Result

Phase 24S-D targeted smoke gate: `PASS`.

Note: the D acceptance gate does not require every residual QID to become proxy PASS. `MULGA-05` and `TUZUK-04` remain residual failures, but they are unchanged from the Phase 24R CBY targeted reference and do not violate the listed hard guards. `TUZUK-04` is not treated as an active-current-law claim; the scored effective state is `repealed`.
