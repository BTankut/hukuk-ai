# Phase 24HR Option C Targeted Smoke Runner Plan

- generated_at_utc: `2026-05-06T16:32:40.855929+00:00`
- status: `BLOCKED_WAITING_FOR_OPTION_B`
- api_url: `http://127.0.0.1:8010/v1`
- model: `hukuk-ai-poc`
- target_qids: `TEB-04 TUZUK-05 KANUN-08 YON-05`
- option_b_status: `MISSING`
- live_8000_modified: `false`
- candidate_gateway_started: `false`
- model_inference_called: `false`
- chat_completions_called: `false`

## Guarded Run Command

```bash
python3 scripts/benchmark/phase24hr_option_c_targeted_smoke.py run-smoke \
  --execute --authorization-token OPTION_C_APPROVED_PHASE24HR
```

## Safety Notes

- Without option-B candidate health evidence, the runner remains blocked.
- Without `--execute`, the runner refuses to call the candidate gateway.
- Without `--authorization-token OPTION_C_APPROVED_PHASE24HR`, the runner refuses to call the candidate gateway.
- API URL using live `8000` is refused.
