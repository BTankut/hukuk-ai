# Phase 24U Trace-Normalized Ablation Decision

Generated UTC: `2026-05-05T15:36:11Z`  
Report HEAD before commit: `b7f304f076545ee5b59969519a98000a960142dc`

## Decision

```text
selected_option = Option D — Code regression not supplement-related
source_supplement_drift_confirmed = false
current_code_reproduces_phase23RE = false
cby_trace_on_clean_but_base_still_drifted = true
next_phase = commit-level regression audit between Phase23R-E accepted state and current HEAD
```

## Evidence

| Run | Collection / flag | Raw | Pass | Key result |
|---|---|---:|---:|---|
| Phase23R-E reference | BASE, trace-on | 816.86 | 91 | accepted baseline |
| Phase24U-B BASE trace-on | BASE, current/default supplements | 805.09 | 89 | clean run, but `-11.77 / -2` vs Phase23R-E |
| Phase24U-C CBY trace-on | CBY collection, current/default supplements | 807.27 | 90 | CBY consideration PASS, not cutover |
| Phase24U-D ablation | BASE, `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=false` | 804.42 | 89 | did not restore; slightly worse than BASE |

## Row Attribution

Phase24U-E found:

```text
rows_attributed = 8
fixed_by_ablation = 0
worsened_by_ablation = 1
unchanged = 7
phase23_pass_to_current_fail = 5
current_to_ablation_pass_changes = 0
```

The only row worsened by ablation was `YON-04`; no regressed row was fixed by disabling source supplements.

## Productization / Runtime Decision

```text
productization = CLOSED
internal_eval = CLOSED
fine_tuning = CLOSED
live_cutover = CLOSED
source_supplements_disablement = REJECTED
CBY_cutover = REJECTED_FOR_NOW
```

Reason: CBY improved narrowly and cleanly, but BASE still fails Phase23R-E parity; ablation does not restore the accepted baseline.

## Safe Next Action

Open the next phase as a commit-level regression audit. Scope should compare the Phase23R-E accepted code/config/runtime against current runtime for at least:

- selector/source identity changes affecting `KANUN-08` and `YON-05`
- answer/slot/scoring policy changes affecting `KANUN-02`, `MULGA-04`, and `YON-08`
- preservation of positive current improvements on `CBY-04`, `KANUN-12`, and `YON-04`

No QID-specific runtime branch or answer-key-driven patch is authorized.
