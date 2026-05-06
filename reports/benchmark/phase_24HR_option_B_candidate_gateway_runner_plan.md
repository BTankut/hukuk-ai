# Phase 24HR Option B Candidate Gateway Runner Plan

- generated_at_utc: `2026-05-06T16:23:32.591246+00:00`
- status: `READY_FOR_OPTION_B_AUTHORIZATION`
- host: `127.0.0.1`
- port: `8010`
- lane: `phase24hr_option_b_candidate`
- collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr`
- authorization_token_required: `OPTION_B_APPROVED_PHASE24HR`
- live_8000_modified: `false`
- candidate_gateway_started: `false`
- model_inference_called: `false`
- chat_completions_called: `false`

## Guarded Start Command

```bash
python3 scripts/benchmark/phase24hr_option_b_candidate_gateway.py start-candidate \
  --execute --authorization-token OPTION_B_APPROVED_PHASE24HR
```

## Safety Notes

- Without `--execute`, the runner refuses to start a process.
- Without `--authorization-token OPTION_B_APPROVED_PHASE24HR`, the runner refuses to start a process.
- The candidate host must be loopback only.
- Port `8000` is refused.
- The runner calls health endpoints only after an authorized start; it does not call chat completions.
