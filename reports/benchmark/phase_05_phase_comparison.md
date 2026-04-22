# Phase 5 vs Phase 4 Comparison

- phase_4_run: `reports/benchmark/runs/20260421T211914Z_phase4_verification_first_final_v4`
- phase_5_run: `reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final`
- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- acceptance_status: `NOT_ACCEPTED`
- numeric_targets_hit: `0/7`

## Target Metrics
| metric | phase_4 | phase_5 | delta | target | result |
| --- | ---: | ---: | ---: | ---: | --- |
| raw_score_proxy | 640.88 | 658.22 | +17.34 | >= 680 | FAIL |
| pass_proxy | 48 | 51 | +3 | >= 58 | FAIL |
| wrong_family | 38 | 35 | -3 | <= 25 | FAIL |
| wrong_document | 22 | 20 | -2 | <= 15 | FAIL |
| hallucinated_identifier | 51 | 48 | -3 | <= 30 | FAIL |
| unsupported_confident_claim | 33 | 33 | 0 | <= 20 | FAIL |
| right-document wrong-article/span | 30 | 34 | +4 | <= 20 | FAIL |

## Secondary Metrics
| metric | phase_4 | phase_5 | delta |
| --- | ---: | ---: | ---: |
| average_score_0_10_proxy | 6.41 | 6.58 | +0.17 |
| hallucinated_source_count | 22 | 20 | -2 |
| missing_gold_document_signal | 22 | 20 | -2 |
| repealed_source_used_as_active | 5 | 5 | 0 |
| missing_required_content_signal | 97 | 97 | 0 |
| partial_grounding_only | 97 | 97 | 0 |

## Failure Mechanisms
| mechanism | phase_4 | phase_5 | delta |
| --- | ---: | ---: | ---: |
| right-document wrong-article/span | 30 | 34 | +4 |
| generation overreach | 22 | 19 | -3 |
| evidence insufficiency | 15 | 14 | -1 |
| right-family wrong-document | 13 | 13 | 0 |
| wrong-family retrieval | 12 | 12 | 0 |
| temporal_miss | 5 | 5 | 0 |

## Interpretation
- Phase 5 improved source identity metrics modestly: raw score, pass count, wrong family, wrong document, hallucinated identifier, hallucinated source, and missing gold document signal all moved in the right direction.
- The improvement is not large enough for acceptance. None of the seven numeric gate targets were met.
- The dominant remaining failure is no longer only source-family selection. The largest cluster is article/span/support selection after the correct or near-correct document is visible.
- The right-document wrong-article/span cluster regressed from 30 to 34, so the next phase should prioritize article/span selector logic and metadata/corpus backfill before any model fine-tuning.
