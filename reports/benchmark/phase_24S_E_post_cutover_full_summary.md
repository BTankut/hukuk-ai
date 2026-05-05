# Phase 24S-E Post-Cutover Full Benchmark Summary

Generated at UTC: `2026-05-05T08:20:55Z`  
Git HEAD before E commit: `fe10184882504b103c12e1705eb3d681c92d00a8`  
Run dir: `reports/benchmark/runs/phase_24S_E_post_cutover_full_20260505T071958Z`  
API URL: `http://127.0.0.1:8000/v1`  
Model: `hukuk-ai-poc`

## Runtime Provenance

- Runtime provenance git SHA: `fe10184882504b103c12e1705eb3d681c92d00a8`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06`
- Milvus entity count: `349405`
- Vector dimension: `1024`

## Contract / Runtime Result

| Metric | Observed | Required | Result |
| --- | ---: | ---: | --- |
| total | 100 | 100 | PASS |
| answered | 100 | 100 | PASS |
| refused_or_empty | 0 | 0 | PASS |
| errors | 0 | 0 | PASS |
| contract_valid | 100/100 | 100/100 | PASS |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |

## Score Result

| Metric | Observed | Minimum Gate | Result |
| --- | ---: | ---: | --- |
| raw_score_proxy | 727.18 | >= 816.86 | FAIL |
| pass_proxy | 73 | >= 91 | FAIL |
| wrong_family | 8 | <= 6 | FAIL |
| wrong_document | 21 | <= 4 | FAIL |
| hallucinated_identifier | 25 | <= 4 | FAIL |

## Key Rows

| QID | Score | Pass | Failure classes |
| --- | ---: | --- | --- |
| CBY-06 | 8.58 | PASS | missing_required_content_signal \| partial_grounding_only |
| KANUN-05 | 2.77 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-08 | 1.45 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_family \| wrong_document \| partial_grounding_only |
| MULGA-05 | 4.00 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| TEB-04 | 8.35 | PASS | missing_required_content_signal \| partial_grounding_only |
| TUZUK-04 | 4.63 | FAIL | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |

## Worst 15 Rows

| QID | Score | Pass | Failure classes |
| --- | ---: | --- | --- |
| KANUN-08 | 1.45 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_family \| wrong_document \| partial_grounding_only |
| KANUN-05 | 2.77 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-14 | 2.84 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| CBY-02 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-02 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-07 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-11 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-13 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-16 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-17 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-18 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-04 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-11 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| MULGA-04 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| TUZUK-05 | 3.25 | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| partial_grounding_only |

## Gate Result

Phase 24S-E minimum full benchmark gate: `FAIL`.

Because this hard gate is `FAIL`, live `8000` must be rolled back to the Phase 22F S7 base collection before any further benchmark/productization step. Phase 24S-F stability must not run.
