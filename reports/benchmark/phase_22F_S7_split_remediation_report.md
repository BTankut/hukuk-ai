# Phase 22F-S7 Split Remediation Final Report

## Commit SHA List

| SHA | Commit |
| --- | --- |
| `b55eca2` | `Design Phase 22F-S7 TEB source identity fix` |
| `c4e1767` | `Design Phase 22F-S7M MULGA current-law contract policy` |
| `2163451` | `Implement Phase 22F-S7 TEB source identity fix` |
| `3ea22c8` | `Run Phase 22F-S7 TEB targeted smoke` |
| `609e48c` | `Implement Phase 22F-S7M MULGA current-law contract policy` |
| `9bf047b` | `Extend Phase 22F-S7M historical repeal proof policy` |
| `4d69ae2` | `Refine Phase 22F-S7M historical proof answer surface` |
| `2ac7537` | `Hide Phase 22F-S7M internal proof reason from answer text` |
| `35ebca8` | `Align Phase 22F-S7M rent cap dual-role article surface` |
| `9ca4e11` | `Run Phase 22F-S7M MULGA targeted smoke` |
| `6a85a51` | `Run Phase 22F-S7 combined guard smoke` |
| `abf4cbf` | `Run Phase 22F-S7 full shadow benchmark` |

## S7 TEB Source Identity

Reports:

- `reports/benchmark/phase_22F_S7_teb_source_identity_design.md`
- `reports/benchmark/phase_22F_S7_teb_source_identity_implementation_report.md`
- `reports/benchmark/phase_22F_S7_teb_targeted_smoke_report.md`

Outcome:

- TEB targeted smoke passed.
- TEBLIGLER: `7/8`
- `TEB-06`: PASS
- `TEB-04`: source identity improved to `19631 / KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ`, but still has answer-surface proxy residual.
- unsupported confident answer: `0`
- answer contract invalid: `0`
- source/binding collisions: `0`

## S7M MULGA Current-Law Policy

Reports:

- `reports/benchmark/phase_22F_S7M_mulga_current_law_policy_design.md`
- `reports/benchmark/phase_22F_S7M_mulga_current_law_policy_implementation_report.md`
- `reports/benchmark/phase_22F_S7M_mulga_targeted_smoke_report.md`

Outcome:

- MULGA targeted smoke passed.
- MULGA: `5/5`
- `MULGA-05`: PASS, with primary `MULGA / 6570 m.gec1` and separate current-law basis `TBK m.344`.
- repealed_as_active_count: `0`
- unsupported confident answer: `0`
- answer contract invalid: `0`
- source/binding collisions: `0`

## Combined Guard

Report:

- `reports/benchmark/phase_22F_S7_combined_guard_smoke_report.md`

Outcome:

- combined pass_proxy: `38/40`
- MULGA: `5/5`
- TEBLIGLER: `7/8`
- `TEB-06`: PASS
- CB_GENELGE: `4/4`
- CB_KARAR: `8/8`
- YONETMELIK: `9/10`
- UY focused: `2/2`
- KANUN relation: `3/3`
- repealed_as_active_count: `0`
- unsupported confident answer: `0`
- answer contract invalid: `0`
- source/binding collisions: `0`

Combined guard passed and allowed full shadow benchmark.

## Full Shadow Benchmark

Reports:

- `reports/benchmark/phase_22F_S7_full_shadow_benchmark_summary.md`
- `reports/benchmark/phase_22F_S7_delta_vs_phase22A.md`
- `reports/benchmark/phase_22F_S7_decision.md`

Outcome:

- full pass_proxy: `91/100`
- raw_score_proxy: `816.86 / 1000`
- wrong_family: `6`
- wrong_document: `4`
- hallucinated_identifier: `4`
- unsupported confident answer: `0`
- answer contract invalid: `0`
- source_key_v2_collision: `0`
- binding_collision: `0`
- repealed_as_active_count: `0`

Minimum gate passed. Preferred gate missed only `wrong_family <= 5` by one row.

## Delta vs Phase 22A

| Metric | Phase 22A | Phase 22F-S7 | Delta |
| --- | ---: | ---: | ---: |
| raw_score_proxy | 800.55 | 816.86 | +16.31 |
| pass_proxy | 89 | 91 | +2 |
| wrong_family | 6 | 6 | 0 |
| wrong_document | 5 | 4 | -1 |
| hallucinated_identifier | 5 | 4 | -1 |
| unsupported_confident_answer | 0 | 0 | 0 |
| answer_contract_invalid | 0 | 0 | 0 |
| source_key_v2_collision | 0 | 0 | 0 |
| binding_collision | 0 | 0 | 0 |

## Decision

Option A applies: full shadow passes the minimum gate.

This phase should proceed to a controlled cutover brief, not automatic cutover.

## Cutover Recommendation

Prepare controlled cutover planning with:

- explicit user approval before switching live `8000`
- live-serving lane binding verification
- Open WebUI/model endpoint verification
- post-switch smoke and runtime stability audit
- rollback path retained until post-switch stability is proven

## Productization Gate

Productization remains closed until controlled cutover and post-switch stability audit complete.

## Fine-Tuning Gate

Fine-tuning remains closed. This phase did not require model-weight changes; gains came from source identity, temporal contract policy, and answer-surface shaping.

## Remaining Risks

- Preferred full-shadow gate is not fully met because `wrong_family = 6`, one above preferred.
- `TEB-04` has correct source identity but still answer-surface proxy failure.
- `YON-04`, `TUZUK-05`, `KANUN-12`, and `KKY-03` remain document/source selection residuals.
- `CBY-04`, `KKY-01`, and related rows carry the residual wrong-family burden.
- All results are shadow-only; no live `8000` cutover was performed in this phase.
