# Phase 18 Recovery A1.7 Phase17F Comparison

| Run | Total | Raw Score | Pass | wrong_family | wrong_document | hallucinated_identifier | unsupported_confident_claim |
|---|---:|---:|---:|---:|---:|---:|---:|
| `original_phase17f_full` | `100` | `767.91` | `77` | `12` | `10` | `18` | `8` |
| `live_8000_A0_smoke20` | `20` | `88.77` | `6` | `7` | `12` | `4` | `0` |
| `A1_6_candidate_smoke20` | `20` | `133.86` | `13` | `3` | `4` | `5` | `0` |
| `A1_7_candidate_full100` | `100` | `729.1` | `71` | `17` | `17` | `24` | `0` |

## Interpretation

- The large collection materially improves the A0 smoke result, but the full 100 candidate remains below the Phase17F original full-run baseline.
- A1.7 misses the full acceptance gate by small but material margins: score, pass count, wrong family, wrong document, and hallucinated identifier.
- This is not sufficient for controlled live cutover.
