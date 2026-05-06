# Phase 24HR Shadow Validation Authorization Packet

Generated: 2026-05-06

## Request
Authorization is requested for the next gated, non-live validation step for `TEB-04` and `TUZUK-05`.

This authorization is **not** a productization approval, internal eval opening, serving-candidate opening, live `8000` switch, model change, prompt/top-k change, or fine-tuning approval.

## Preflight Evidence
| item | evidence |
|---|---|
| Local shadow preflight | `reports/benchmark/phase_24HR_shadow_validation_preflight.md` |
| Preflight result | `PASS`, 21/21 checks |
| Non-live residual smoke | `reports/benchmark/phase_24HR_non_live_residual_smoke.md` |
| Non-live smoke result | `PASS`, 9/9 checks |
| Shadow validation plan | `reports/benchmark/productization/phase_24HR_shadow_validation_plan.md` |

## Authorization Options
Approve only the smallest scope needed.

| option | authorization scope | side-effect boundary |
|---|---|---|
| A | Build/load a Milvus shadow collection for `TEB-04` chunked spans and `TUZUK-05` policy validation. | No live `8000`; no existing base collection overwrite; no serving candidate. |
| B | Start a non-live candidate gateway on a separate port after shadow collection build. | No live `8000`; no public endpoint; no Open WebUI switch. |
| C | Run targeted trace-on candidate smoke for `TEB-04`, `TUZUK-05`, and source-identity guard rows. | No full benchmark yet; no gate change. |
| D | If targeted smoke passes, run full trace-on candidate benchmark. | Uses shared model/GPU resources; no product/internal/serving switch. |

## Proposed Execution Order
1. Re-run `python3 scripts/benchmark/phase24hr_shadow_preflight.py`.
2. Build/load a shadow-only candidate collection if option A is approved.
3. Start a non-live candidate gateway if option B is approved.
4. Run targeted trace-on smoke if option C is approved.
5. Run full trace-on candidate benchmark only if option D is approved and targeted smoke passes.
6. Update productization reports; keep final gate `not_productization_ready` unless all brief gates pass or explicit waivers are recorded.

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
