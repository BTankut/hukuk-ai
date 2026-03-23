# FAZ 2C Live Controlled Cutover

**Date:** 2026-03-23  
**Basis:** `docs/faz2c-controlled-cutover-runbook.md`, `scripts/faz2c/run_controlled_cutover.sh`

## Result

Controlled cutover completed successfully.

The live `8000` lane now points to the promoted `dgx1` merged candidate alias.

## Observed sequence

1. Baseline lane preflight passed.
2. Candidate lane preflight passed.
3. Baseline cited smoke passed.
4. Candidate cited smoke passed.
5. Bounded backup bundle was created:
   - `/tmp/faz2c_controlled_cutover_backup/dgx1_candidate_controlled_cutover_20260323T080925Z/manifest.json`
6. Baseline lane on `8000` was stopped.
7. Candidate alias was launched on `8000`.
8. Post-cutover alias health, metrics, and cited smoke all passed.

## Live state after cutover

| Surface | Result |
| --- | --- |
| `GET /v1/health` on `127.0.0.1:8000` | pass |
| `GET /v1/metrics` on `127.0.0.1:8000` | pass |
| `POST /v1/chat/completions` cited smoke | pass |
| Audit event counter | `hukuk_ai_audit_events_total = 1` |
| Usage source counter | `hukuk_ai_usage_source_total{source="upstream"} = 1` |

## Source artifacts

- cutover summary:
  - `runtime_logs/faz2c_controlled_cutover_summary.json`
- audit log:
  - `runtime_logs/api_audit.jsonl`
- rollback command:
  - `bash scripts/faz2c/run_controlled_rollback.sh`

## Steering read

- FAZ 2B `NARROW GO` is now exercised as a real live cutover, not only a packaged command surface.
- Broad production is still not approved.
- Preserved baseline rollback remains the immediate safety path.
