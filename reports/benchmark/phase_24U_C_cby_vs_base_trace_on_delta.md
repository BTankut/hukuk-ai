# Phase 24U-C CBY vs BASE Trace-On Delta

Generated UTC: `2026-05-05T14:29:20Z`

## Matched Runtime Check

| Field | BASE | CBY | Match / Intended Difference |
|---|---|---|---|
| git_sha | `66de1538b6f007d29f6b50189d53b0d3116dd97e` | `66de1538b6f007d29f6b50189d53b0d3116dd97e` | match |
| DGX_MODEL | `/models/merged_model_fabric_stage_20260321` | `/models/merged_model_fabric_stage_20260321` | match |
| include_trace | `True` | `True` | match |
| collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06` | intended difference |
| entity_count | 349403 | 349405 | intended difference |
| live_8000_untouched | `True` | `True` | match |

## Aggregate Delta

| Metric | BASE | CBY | Delta | CBY acceptance |
|---|---:|---:|---:|---|
| raw_score_proxy | 805.09 | 807.27 | +2.18 | PASS |
| pass_proxy | 89 | 90 | +1 | PASS |
| wrong_family | 8 | 8 | +0 | PASS |
| wrong_document | 3 | 3 | +0 | PASS |
| hallucinated_identifier | 7 | 7 | +0 | PASS |
| answer_contract_invalid | 0 | 0 | +0 | PASS |
| source_key_v2_collision | 0 | 0 | +0 | PASS |
| binding_collision | 0 | 0 | +0 | PASS |

## Changed Rows

| QID | BASE score | CBY score | BASE pass | CBY pass | BASE failure classes | CBY failure classes |
|---|---:|---:|---|---|---|---|
| CBKAR-03 | 7.90 | 8.80 | PASS | PASS | `missing_required_content_signal | partial_grounding_only` | `missing_required_content_signal | partial_grounding_only` |
| CBY-02 | 8.65 | 9.10 | PASS | PASS | `missing_required_content_signal | partial_grounding_only` | `missing_required_content_signal | partial_grounding_only` |
| CBY-06 | 6.80 | 7.90 | FAIL | PASS | `missing_required_content_signal | partial_grounding_only` | `missing_required_content_signal | partial_grounding_only` |
| YON-09 | 7.82 | 7.55 | PASS | PASS | `missing_required_content_signal | partial_grounding_only` | `missing_required_content_signal | partial_grounding_only` |

## Decision

CBY consideration gate = `PASS`. The only pass/fail improvement is `CBY-06`; no aggregate safety or identity counter regressed. Because BASE remains below Phase23R-E, this is not a cutover authorization.
