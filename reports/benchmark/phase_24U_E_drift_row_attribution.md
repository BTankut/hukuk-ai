# Phase 24U-E Drift Row Attribution

Generated UTC: `2026-05-05T15:35:04Z`  
Report HEAD before commit: `43869fdf9a8e82c3e2dc449f2c000cc1f82ad576`

## Scope

- Rows included: `8`
- Mandatory focus rows: `MULGA-04`, `KANUN-08`, `KANUN-02`, `YON-05`, `YON-08`
- Additional pass/fail-change rows: `CBY-04, KANUN-12, YON-04`

## Aggregate Attribution

```text
fixed_by_ablation = 0
worsened_by_ablation = 1
unchanged = 7
mixed = 0
unknown = 0
phase23_pass_to_current_fail = 5 (KANUN-02, KANUN-08, MULGA-04, YON-05, YON-08)
phase23_fail_to_current_pass = 3 (CBY-04, KANUN-12, YON-04)
current_to_ablation_pass_changes = 0 ()
```

## Key Finding

Ablation did not fix any Phase23R-E to current regression row. Seven included rows were unchanged by ablation, and `YON-04` worsened under ablation. This supports Phase24U-D: source supplement drift is not sufficient to explain the remaining gap.

## Row Table

| QID | Phase23 | Current | Ablation | Effect | Root cause | Safe next action |
|---|---:|---:|---:|---|---|---|
| CBY-04 | 6.85 FAIL | 7.12 PASS | 7.12 PASS | `unchanged` | current code improved this row vs Phase23R-E; not a remediation target, preserve behavior while auditing regressions | no fix; protect as positive current behavior during regression audit |
| KANUN-02 | 8.65 PASS | 3.25 FAIL | 3.25 FAIL | `unchanged` | same selected source as Phase23R-E but answer/slot/scoring policy regressed; unchanged under ablation, so not source-supplement caused | open commit-level regression audit; compare Phase23R-E accepted code/config vs current for selector, answer slots, and scorer policy |
| KANUN-08 | 7.55 PASS | 1.45 FAIL | 1.45 FAIL | `unchanged` | current selected/claimed source identity drift vs Phase23R-E; unchanged under ablation, so not source-supplement caused | open commit-level regression audit; compare Phase23R-E accepted code/config vs current for selector, answer slots, and scorer policy |
| KANUN-12 | 1.45 FAIL | 8.99 PASS | 8.99 PASS | `unchanged` | current code improved this row vs Phase23R-E; not a remediation target, preserve behavior while auditing regressions | no fix; protect as positive current behavior during regression audit |
| MULGA-04 | 7.55 PASS | 0.00 FAIL | 0.00 FAIL | `unchanged` | same selected source as Phase23R-E but answer/slot/scoring policy regressed; unchanged under ablation, so not source-supplement caused | open commit-level regression audit; compare Phase23R-E accepted code/config vs current for selector, answer slots, and scorer policy |
| YON-04 | 3.25 FAIL | 8.22 PASS | 7.55 PASS | `worsened_by_ablation` | source supplement appears beneficial for this row; disabling removed/weakened canonical span support, not a fix | do not disable supplements; preserve current supplement path and audit why Phase23R-E differed separately |
| YON-05 | 9.55 PASS | 5.75 FAIL | 5.75 FAIL | `unchanged` | current selected/claimed source identity drift vs Phase23R-E; unchanged under ablation, so not source-supplement caused | open commit-level regression audit; compare Phase23R-E accepted code/config vs current for selector, answer slots, and scorer policy |
| YON-08 | 7.25 PASS | 6.80 FAIL | 6.80 FAIL | `unchanged` | same selected source as Phase23R-E but answer/slot/scoring policy regressed; unchanged under ablation, so not source-supplement caused | open commit-level regression audit; compare Phase23R-E accepted code/config vs current for selector, answer slots, and scorer policy |

## Decision Input

```text
source_supplement_drift_confirmed = false
safe_decision_option = Option D — commit-level code regression audit
do_not_disable_source_supplements = true
do_not_cut_over_cby_yet = true
```
