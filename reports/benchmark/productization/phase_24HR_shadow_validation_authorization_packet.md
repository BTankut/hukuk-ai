# Phase 24HR Shadow Validation Authorization Packet

Generated: 2026-05-06

## Request
Authorization is requested for the next gated, non-live validation step for `TEB-04` and `TUZUK-05`.

Option `A` was approved by the owner and executed on 2026-05-06. Options `B`, `C`, and `D` remain unauthorized.

This authorization is **not** a productization approval, internal eval opening, serving-candidate opening, live `8000` switch, model change, prompt/top-k change, or fine-tuning approval.

## Preflight Evidence
| item | evidence |
|---|---|
| Local shadow preflight | `reports/benchmark/phase_24HR_shadow_validation_preflight.md` |
| Preflight result | `PASS`, 43/43 checks after option-A build/load, read-only verification, and option-B guard coverage |
| Non-live residual smoke | `reports/benchmark/phase_24HR_non_live_residual_smoke.md` |
| Non-live smoke result | `PASS`, 9/9 checks |
| Shadow build dry-run manifest | `reports/benchmark/phase_24HR_shadow_collection_dry_run_report.md` |
| Dry-run result | `PASS`, 59 proposed delta rows; no live 8000, Milvus, embedding, gateway, or model inference |
| Guarded shadow build plan | `reports/benchmark/phase_24HR_shadow_collection_build_plan.md` |
| Guarded build script | `scripts/benchmark/phase24hr_shadow_collection_build.py`; refuses before Milvus without `--execute` and `OPTION_A_APPROVED_PHASE24HR` |
| Guard smoke | `reports/benchmark/phase_24HR_shadow_build_guard_smoke.md` |
| Guard smoke result | `PASS`, 4/4 fail-closed paths; no live 8000, Milvus, embedding, gateway, or model inference |
| Option-A build report | `reports/benchmark/phase_24HR_shadow_collection_build_report.md` |
| Option-A build result | `PASS`, target collection `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr`, 349462 rows, 59 delta rows, `load_after_build=true` |
| Option-A read-only verify | `reports/benchmark/phase_24HR_shadow_collection_verify.md` |
| Option-A verify result | `PASS`, 59/59 delta rows found in target, base delta collision `0`, load state observed `Loaded` |
| Shadow validation plan | `reports/benchmark/productization/phase_24HR_shadow_validation_plan.md` |
| Option-B candidate gateway plan | `reports/benchmark/productization/phase_24HR_option_B_candidate_gateway_plan.md` |
| Option-B guarded runner | `scripts/benchmark/phase24hr_option_b_candidate_gateway.py` |
| Option-B runner plan | `reports/benchmark/phase_24HR_option_B_candidate_gateway_runner_plan.md`; `READY_FOR_OPTION_B_AUTHORIZATION`, prerequisites `PASS` |
| Option-B guard smoke | `reports/benchmark/phase_24HR_option_B_candidate_gateway_guard_smoke.md`; `PASS`, 5/5 fail-closed paths; no live 8000, gateway, chat, or model inference |

## Authorization Options
Approve only the smallest scope needed.

| option | authorization scope | side-effect boundary |
|---|---|---|
| A | Build/load a Milvus shadow collection for `TEB-04` chunked spans and `TUZUK-05` policy validation. | **Completed**; no live `8000`; no existing base collection overwrite; no serving candidate. |
| B | Start a non-live candidate gateway on a separate port after shadow collection build. | No live `8000`; no public endpoint; no Open WebUI switch. |
| C | Run targeted trace-on candidate smoke for `TEB-04`, `TUZUK-05`, and source-identity guard rows. | No full benchmark yet; no gate change. |
| D | If targeted smoke passes, run full trace-on candidate benchmark. | Uses shared model/GPU resources; no product/internal/serving switch. |

## Proposed Execution Order
1. Re-run `python3 scripts/benchmark/phase24hr_shadow_preflight.py`.
2. Re-run `python3 scripts/benchmark/phase24hr_shadow_build_dry_run.py`.
3. Re-run `python3 scripts/benchmark/phase24hr_shadow_build_guard_smoke.py`.
4. Re-run `python3 scripts/benchmark/phase24hr_shadow_collection_build.py plan`.
5. Option A is complete; do not rebuild unless explicitly re-authorized.
6. Start a non-live candidate gateway only if option B is approved, using `scripts/benchmark/phase24hr_option_b_candidate_gateway.py` and following `reports/benchmark/productization/phase_24HR_option_B_candidate_gateway_plan.md`.
7. Run targeted trace-on smoke only if option C is approved.
8. Run full trace-on candidate benchmark only if option D is approved and targeted smoke passes.
9. Update productization reports; keep final gate `not_productization_ready` unless all brief gates pass or explicit waivers are recorded.

## Hard Stop Conditions
Stop immediately and report if any condition occurs:

- Any live `8000` change is required.
- Any base collection overwrite is required.
- Any source key or binding key collision is detected.
- Any `answer_contract_invalid_count > 0`.
- Any `unsupported_confident_answer_count > 0`.
- `TEB-04` loses `19631` / KDV Genel Uygulama Tebliği as source.
- `TEB-04` truncates `I/C-2.1.3` instead of using chunked spans.
- `TUZUK-05` selects a concrete irrelevant tüzük as primary source.
- Full benchmark remains below `raw_score_proxy >= 816` or `pass_proxy >= 91`.

## Explicit Non-Authorization
Unless separately approved, this packet does not authorize:

- Live `8000` cutover.
- Internal eval opening.
- Serving candidate opening.
- Productization/public serving.
- Fine-tuning.
- Model path change.
- Prompt or top-k change.
- Open WebUI backend switch.
