# Phase 24S-E Delta vs Phase23R-E

Generated at UTC: `2026-05-05T08:20:55Z`

Phase23R-E stable baseline uses `reports/benchmark/phase_23R_E6_stability_full_summary.md`.

| Metric | Phase23R-E | Phase24S-E CBY live | Delta | Gate impact |
| --- | ---: | ---: | ---: | --- |
| raw_score_proxy | 816.86 | 727.18 | -89.68 | FAIL |
| pass_proxy | 91 | 73 | -18 | FAIL |
| wrong_family | 6 | 8 | +2 | FAIL |
| wrong_document | 4 | 21 | +17 | FAIL |
| hallucinated_identifier | 4 | 25 | +21 | FAIL |
| contract_valid | 100/100 | 100/100 | +0 | PASS |
| unsupported_confident_answer | 0 | 0 | +0 | PASS |
| answer_contract_invalid | 0 | 0 | +0 | PASS |
| source_key_v2_collision | 0 | 0 | +0 | PASS |
| binding_collision | 0 | 0 | +0 | PASS |

## Interpretation

The Phase24S CBY live run preserves contract/collision safety but materially regresses against the Phase23R-E stable baseline on score, pass count, wrong-document, wrong-family, and hallucinated-identifier counts. This is a hard rollback condition under the Phase24S brief.
