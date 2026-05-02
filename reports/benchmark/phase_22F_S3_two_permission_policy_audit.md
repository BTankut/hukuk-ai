# Phase 22F-S3 Two-Permission Policy Audit
Audit/design-only classification. Inputs are existing Phase 22F-S full shadow trace/candidate artifacts; no benchmark run, answer-key read, runtime code change, retrieval change, or live cutover was performed.
## Inputs
- `reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z/candidate_answers.csv`
- `reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z/trace.jsonl`
## Summary
- Rows classified: 13/13
- Active non-MULGA rows with claim-family rewrite denied: 7
- MULGA rows with historical surface path: 5
## Policy Bucket Counts
- `active_non_mulga_preserve_family`: 7
- `legacy_mulga_historical_surface_without_relation_chain`: 4
- `manual_review_required`: 1
- `relation_chain_historical_three_part_claim`: 1
## Row Bucket Table
| qid | benchmark | selected family | current claimed | state | relation | preserve selected | family rewrite | historical surface | bucket |
|---|---|---|---|---|---:|---:|---:|---:|---|
| `KANUN-05` | KANUN | KANUN | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `KANUN-10` | KANUN | KANUN | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `KANUN-14` | KANUN | KANUN | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `KHK-03` | KHK | KHK | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `TEB-03` | TEBLIGLER | TEBLIGLER | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `TEB-04` | TEBLIGLER | TEBLIGLER | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `TUZUK-03` | TUZUK | TUZUK | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `UY-01` | UY | KKY | YONETMELIK | active | False | True | False | False | `manual_review_required` |
| `MULGA-01` | MULGA | KKY | MULGA | historical_repealed | True | False | True | True | `relation_chain_historical_three_part_claim` |
| `MULGA-02` | MULGA | KKY | MULGA | active | False | False | True | True | `legacy_mulga_historical_surface_without_relation_chain` |
| `MULGA-03` | MULGA | TUZUK | MULGA | active | False | False | True | True | `legacy_mulga_historical_surface_without_relation_chain` |
| `MULGA-04` | MULGA | KHK | MULGA | active | False | False | True | True | `legacy_mulga_historical_surface_without_relation_chain` |
| `MULGA-05` | MULGA | MULGA | MULGA | repealed | False | False | True | True | `legacy_mulga_historical_surface_without_relation_chain` |
## Audit Decision
The policy must not reuse a single temporal gate. Active non-MULGA preservation and legacy/MULGA historical-surface permission are separate decisions. `MULGA-02`, `MULGA-03`, and `MULGA-04` prove that relation-chain absence cannot by itself suppress historical claim surface when the benchmark/query is genuinely MULGA-like.
