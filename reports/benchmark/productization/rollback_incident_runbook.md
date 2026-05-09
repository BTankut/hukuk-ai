# Rollback And Incident Runbook

## Scope
This runbook defines the minimum rollback and incident response requirements before any serving-candidate or productization cutover.

## Current Live Baseline
| field | observed value |
|---|---|
| endpoint | `http://127.0.0.1:8000/v1` |
| health status | `ok` |
| lane | `phase22f_s7_full_shadow` |
| api version | `2026-05-03-phase23R-E-benchmark-only-cutover` |
| retriever | `milvus` |
| guardrails | `disabled` |
| verification | `disabled` |

## Pre-Cutover Requirements
- Capture current health response.
- Capture model ID, retrieval collection ID, environment file path, and deployed git commit.
- Capture candidate configuration separately from current live configuration.
- Verify rollback ownership and communication path.
- Run non-live smoke before any live switch.

## Rollback Procedure
1. Stop candidate traffic using the approved deployment mechanism.
2. Restore the previously captured live configuration.
3. Restart only the affected service using the approved service manager.
4. Check health with `curl -sS http://127.0.0.1:8000/v1/health`.
5. Run a small smoke set covering contract validity, unsupported confident answer blocking, source-key collision checks, and one known residual blocker.
6. Record incident summary, rollback time, final health, and follow-up owner.

## Incident Severity
| severity | trigger |
|---|---|
| P0 | Wrong legal source confidently served to users or public endpoint. |
| P1 | Contract invalid, unsupported confident answer, or source-key collision in candidate. |
| P2 | Benchmark regression or trace/audit gap before public exposure. |
| P3 | Documentation or review-packet inconsistency. |

## Current State
- This runbook is documentation only and has not been operationally rehearsed.
- Serving candidate and productization remain blocked until rollback is rehearsed and signed off.
- No live runtime change was made by this runbook artifact.

