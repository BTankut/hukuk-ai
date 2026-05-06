# Phase 24HR Shadow Validation Plan

Generated: 2026-05-06

## Scope
This plan covers the next gated validation step for `TEB-04` and `TUZUK-05` after human legal review, deterministic TEB-04 materialization, TUZUK-05 offline scorer policy, and artifact-level non-live smoke.

This plan does not authorize live `8000`, internal eval, serving candidate, productization, model change, prompt change, top-k change, or fine-tuning.

## Current Evidence
| item | evidence |
|---|---|
| TEB-04 materialization | `reports/benchmark/phase_24HR_teb04_kdv_gut_materialization_report.md` |
| TEB-04 full spans | `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.jsonl` |
| TEB-04 chunked spans | `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.jsonl` |
| TUZUK-05 policy | `reports/benchmark/productization/post_human_review_tuzuk05_policy_update_report.md` |
| Artifact-level smoke | `reports/benchmark/phase_24HR_non_live_residual_smoke.md` |
| Shadow validation preflight | `reports/benchmark/phase_24HR_shadow_validation_preflight.md` |
| Shadow build dry-run manifest | `reports/benchmark/phase_24HR_shadow_collection_dry_run_report.md` |
| Guarded shadow build plan | `reports/benchmark/phase_24HR_shadow_collection_build_plan.md` |
| Guarded shadow build script | `scripts/benchmark/phase24hr_shadow_collection_build.py` |
| Guarded build fail-closed smoke | `reports/benchmark/phase_24HR_shadow_build_guard_smoke.md` |
| Option-A build report | `reports/benchmark/phase_24HR_shadow_collection_build_report.md` |
| Option-A read-only verify | `reports/benchmark/phase_24HR_shadow_collection_verify.md` |
| Authorization packet | `reports/benchmark/productization/phase_24HR_shadow_validation_authorization_packet.md` |

## Required Shadow Validation Steps
1. **Completed:** build a new shadow-only candidate collection from the current base collection.
2. **Completed:** insert TEB-04 chunked subspans, not the oversized full `I/C-2.1.3` section, to avoid truncation.
3. Preserve source metadata: `source_family=teblig`, `source_family_raw=TEBLIGLER`, `source_identifier=19631`, `canonical_source_key_v2`, `binding_source_key`, raw PDF SHA-256.
4. Do not create QID-specific runtime branches.
5. Use the local dry-run manifest as the row-level input contract for any authorized shadow collection build.
6. Re-run the guard smoke to verify the build script still refuses unsafe invocation before option-A authorization.
7. **Completed:** execute the guarded build script after option-A authorization and verify the target collection read-only.
8. Run a non-live candidate gateway or benchmark lane that points only to the shadow candidate collection; this requires option-B authorization.
9. Run targeted trace-on smoke for `TEB-04`, `TUZUK-05`, and guard rows that historically regress around source identity/family; this requires option-C authorization.
10. If targeted smoke passes, run full trace-on candidate benchmark; this requires option-D authorization.
11. Keep live `8000` unchanged until full gate review explicitly authorizes any switch.

## Targeted Acceptance Criteria
| qid | criteria |
|---|---|
| `TEB-04` | selected source includes `19631` / KDV Genel Uygulama Tebliği; selected span includes one of `I/C-2.1.3`, `I/C-2.1.5`, `I/C-2.1.5.2.1`, `I/C-2.1.5.2.2`, `I/C-2.1.5.3`; no old-only sirküler/özelge primary source. |
| `TUZUK-05` | answer applies general norm hierarchy rule; no fabricated exact tüzük; no `Gıda Maddelerinin... Tüzüğü` primary/source claim; kurum içi alt düzenleme cannot override tüzük/upper norm. |

## Full Benchmark Acceptance Criteria
| metric | required |
|---|---|
| `raw_score_proxy` | `>= 816` |
| `pass_proxy` | `>= 91` |
| `answer_contract_invalid_count` | `0` |
| `unsupported_confident_answer_count` | `0` |
| `source_key_v2_collision_detected_count` | `0` |
| `binding_source_key_collision_detected_count` | `0` |
| `wrong_family` | `<= 6`, preferred `<= 5` |
| `wrong_document` | `<= 4` |
| `hallucinated_identifier` | `<= 4` |

## Stop Conditions
Stop and report without switching anything if any of these occur:

- Candidate requires live `8000` change.
- Candidate requires product/internal-eval/serving scope opening.
- TEB-04 causes truncation of `I/C-2.1.3` or loses chunk metadata.
- TUZUK-05 selects a concrete irrelevant tüzük as primary source.
- Any source key or binding key collision appears.
- Any unsupported confident answer or answer contract invalid appears.
- Full benchmark score remains below product threshold.

## Required Authorization Before Execution
The following require explicit owner authorization before execution:

- Rebuilding or reloading a Milvus shadow collection after the completed option-A build/load.
- Starting a candidate gateway on a non-live port.
- Running a full trace-on candidate benchmark if it uses shared GPU/model resources.
- Any switch, cutover, internal eval opening, serving candidate opening, or productization decision.

Use `reports/benchmark/productization/phase_24HR_shadow_validation_authorization_packet.md` to approve the smallest needed scope.
