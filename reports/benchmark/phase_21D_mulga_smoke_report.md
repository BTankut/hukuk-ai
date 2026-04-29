# Phase 21D MULGA Smoke Report

## Scope

- Audit commit: `a539502` (`Phase 21D MULGA source/span audit`)
- Remediation commit: this report's commit (`Remediate MULGA source span routing`)
- Runtime: `hukuk-ai-poc` through `http://127.0.0.1:8000/v1`
- Model endpoint: `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- Model id/path: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Embedding: remote `intfloat/multilingual-e5-large-instruct`
- Guardrails / Presidio / verification: disabled for benchmark runtime

## Remediation Summary

Runtime changes are systemic and not QID-specific:

- `article_span_selection.py`: temporary / transitional clause queries now prefer `gecici`, `GEC`, `ek`, and additional-article spans before ordinary neighboring articles.
- `article_span_selection.py`: selected-document-only bundling no longer treats an inferred query article token as a precise lock unless the selected main article actually matches it.
- `article_span_selection.py`: cross-document exact article matches can become supporting evidence spans, allowing current-law support such as `TBK m.344` to remain visible beside a historical/MULGA main source.
- `source_identity.py`: historical/MULGA questions with blocked current-law prior can keep a controlled current-law `kanun` support bridge.
- `source_identity.py`: supporting-family bridge ranking now prioritizes explicit article references already present in the retrieval contract.
- `chat.py`: rent-increase/TBK domain detection now covers natural currentness/temporary-regime formulations, and weak same-family metadata locks are suppressed when they conflict with a domain-law hint.
- `chat.py`: pre-generation family-pool query now includes deterministic exact article refs so upstream family filtering can see forced support refs.

No changes were made to `answer_synthesis.py` or `answer_slots.py`.

## MULGA Smoke

Run:

```text
reports/benchmark/runs/20260429T_phase21D_mulga_smoke_v2
```

Summary:

| metric | value |
|---|---:|
| pass_proxy | 4/5 |
| average_score_0_10_proxy | 6.42 |
| unsupported_confident_answer_count | 0 |
| answer_contract_invalid_count | 0 |
| source_key_v2_collision_detected_count | 0 |
| binding_source_key_collision_detected_count | 0 |
| repealed_as_active_count | 0 |
| hallucinated_source_count | 0 |

Rows:

| qid | score | status | selected_main_span_id | note |
|---|---:|---|---|---|
| MULGA-01 | 0.00 | FAIL | `832 m.98/f.0` | residual insufficient canonical span / wrong article |
| MULGA-02 | 9.10 | PASS | `33899 m.32/f.0` | guard preserved |
| MULGA-03 | 7.55 | PASS | `743 m.924/f.0` | guard preserved |
| MULGA-04 | 8.22 | PASS | `556 m.42/f.0` | guard preserved |
| MULGA-05 | 7.25 | PASS | `6570 m.GEC1/f.0` | recovered; `TBK m.344/f.0` retained as supporting span |

Phase 21D acceptance target `MULGA pass >= 4/5` is met.

## Regression Guard

Run:

```text
reports/benchmark/runs/20260429T_phase21D_regression_guard
```

Guard results:

| group | result |
|---|---:|
| TEB | 7/8 |
| YON | 9/10 |
| CBG | 4/4 |
| UY focused | 2/2 |
| KANUN relation | 3/3 |

Regression safety counters:

| metric | value |
|---|---:|
| unsupported_confident_answer_count | 0 |
| answer_contract_invalid_count | 0 |
| source_key_v2_collision_detected_count | 0 |
| binding_source_key_collision_detected_count | 0 |
| repealed_as_active_count | 0 |

Known residual failing rows remain:

| qid | score | selected_main_span_id | note |
|---|---:|---|---|
| TEB-06 | 3.25 | `23093 m.6/f.0` | pre-existing TEB source/span blocker |
| YON-04 | 3.25 | `12536 m.23/f.0` | pre-existing YON document blocker |

## Decision

Phase 21D is accepted.

Proceed to the next planned phase with `MULGA-01`, `TEB-06`, and `YON-04` tracked as residual source/span blockers. Productization remains closed unless separately authorized.
