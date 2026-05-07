# Phase 24HR Option C Targeted Smoke Plan

Generated: 2026-05-06

## Scope
This is a non-executing plan for option `C` in `phase_24HR_shadow_validation_authorization_packet.md`.

Option `C` means running a targeted trace-on candidate smoke against the option-B non-live candidate gateway after option B has started and produced health evidence.

This plan does not authorize or perform:

- Live `8000` cutover.
- Internal eval opening.
- Serving-candidate opening.
- Productization or public serving.
- Open WebUI backend switch.
- Model, prompt, top-k, or fine-tuning change.
- Full benchmark execution.

## Current Status
Option `C` was approved by the owner and executed on 2026-05-07.

Technical run status is `PASS`, but targeted quality gate status is `FAIL`.

Evidence:

- Option-B start report: `reports/benchmark/phase_24HR_option_B_candidate_gateway_start_report.md`
- Option-C runner plan: `reports/benchmark/phase_24HR_option_C_targeted_smoke_runner_plan.md`
- Option-C run report: `reports/benchmark/phase_24HR_option_C_targeted_smoke_run_report.md`
- Candidate API URL: `http://127.0.0.1:8010/v1`
- Targeted smoke called chat/model inference for 4 QIDs only.
- No full benchmark, live cutover, internal eval, serving candidate, productization, prompt/top-k change, model change, or fine-tuning was performed.

Result summary:

- `raw_score_proxy=10.45/40`
- `pass_proxy=0/4`
- hard counters stayed clean: answer contract invalid `0`, unsupported confident answer `0`, source-key collision `0`, binding collision `0`
- `TUZUK-05` selected a concrete irrelevant tüzük as primary source, so the stop condition failed
- Option `D` is blocked until systemic remediation passes another targeted smoke under explicit authorization

## Targeted QIDs
| qid | reason |
|---|---|
| `TEB-04` | Verifies KDV GUT source `19631` and chunked materialized spans. |
| `TUZUK-05` | Verifies no fabricated exact tüzük and general hierarchy policy handling. |
| `KANUN-08` | Source-identity guard row for domain-incompatible title-only primary selection. |
| `YON-05` | Source-identity guard row for support-law identifier demotion and regulation primary selection. |

## Required Prerequisites
| prerequisite | evidence | required state |
|---|---|---|
| Option-B candidate gateway start | `reports/benchmark/phase_24HR_option_B_candidate_gateway_start_report.json` | `STARTED`, candidate health `ok`, non-live port |
| Option-B runner plan | `reports/benchmark/phase_24HR_option_B_candidate_gateway_runner_plan.md` | ready |
| Option-B guard smoke | `reports/benchmark/phase_24HR_option_B_candidate_gateway_guard_smoke.md` | `PASS`, 5/5 |
| Live runtime boundary | `http://127.0.0.1:8000/v1/health` | remains benchmark-only; no switch |

## Guarded Run Command
Run only after explicit option-C approval and after option-B candidate gateway health is verified:

```bash
python3 scripts/benchmark/phase24hr_option_c_targeted_smoke.py run-smoke \
  --execute --authorization-token OPTION_C_APPROVED_PHASE24HR
```

## Expected Candidate Command
The guarded runner calls the public benchmark runner only after the checks above pass:

```bash
python3 scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8010/v1 \
  --model hukuk-ai-poc \
  --out-dir reports/benchmark/runs/phase_24HR_option_C_targeted_candidate_smoke \
  --qids TEB-04 TUZUK-05 KANUN-08 YON-05
```

Then it scores:

```bash
python3 scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/phase_24HR_option_C_targeted_candidate_smoke/candidate_answers.csv \
  --out-dir reports/benchmark/runs/phase_24HR_option_C_targeted_candidate_smoke/score
```

## Stop Conditions
Stop and report without running smoke if any condition occurs:

- Option-B start report is missing or not `STARTED`.
- Candidate health is not `ok`.
- API URL points to live `8000`.
- Candidate requires public bind address or external exposure.
- Candidate requires model, prompt, top-k, Open WebUI, or live route change.
- Any `answer_contract_invalid_count > 0`.
- Any `unsupported_confident_answer_count > 0`.
- `TEB-04` loses `19631` / KDV Genel Uygulama Tebliği as source.
- `TUZUK-05` selects a concrete irrelevant tüzük as primary source.

## Boundary To Option D
Option `C` did not authorize a full benchmark. Option `D` must not be requested from this state because targeted smoke failed.
