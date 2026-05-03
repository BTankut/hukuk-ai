# Phase 23R-E6 Delta vs E5

Generated: 2026-05-03T10:16:11Z

E5 run: `reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full`

E6 run: `reports/benchmark/runs/20260503T091350Z_phase23R_E6_stability_full`

## Stability Delta

| Metric | E5 | E6 | Delta E6-E5 | Tolerance | Result |
|---|---:|---:|---:|---:|---|
| raw_score_proxy | 816.86 | 816.86 | 0.00 | >= -10 | PASS |
| pass_proxy | 91 | 91 | 0 | >= -2 | PASS |
| wrong_family | 6 | 6 | 0 | <= E5 + 1 | PASS |
| wrong_document | 4 | 4 | 0 | <= E5 + 1 | PASS |
| hallucinated_identifier / source | 4 | 4 | 0 | <= E5 + 1 | PASS |
| unsupported_confident_answer | 0 | 0 | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | 0 | 0 | PASS |
| contract_valid | 100 | 100 | 0 | 100/100 | PASS |
| API errors | 0 | 0 | 0 | 0 | PASS |
| refused_or_empty | 0 | 0 | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | 0 | 0 | PASS |
| binding_collision | 0 | 0 | 0 | 0 | PASS |

## Decision

Stability tolerance: PASS.

E6 is metric-identical to E5 on all hard and tolerance-gated metrics.
