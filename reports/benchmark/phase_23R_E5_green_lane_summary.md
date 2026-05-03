# Phase 23R-E5 Green Lane Summary

Generated: 2026-05-03T09:12:43Z

Run dir: `reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full`

## Green Lane Criteria

| Criterion | Required | Observed | Result |
|---|---:|---:|---|
| answered | 100/100 | 100/100 | PASS |
| contract_valid | 100/100 | 100/100 | PASS |
| API errors | 0 | 0 | PASS |
| refused_or_empty | 0 | 0 | PASS |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |
| raw_score_proxy | >= 800 | 816.86 | PASS |
| pass_proxy | >= 89 | 91 | PASS |
| wrong_family | <= 6 | 6 | PASS |
| wrong_document | <= 5 | 4 | PASS |
| hallucinated_identifier / source | <= 5 | 4 | PASS |

## Status

Green lane: PASS.

No rollback condition was triggered by E5. The system remains approved for benchmark-only use, not public serving or productization.
