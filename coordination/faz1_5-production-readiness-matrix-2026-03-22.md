# FAZ 1.5 Production Readiness Matrix

**Date:** 2026-03-22  
**Basis:** `docs/FAZ1_5-PLANLAMA-2026-03-22.md` + current repo artefacts

This matrix is a snapshot of what is already evidenced in the repo, what is still missing, and which items are must-close versus defer for FAZ 1.5.

## Executive Position

Current state is **not cutover-ready**.

The promoted `dgx1` lane has a valid post-train promotion record for `faz1-50`, but FAZ 1.5 requires full-family matched eval, lineage audit, readiness gating, topology rehearsal, and scope contract closure before any production cutover can be considered.

## Gate Matrix

| Gate / Heading | Current Status | Must-Close | Defer | Missing Evidence |
| --- | --- | --- | --- | --- |
| Freeze Gate | Closed | Keep frozen dataset, runner, manifest, and metric code for `faz1-50`, `v2-95`, `v3-170` unchanged | None | None while freeze stays intact |
| Eval Integrity Gate | Partial pass | Produce the remaining matched baseline and candidate artefacts with the same runner family, same dataset version, same metric code | None | `v3-170` matched closure is still open |
| Model Qualification Gate | Partial pass | Publish the full-family results table and category breakdowns for `faz1-50`, `v2-95`, `v3-170` | Broad release/cutover | `v3-170` source-of-record reports and taxonomy are still open |
| Release Readiness Gate | Open | Close operational blockers: auth, audit logging, PII masking proof, Redis session store, token accounting, observability, alerting, rollback, keepalive, backup/restore | DGX-native productization, new UI, broad Phase 2 feature work | No direct repo evidence that release controls are validated end-to-end |
| Steering Decision Gate | Open | Publish a single decision package: GO, Narrow GO, or NO-GO with evidence | Production cutover until gates above are closed | No final FAZ 1.5 steering package yet |

## Work Package Matrix

| WP | Current Status | Must-Close | Defer | Missing Evidence |
| --- | --- | --- | --- | --- |
| WP-1 Eval Freeze and Reproducibility | Closed | Preserve question-set versions, runner parity, manifest contract, and metric code hash | None | None while freeze stays unchanged |
| WP-2 Full-Family Matched Eval | In progress | Close the remaining matched `v3-170` baseline and candidate reports/manifests | None | `v3-170` source-of-record closure is still missing |
| WP-3 Error Taxonomy and Root Cause Split | Open as a formal artefact | Classify failures into retrieval miss, wrong source, cross-law confusion, unsupported answer, refusal miss, missing coverage, infra error | None | No formal taxonomy report in `coordination/` yet |
| WP-4 Train Data Lineage Audit | Closed | Keep the `1076 -> 807` explanation and separation proof as the canonical lineage record | None | None for FAZ 1.5 closure |
| WP-5 Production Readiness Matrix | Partial | Capture must-close vs defer for auth, audit logging, PII, Redis, token accounting, observability, alerting, versioning, keepalive, backup/restore | DGX appliance packaging | No validated release-control implementation evidence for several items |
| WP-6 Topology Contract and Cutover Rehearsal | Partial | Define internal/pilot vs customer-appliance topology and execute at least one rollback rehearsal | Customer appliance bundle | No successful rollback rehearsal record yet |
| WP-7 Scope Contract | Closed | Preserve supported laws, unsupported areas, refusal behavior, and unsupported feature claims | None | None for FAZ 1.5 closure |
| WP-8 Final Decision Package | Open | Select one final outcome only after gates 1 to 7 close | Production cutover / narrow GO until evidence is complete | No full-family evidence package to support a final cutover decision |

## What Is Already Evidenced

- The promoted `dgx1` lane has a clean post-promotion cleanup run.
- `faz1-50` has a valid matched post-train report and evidence manifest.
- `v2-95` baseline rerun was reset and re-closed under the official `dgxnode2_base_thinkingoff_r2_20260322` source-of-record label.
- `final_train.jsonl` is frozen as the canonical active package with `807` unique questions.
- The repo has explicit readiness-gate logic for baseline, post-train, and promotion evidence.

