# Phase 21F Delta vs Phase20F

Phase21F run: `reports/benchmark/runs/20260429T174747Z_phase21F_full`
Phase20F baseline run: `reports/benchmark/runs/20260428T_phase20F_full_after_C_D`

| Metric | Phase21F | Phase20F | Delta |
| --- | ---: | ---: | ---: |
| `raw_score_proxy` | 800.55 | 755.6 | +44.95 |
| `pass_proxy` | 89 | 79 | +10 |
| `fail_proxy` | 11 | 21 | -10 |
| `wrong_family` | 6 | 10 | -4 |
| `wrong_document` | 5 | 9 | -4 |
| `hallucinated_identifier` | 5 | 11 | -6 |
| `unsupported_confident_answer_count` | 0 | 0 | +0 |
| `unsupported_confident_claim` | 0 | 0 | +0 |
| `answer_contract_invalid_count` | 0 | 0 | +0 |
| `source_key_v2_collision_detected_count` | 0 | 0 | +0 |
| `binding_source_key_collision_detected_count` | 0 | 0 | +0 |
| `auto_fail_triggered_count` | 2 | 4 | -2 |
| `support_insufficient_for_specific_claim_count` | 8 | 6 | +2 |
| `insufficient_canonical_span_evidence` | 3 | 2 | +1 |

## High-Signal Changes

- Raw score improved by `+44.95` points (`755.6` -> `800.55`).
- Pass count improved by `+10` (`79/100` -> `89/100`).
- Wrong-family blockers improved by `-4`; wrong-document blockers improved by `-4`; hallucinated identifier blockers improved by `-6`.
- Safety metrics stayed clean: unsupported confident answer/claim, contract invalid, source_key_v2 collision, and binding collision are all zero.
