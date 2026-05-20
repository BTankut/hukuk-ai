# FAZ12 Output Parity First-Divergence Table

Tarih: 2026-03-25

Referans:
- `evaluation/reports/faz12-output-parity-frontier-replay-2026-03-25.md`
- `coordination/faz12-output-parity-reconciliation-2026-03-25.md`

## Genel Ozet

- `frontier_count = 86`
- `first_divergence_assigned_count = 86`
- `primary_reason_assigned_count = 86`
- `unexplained_count = 80`

## Stage Dagilimi

| stage | count |
| --- | ---: |
| `preprojection_hash` | 80 |
| `final_mode_mapping_hash` | 6 |

## Primary Reason Dagilimi

| primary_reason | count |
| --- | ---: |
| `unexplained_post_preprojection_drift` | 80 |
| `final_mode_mapping_delta` | 6 |

## Family Bazli Dagilim

| family | frontier_count | dominant_stage | dominant_reason |
| --- | ---: | --- | --- |
| `faz1-50` | 17 | `preprojection_hash` | `unexplained_post_preprojection_drift` |
| `v2-95` | 63 | `preprojection_hash` | `unexplained_post_preprojection_drift` |
| `v3-170` | 6 | `final_mode_mapping_hash` | `final_mode_mapping_delta` |
