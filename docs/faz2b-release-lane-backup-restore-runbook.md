# FAZ 2B Release Lane Backup / Restore Runbook

## Purpose
- Provide a bounded, repeatable backup / restore path for the release lane configuration surface.
- Scope is lane config and launch surface, not a full Milvus data export.

## Supervision Check

### Candidate lane example
```bash
python3 scripts/faz2b/ensure_release_lane.py \
  --launch-script scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh \
  --gateway-pid-path runtime_logs/candidate_gateway_dgx1_merged.pid \
  --tunnel-pid-path runtime_logs/dgx1_merged_vllm_tunnel.pid \
  --health-url http://127.0.0.1:8004/v1/health \
  --metrics-url http://127.0.0.1:8004/v1/metrics \
  --audit-log-path runtime_logs/api_audit.jsonl \
  --api-key "$API_KEY" \
  --restart
```

### Baseline lane example
```bash
python3 scripts/faz2b/ensure_release_lane.py \
  --launch-script scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh \
  --gateway-pid-path runtime_logs/baseline_gateway_dgxnode2.pid \
  --tunnel-pid-path runtime_logs/baseline_dgxnode2_vllm_tunnel.pid \
  --health-url http://127.0.0.1:8000/v1/health \
  --metrics-url http://127.0.0.1:8000/v1/metrics \
  --audit-log-path runtime_logs/api_audit.jsonl \
  --api-key "$API_KEY" \
  --restart
```

## Backup Bundle
- Capture the release-lane env contract plus the launch/proof scripts that define the lane.

```bash
python3 scripts/faz2b/backup_release_state.py \
  --output-dir /tmp/faz2b_release_backup_drill \
  --label dgx1_candidate_release_lane \
  --env-key API_AUTH_ENABLED \
  --env-key AUDIT_LOG_ENABLED \
  --env-key SESSION_STORE_BACKEND \
  --env-key MILVUS_COLLECTION \
  --include-path scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh \
  --include-path scripts/faz2b/ensure_release_lane.py
```

## Restore Bundle
- Rebuild a shell-exportable env file and verify copied bundle files exist.

```bash
python3 scripts/faz2b/restore_release_state.py \
  --manifest-path /tmp/faz2b_release_backup_drill/<bundle>/manifest.json \
  --restore-dir /tmp/faz2b_release_backup_drill/restore
```

Expected restore outputs:
- `restore.env.sh`
- `restore_summary.json`

## Minimum Release Bundle
- Auth / audit / session env keys
- lane launch script
- supervision script
- Milvus collection reference

## Known Boundary
- This runbook does not create a full Milvus snapshot.
- It closes the repo-native bounded restore proof for lane configuration and dependency wiring.
- Full vector-store export remains an infrastructure operation outside this repo.
