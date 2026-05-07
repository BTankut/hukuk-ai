# Phase 24HR Option C Targeted Smoke Guard Smoke

- generated_at_utc: `2026-05-07T04:18:12.745457+00:00`
- status: `PASS`
- row_count: `5`
- pass_count: `5`
- fail_count: `0`
- live_8000_modified: `false`
- candidate_gateway_started: `false`
- model_inference_called: `false`
- chat_completions_called: `false`

| case | status | observed_status | observed_error |
|---|---|---|---|
| `plan_local_only` | `PASS` | `READY_FOR_OPTION_C_AUTHORIZATION` |  |
| `run_without_execute_refused` | `PASS` | `REFUSED` | Refusing targeted smoke: pass --execute only after owner option-C authorization. |
| `run_without_token_refused` | `PASS` | `REFUSED` | Refusing targeted smoke: missing or invalid option-C authorization token. |
| `run_live_8000_refused_before_candidate` | `PASS` | `REFUSED` | Refusing targeted smoke: live 8000 must not be used. |
| `run_candidate_port_mismatch_refused_before_chat` | `PASS` | `REFUSED` | Refusing targeted smoke: api-url port does not match the option-B candidate port. |

## Decision

- Guard smoke is safe to run without option-C authorization.
- It verifies fail-closed behavior only; it does not call the candidate gateway, chat completions, or model.