## What Still Blocks Cutover

- `v3-170` baseline and candidate source-of-record artefacts are still open.
- No formal taxonomy / root-cause report yet for the full family results.
- No formal rollback rehearsal record.
- No validated release-control matrix for auth, audit logging, Redis, token accounting, observability, alerting, or backup/restore.
- No single decision package that can honestly say cutover is approved.

## Release Controls Table

| Control | Current State | Risk | Must-Close / Defer | Owner | Test Method | Evidence | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Auth | Main legal API does not enforce request auth | High | Must-close | API | Protected endpoint smoke against gateway | [main.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/main.py), [embedding.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/rag/embedding.py) | Missing |
| Audit logging | Session-scoped runtime logs exist, immutable audit trail does not | High | Must-close | API / Ops | Emit-and-retrieve audit event proof | [chat.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/routers/chat.py) | Partial |
| PII masking | Guardrails + Presidio integration exists but release-proof is not frozen | Medium | Must-close | Guardrails | Masking smoke with cited legal request and PII payload | [actions.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/guardrails/actions.py), [config.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/config.py) | Partial |
| Redis session store | Sessions remain in-memory only | Medium | Must-close | API / Infra | Persistence restart proof | [chat.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/routers/chat.py) | Missing |
| Token accounting | `usage` is approximate; production tokenizer accounting is not implemented | Medium | Must-close | API | Compare response usage against tokenizer-backed counter | [chat.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/routers/chat.py), [token_manager.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/rag/token_manager.py) | Partial |
| Observability | Health endpoints and runtime logs exist; no metrics pipeline evidence | Medium | Must-close | Ops | Metrics scrape or operator dashboard proof | [main.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/main.py) | Partial |
| Alerting | No repo-native alerting integration | Medium | Must-close | Ops | Simulated lane failure alert proof | current repo state | Missing |
| API versioning | `/v1` only | Low | Defer | API | Versioned route contract test | [main.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/main.py) | Missing |
| Keepalive / supervision | Detached launcher tools exist but not full service supervision | Medium | Must-close | Ops | Kill-and-recover process proof | [detach_logged_job.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/finetune/detach_logged_job.py), [dgx-vllm-ensure-running.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/dgx-vllm-ensure-running.sh) | Partial |
| Backup / restore | No formal backup/restore runbook or restore evidence | Medium | Must-close | Ops / Data | Restore drill for vector store plus lane config | current repo state | Missing |
| Smoke checks | Health and cited smoke paths exist | Low | Must-close | Ops | Health + cited query smoke on both lanes | [runtime-bringup-recovery-2026-03-20.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/runtime-bringup-recovery-2026-03-20.md), [dgx1-merged-endpoint-bridge-2026-03-21.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/dgx1-merged-endpoint-bridge-2026-03-21.md) | Present |
| Rollback plan | Procedure exists and has now been proven in rehearsal | High | Must-close | Ops | Successful cutover plus rollback rehearsal | [run_cutover_rehearsal.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz1_5/run_cutover_rehearsal.sh), [faz1_5-cutover-rehearsal-2026-03-22.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz1_5-cutover-rehearsal-2026-03-22.md) | Present |
| Guardrails latency budget | Guardrails are enabled, but no formal FAZ 1.5 latency budget acceptance row exists | Medium | Must-close | Guardrails / Ops | Timed smoke under promoted lane with guardrails on | [guardrails-safe-default-decision-2026-03-20.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/guardrails-safe-default-decision-2026-03-20.md) | Partial |

## Decision Implication

FAZ 1.5 should be treated as a **closed decision gate**, not as a feature wave.

At the current repo state, the most defensible stance is:

- `NO-GO - Retrieval/Coverage first`
- release-control closure remains necessary, but it is not the primary steering blocker
