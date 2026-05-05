# Phase 24U-D Ablation vs Current Trace-On Delta

Generated UTC: `2026-05-05T15:31:56Z`

## Matched Runtime Check

| Field | Current BASE | Ablation | Match / Intended Difference |
|---|---|---|---|
| git_sha | `66de1538b6f007d29f6b50189d53b0d3116dd97e` | `66de1538b6f007d29f6b50189d53b0d3116dd97e` | match |
| DGX_MODEL | `/models/merged_model_fabric_stage_20260321` | `/models/merged_model_fabric_stage_20260321` | match |
| include_trace | `True` | `True` | match |
| collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | match |
| entity_count | 349403 | 349403 | match |
| supplement flag | current/default | `false` | intended difference |
| live_8000_untouched | `True` | `True` | match |

## Aggregate Delta

| Metric | Current BASE | Ablation | Delta | Interpretation |
|---|---:|---:|---:|---|
| raw_score_proxy | 805.09 | 804.42 | -0.67 | worsened |
| pass_proxy | 89 | 89 | +0 | unchanged |
| wrong_family | 8 | 8 | +0 | unchanged |
| wrong_document | 3 | 3 | +0 | unchanged |
| hallucinated_identifier | 7 | 7 | +0 | unchanged |
| insufficient_canonical_span_evidence | 1 | 2 | +1 | worsened |
| answer_contract_invalid | 0 | 0 | +0 | unchanged |
| source_key_v2_collision | 0 | 0 | +0 | unchanged |
| binding_collision | 0 | 0 | +0 | unchanged |

## Changed Rows

| QID | Current score | Ablation score | Current pass | Ablation pass | Current failure classes | Ablation failure classes |
|---|---:|---:|---|---|---|---|
| YON-04 | 8.22 | 7.55 | PASS | PASS | `missing_required_content_signal | partial_grounding_only` | `missing_required_content_signal | partial_grounding_only | insufficient_canonical_span_evidence` |

## Decision Input

Ablation restores Phase23R-E level = `NO`.

Because ablation does not restore the `816.86 / 91` reference and slightly worsens the current BASE result, source supplement drift is not sufficient as the remaining-root-cause explanation.
