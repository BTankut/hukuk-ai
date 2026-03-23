# FAZ 2C Controlled Cutover Runbook

## Purpose
- Execute the FAZ 2B `NARROW GO` decision as a controlled internal cutover or dar kapsam pilot.
- Keep the preserved baseline as an immediate rollback target.

## Approved Scope
- Approved:
  - DGX-native internal cutover
  - dar kapsam pilot
  - preserved baseline rollback
- Not approved:
  - broad public production rollout
  - customer-appliance shipment
  - claims beyond bounded restore proof

## Preconditions
- baseline lane healthy at `127.0.0.1:8000`
- candidate lane healthy at `127.0.0.1:8004`
- `GET /v1/metrics` reachable on both lanes
- audit logging enabled
- operator has `API_KEY` if auth is enabled
- baseline rollback scripts still available

## Cutover Command

```bash
API_KEY=<key> \
bash scripts/faz2c/run_controlled_cutover.sh
```

What it does:
- preflights baseline and candidate with `ensure_release_lane.py`
- runs cited smoke on both lanes
- creates a bounded backup bundle
- stops baseline lane on `8000`
- launches candidate alias on `8000`
- verifies health, metrics, and cited smoke on the alias
- writes `runtime_logs/faz2c_controlled_cutover_summary.json`

## Rollback Command

```bash
API_KEY=<key> \
bash scripts/faz2c/run_controlled_rollback.sh
```

What it does:
- stops the candidate alias on `8000`
- relaunches preserved baseline
- verifies health, metrics, and cited smoke
- writes `runtime_logs/faz2c_controlled_rollback_summary.json`

## Dry Run

```bash
bash scripts/faz2c/run_controlled_cutover.sh --dry-run
bash scripts/faz2c/run_controlled_rollback.sh --dry-run
```

## Immediate Rollback Triggers
- `/v1/health` fails on the alias lane
- `/v1/metrics` is unavailable after cutover
- cited smoke no longer returns `TBK m.49`
- operator sees lane-health degradation or unexpected refusal/blocking behavior

## Expected Artifacts
- cutover summary:
  - `runtime_logs/faz2c_controlled_cutover_summary.json`
- rollback summary:
  - `runtime_logs/faz2c_controlled_rollback_summary.json`
- bounded backup manifest:
  - under `/tmp/faz2c_controlled_cutover_backup/`

## Known Boundary
- This runbook packages the controlled DGX-native cutover path.
- It does not expand the decision into broad production or customer-appliance scope.
