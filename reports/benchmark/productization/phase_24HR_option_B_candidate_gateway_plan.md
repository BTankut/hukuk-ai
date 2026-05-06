# Phase 24HR Option B Candidate Gateway Plan

Generated: 2026-05-06

## Scope
This is a non-executing plan for option `B` in `phase_24HR_shadow_validation_authorization_packet.md`.

Option `B` means starting a **non-live candidate gateway** on a separate loopback port that points to the verified Phase 24HR shadow collection:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr
```

This plan does not authorize or perform:

- Live `8000` cutover.
- Internal eval opening.
- Serving-candidate opening.
- Productization or public serving.
- Open WebUI backend switch.
- Model, prompt, top-k, or fine-tuning change.
- Targeted trace-on smoke or full benchmark execution.

## Execution Status
Option `B` was approved by the owner and executed on 2026-05-06.

Evidence:

- Start report: `reports/benchmark/phase_24HR_option_B_candidate_gateway_start_report.md`
- Candidate health: `status=ok`, lane `phase24hr_option_b_candidate`, host `127.0.0.1`, port `8010`
- Live `8000`: unchanged
- Chat/model inference: not called

## Current Prerequisites
| prerequisite | evidence | required state |
|---|---|---|
| Option-A shadow build/load | `reports/benchmark/phase_24HR_shadow_collection_build_report.md` | `PASS`, target `349462`, delta `59` |
| Option-A read-only verification | `reports/benchmark/phase_24HR_shadow_collection_verify.md` | `PASS`, `59/59` delta rows, base collision `0`, load state `Loaded` |
| Phase 24HR preflight | `reports/benchmark/phase_24HR_shadow_validation_preflight.md` | `PASS`, `49/49` |
| Live runtime boundary | `http://127.0.0.1:8000/v1/health` | remains benchmark-only; no switch |

## Proposed Candidate Boundary
| item | value |
|---|---|
| Candidate port | `8010` |
| Candidate bind address | `127.0.0.1` only |
| Candidate lane | `phase24hr_option_b_candidate` |
| Candidate API version | `2026-05-06-phase24hr-option-b-candidate` |
| Candidate collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr` |
| Candidate log | `runtime_logs/phase24hr/option_b_candidate_gateway.log` |
| Candidate pid file | `runtime_logs/phase24hr/option_b_candidate_gateway.pid` |
| Live port | `8000`, must remain unchanged |

## Pre-Start Checks
Run only after explicit option-B approval:

```bash
curl -sS --max-time 5 http://127.0.0.1:8000/v1/health
python3 scripts/benchmark/phase24hr_shadow_preflight.py
api-gateway/.venv/bin/python scripts/benchmark/phase24hr_shadow_collection_verify.py
lsof -nP -iTCP:8010 -sTCP:LISTEN
```

Expected:

- Live `8000` health responds and remains the current benchmark-only lane.
- Preflight is `PASS`.
- Shadow collection verify is `PASS`.
- Port `8010` is free. If `lsof` returns a listener, stop and report instead of reusing the port.

## Candidate Start Command
Run only after explicit option-B approval:

Preferred guarded runner:

```bash
python3 scripts/benchmark/phase24hr_option_b_candidate_gateway.py start-candidate \
  --execute --authorization-token OPTION_B_APPROVED_PHASE24HR
```

Equivalent expanded command used by the runner:

```bash
mkdir -p runtime_logs/phase24hr

env \
  PYTHONPATH=api-gateway/src \
  RELEASE_LANE_ID=phase24hr_option_b_candidate \
  API_VERSION_LABEL=2026-05-06-phase24hr-option-b-candidate \
  MILVUS_ENABLED=true \
  MILVUS_URI=http://localhost:19530 \
  MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr \
  EMBEDDING_BACKEND=remote \
  EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
  EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
  EMBEDDING_DIM=1024 \
  DGX_BASE_URL=http://192.168.12.243:30000/v1 \
  DGX_MODEL=/models/merged_model_fabric_stage_20260321 \
  GUARDRAILS_ENABLED=false \
  PRESIDIO_ENABLED=false \
  USE_VERIFICATION=false \
  API_AUTH_ENABLED=false \
  AUDIT_LOG_ENABLED=false \
  TRACE_LOG_DIR=logs/traces/phase24hr_option_b_candidate \
  api-gateway/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8010 \
  > runtime_logs/phase24hr/option_b_candidate_gateway.log 2>&1 &

echo "$!" > runtime_logs/phase24hr/option_b_candidate_gateway.pid
```

## Post-Start Health Checks
These are option-B checks and should not call `/v1/chat/completions`:

```bash
curl -sS --max-time 5 http://127.0.0.1:8010/v1/health
curl -sS --max-time 5 http://127.0.0.1:8000/v1/health
```

Expected:

- Candidate `8010` health returns `status=ok`, lane `phase24hr_option_b_candidate`, retriever `milvus`.
- Live `8000` health is unchanged.
- No chat/model inference is called under option `B`.

## Stop Command
Use this if any health check fails, if live `8000` changes, or after option-B inspection is complete:

```bash
if [ -f runtime_logs/phase24hr/option_b_candidate_gateway.pid ]; then
  kill "$(cat runtime_logs/phase24hr/option_b_candidate_gateway.pid)"
fi
```

## Hard Stop Conditions
Stop and report without running targeted smoke or benchmark if any condition occurs:

- Candidate cannot start on `127.0.0.1:8010`.
- Candidate health is not `status=ok`.
- Candidate retriever is not `milvus`.
- Live `8000` health changes.
- Candidate requires a model, prompt, top-k, Open WebUI, or live route change.
- Candidate requires public bind address or external exposure.
- Candidate requires internal eval, serving-candidate, productization, or fine-tuning opening.

## Boundary To Options C/D
Option `B` ends after candidate health checks. It does not authorize question answering, targeted smoke, trace-on benchmark, or scorer execution.

The next explicit approvals are:

- Option `C`: targeted trace-on candidate smoke for `TEB-04`, `TUZUK-05`, and source-identity guard rows.
- Option `D`: full trace-on candidate benchmark, only after targeted smoke passes.

## Guard Evidence
The fail-closed runner is `scripts/benchmark/phase24hr_option_b_candidate_gateway.py`.

The no-authorization guard smoke is `reports/benchmark/phase_24HR_option_B_candidate_gateway_guard_smoke.md`.
