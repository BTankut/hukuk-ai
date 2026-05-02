# Phase 22F-S2 Overapplication Fixture
Fixture source: Phase22A baseline run and Phase22F-S full shadow run. No private answer key was used. No runtime behavior was changed.
## Summary
- Fixture rows: 9
- Temporal alignment applied before fix: 8
- Relation-chain expansion applied before fix: 0
- Rows where temporal alignment should apply under S2 scope: 0
## Rows
| qid | A score | F-S score | selected family | claimed family | selected state | claimed state | temporal applied | relation chain | should apply | expected after fix |
|---|---:|---:|---|---|---|---|---:|---:|---:|---|
| `KANUN-05` | 8.17 | 6.10 | KANUN | MULGA | active | repealed | True | False | False | preserve KANUN claimed family/effective_state when selected source is active KANUN and no relation-chain metadata exists |
| `KANUN-10` | 7.15 | 5.35 | KANUN | MULGA | active | repealed | True | False | False | preserve KANUN claimed family/effective_state when selected source is active KANUN and no relation-chain metadata exists |
| `KANUN-14` | 8.24 | 6.44 | KANUN | MULGA | active | repealed | True | False | False | preserve KANUN claimed family/effective_state when selected source is active KANUN and no relation-chain metadata exists |
| `KHK-03` | 7.25 | 5.45 | KHK | MULGA | active | repealed | True | False | False | preserve KHK claimed family unless explicit relation-chain currentness/repeal metadata exists |
| `MULGA-05` | 7.25 | 5.45 | MULGA | MULGA | repealed | repealed | True | False | False | genuine MULGA row; preserve selected MULGA/repealed surface, but do not apply relation-chain temporal rewrite without relation metadata |
| `TEB-03` | 8.00 | 4.55 | TEBLIGLER | MULGA | active | repealed | True | False | False | preserve TEBLIGLER claimed family; do not rewrite to MULGA from temporal wording alone |
| `TEB-04` | 7.25 | 5.45 | TEBLIGLER | MULGA | active | repealed | True | False | False | preserve TEBLIGLER claimed family; do not rewrite to MULGA from temporal wording alone |
| `TUZUK-03` | 8.58 | 5.00 | TUZUK | MULGA | active | repealed | True | False | False | preserve TUZUK claimed family without explicit relation-chain rewrite requirement |
| `UY-01` | 8.09 | 6.02 | KKY | YONETMELIK | active | active | False | False | False | preserve UY selected/claimed family unless selected evidence truly belongs to another family; temporal alignment must not rewrite family |
## Fixture Decision
The fixture confirms the S2 target: active non-MULGA rows must preserve selected family/identifier unless explicit relation-chain metadata justifies claim-family/effective-state rewrite. `MULGA-05` remains a separate genuine-MULGA article/claim-surface guard.
