# Phase 24S-G Residual Register Update

Generated at UTC: `2026-05-05T08:23:33Z`  
Git HEAD before G commit: `454603f7a1840340b32c2a856520ed2b1405032b`  
Source run: `reports/benchmark/runs/phase_24S_E_post_cutover_full_20260505T071958Z`  
CSV: `reports/benchmark/phase_24S_G_residual_register_update.csv`

## Gate Context

Phase 24S-E failed the mandatory full benchmark gate and live `8000` was rolled back to the Phase 22F S7 base collection.

```text
raw_score_proxy = 727.18 / 1000
pass_proxy = 73 / 100
fail_proxy = 27 / 100
wrong_family = 8
wrong_document = 21
hallucinated_identifier = 25
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
```

## Residual Counts

- open_fail_residual_rows: `27`
- wrong_family_fail_rows: `6`
- wrong_document_fail_rows: `21`
- hallucinated_identifier_fail_rows: `23`
- TEB-04 raw intake blocker rows: `1`
- CBY-06 validated-candidate-not-live rows: `1`

## Category Counts

- document_or_source_identity_residual: `21`
- family_identity_residual: `5`
- official_raw_source_intake_blocker: `1`
- rubric_grounding_residual: `1`
- validated_candidate_not_live: `1`

## Worst Fail Rows

| QID | Score | Category | Failure classes |
| --- | ---: | --- | --- |
| CBY-02 | 3.25 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| CBY-04 | 6.85 | family_identity_residual | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |
| KANUN-02 | 3.25 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-04 | 3.70 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-05 | 2.77 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-06 | 3.93 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-07 | 3.25 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-08 | 1.45 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_family \| wrong_document \| partial_grounding_only |
| KANUN-11 | 3.25 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-13 | 3.25 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-14 | 2.84 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-16 | 3.25 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-17 | 3.25 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-18 | 3.25 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-20 | 3.59 | document_or_source_identity_residual | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |

## Decisions

- `CBY-06` remains validated in the candidate collection, but it is not live after rollback because the full gate failed.
- `TEB-04` remains blocked for materialization until the official browser-saved GIB PDF is acquired and hashed.
- No QID-specific runtime patch is authorized.
- Next remediation must address source/document identity and canonical span recall systemically, then re-enter controlled benchmark gates.
