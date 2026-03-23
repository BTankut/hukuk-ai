# FAZ 2B Wave 3 — supervision and bounded restore proof

## Scope
- Objective: close the remaining repo-native operational proof gaps before steering refresh.
- Covered:
  - release-lane supervision / restart decision surface
  - bounded backup / restore proof for lane config and launch surface

## Implemented artefacts
- Supervision helper:
  - `scripts/faz2b/ensure_release_lane.py`
- Backup helper:
  - `scripts/faz2b/backup_release_state.py`
- Restore helper:
  - `scripts/faz2b/restore_release_state.py`
- Bounded proof tests:
  - `tests/test_faz2b_release_ops.py`
- Runbook:
  - `docs/faz2b-release-lane-backup-restore-runbook.md`

## Verification
- `python3 -m py_compile` passed for:
  - `scripts/faz2b/ensure_release_lane.py`
  - `scripts/faz2b/backup_release_state.py`
  - `scripts/faz2b/restore_release_state.py`
- `pytest tests/test_faz2b_release_ops.py -q` passed (`3 passed`)

## Bounded proof runs

### 1) Supervision dry-run
Command:
```bash
python3 scripts/faz2b/ensure_release_lane.py \
  --launch-script scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh \
  --gateway-pid-path /tmp/faz2b_fake_gateway.pid \
  --tunnel-pid-path /tmp/faz2b_fake_tunnel.pid \
  --health-url http://127.0.0.1:9/v1/health \
  --metrics-url http://127.0.0.1:9/v1/metrics \
  --audit-log-path /tmp/faz2b_fake_audit.jsonl \
  --restart \
  --dry-run
```

Observed result:
- `restart_requested=true`
- expected failure classes surfaced:
  - `gateway_pid_not_running`
  - `tunnel_pid_not_running`
  - `health_failed`
  - `metrics_failed`
  - `audit_log_missing`

### 2) Backup / restore drill
Backup manifest:
- `/tmp/faz2b_release_backup_drill/dgx1_candidate_release_lane_20260323T074137Z/manifest.json`

Restore summary:
- `/tmp/faz2b_release_backup_drill/restore/restore_summary.json`

Observed result:
- env keys captured:
  - `API_AUTH_ENABLED=true`
  - `AUDIT_LOG_ENABLED=true`
  - `SESSION_STORE_BACKEND=redis`
  - `MILVUS_COLLECTION=mevzuat_e5_shadow`
- copied lane files existed at restore time and matched recorded sha256
- `restore.env.sh` rendered successfully

## Decision
- Wave 3 closes these FAZ 2B must-close items at repo-native proof level:
  - keepalive / supervision proof
  - bounded backup / restore proof
- FAZ 2B remains open only for the refreshed steering package that will decide cutover readiness.

## Next active target
- Refresh the FAZ 2B steering package:
  - closure matrix
  - decision table
  - cutover-readiness recommendation
