# Phase 23R-E6 Green Lane Summary

Generated: 2026-05-03T10:16:11Z

Run dir: `reports/benchmark/runs/20260503T091350Z_phase23R_E6_stability_full`

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
| raw_score_delta vs E5 | >= -10 | 0.00 | PASS |
| pass_delta vs E5 | >= -2 | 0 | PASS |
| wrong_family | <= E5 + 1 | 6 | PASS |
| wrong_document | <= E5 + 1 | 4 | PASS |
| hallucinated_identifier / source | <= E5 + 1 | 4 | PASS |

## Status

Green lane: PASS.

The benchmark-only cutover remains stable after the second full run.
