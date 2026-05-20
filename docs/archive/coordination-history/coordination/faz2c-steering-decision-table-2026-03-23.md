# FAZ 2C Steering Decision Table

**Date:** 2026-03-23  
**Basis:** `coordination/faz2c-implementation-plan-2026-03-23.md` + live FAZ 2C artefacts

## 1) Decision Options

| Option | Decision meaning | Gate basis | Required evidence | Status |
| --- | --- | --- | --- | --- |
| `STAY ON PROMOTED LANE` | Controlled cutover remains active under narrow-pilot boundary | Live cutover succeeds, rollback stays ready, narrow-pilot snapshot stays clean | cutover summary, rollback surface, clean monitoring snapshot, no immediate rollback trigger | selected |
| `ROLLBACK NOW` | Immediate restore to preserved baseline | Alias lane health, metrics, cited smoke, or live response shape fails | rollback trigger row or operator-observed degradation | rejected |
| `PAUSE AT PACKAGE ONLY` | Scripts/runbooks exist but live lane should not stay cut over | FAZ 2C packaging closes but live evidence does not justify active cutover | package-only proof without clean live monitoring | superseded |
| `GO - Broad Production` | Widen approval beyond narrow pilot | Broader production / productization depth closes | broad rollout, external monitoring depth, productization evidence | rejected |

## 2) Required Evidence Checklist

| Item | Source-of-record placeholder | Status |
| --- | --- | --- |
| Controlled cutover package | [faz2c-wave1-cutover-package-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2c-wave1-cutover-package-2026-03-23.md) | closed |
| Live cutover execution summary | [faz2c-live-cutover-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2c-live-cutover-2026-03-23.md) | closed |
| Rollback command surface | [run_controlled_rollback.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz2c/run_controlled_rollback.sh) | closed |
| Narrow pilot monitoring package | [faz2c-wave2-narrow-pilot-monitoring-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2c-wave2-narrow-pilot-monitoring-2026-03-23.md) | closed |
| Clean live response normalization | [test_guardrails_pipeline_smoke.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/tests/test_guardrails_pipeline_smoke.py), [faz2c-wave2-narrow-pilot-monitoring-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2c-wave2-narrow-pilot-monitoring-2026-03-23.md) | closed |
| Final execution-state package | [FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md) | closed |

## 3) Official Decision

Official decision: **`Controlled cutover active -> stay on promoted lane under narrow-pilot boundary.`**

Reason:

- FAZ 2B already approved only a `NARROW GO`, not broad production
- FAZ 2C converted that steering decision into a real live cutover with explicit rollback
- the refreshed narrow-pilot snapshot on live `8000` is clean:
  - `rollback_recommended = false`
  - health `ok`
  - cited smoke `pass`
  - audit/upstream/chat counters advance
  - `refusal_delta = 0`
- preserved baseline rollback remains the immediate safety path

Boundary:

- this is not broad public production approval
- this is not productization approval
- this is an execution-state decision for the DGX-native narrow pilot lane
