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
| Freeze Gate | Partial pass | Freeze dataset, runner, manifest, and metric code for `faz1-50`, `v2-95`, `v3-170` | None | No explicit freeze artefact for all three eval families in one place |
| Eval Integrity Gate | Partial pass | Produce matched baseline and candidate artefacts with the same runner family, same dataset version, same metric code | None | No matched baseline/candidate pair yet for `v2-95` and `v3-170` |
| Model Qualification Gate | Partial pass | Run baseline and promoted candidate on `faz1-50`, `v2-95`, `v3-170` and publish category breakdowns | Broad release/cutover | No post-train matched reports for `v2-95` and `v3-170` |
| Release Readiness Gate | Open | Close operational blockers: auth, audit logging, PII masking proof, Redis session store, token accounting, observability, alerting, rollback, keepalive, backup/restore | DGX-native productization, new UI, broad Phase 2 feature work | No direct repo evidence that release controls are validated end-to-end |
| Steering Decision Gate | Open | Publish a single decision package: GO, Narrow GO, or NO-GO with evidence | Production cutover until gates above are closed | No decision package yet for FAZ 1.5 |

## Work Package Matrix

| WP | Current Status | Must-Close | Defer | Missing Evidence |
| --- | --- | --- | --- | --- |
| WP-1 Eval Freeze and Reproducibility | Partial | Lock all question-set versions, runner parity, manifest contract, and metric code hash | None | No single artefact that freezes all 3 eval families together |
| WP-2 Full-Family Matched Eval | Not done | Run matched baseline and candidate on `faz1-50`, `v2-95`, `v3-170` | None | Only `faz1-50` has an accepted promoted-candidate record |
| WP-3 Error Taxonomy and Root Cause Split | Not done as a formal artefact | Classify failures into retrieval miss, wrong source, cross-law confusion, unsupported answer, refusal miss, missing coverage, infra error | None | No formal taxonomy report in `coordination/` yet |
| WP-4 Train Data Lineage Audit | Partial | Explain the `1076 -> 807` reduction with explicit buckets and separation proof | None | The explanation exists across docs, but no standalone lineage audit file yet |
| WP-5 Production Readiness Matrix | Being created now | Capture must-close vs defer for auth, audit logging, PII, Redis, token accounting, observability, alerting, versioning, keepalive, backup/restore | DGX appliance packaging | No validated release-control implementation evidence for several items |
| WP-6 Topology Contract and Cutover Rehearsal | Not done | Define internal/pilot vs customer-appliance topology and execute at least one rollback rehearsal | Customer appliance bundle | No rollback rehearsal evidence in current repo state |
| WP-7 Scope Contract | Not done as a formal contract file | State supported laws, unsupported areas, refusal behavior, and unsupported feature claims | None | No standalone scope contract existed before this artefact |
| WP-8 Final Decision Package | Blocked | Select one final outcome only after gates 1 to 7 close | Production cutover / narrow GO until evidence is complete | No full-family evidence package to support a final cutover decision |

## What Is Already Evidenced

- The promoted `dgx1` lane has a clean post-promotion cleanup run.
- `faz1-50` has a valid matched post-train report and evidence manifest.
- `final_train.jsonl` is frozen as the canonical active package with `807` unique questions.
- The repo has explicit readiness-gate logic for baseline, post-train, and promotion evidence.

## What Still Blocks Cutover

- No matched post-train evidence yet for `v2-95`.
- No matched post-train evidence yet for `v3-170`.
- No formal rollback rehearsal record.
- No validated release-control matrix for auth, audit logging, Redis, token accounting, observability, alerting, or backup/restore.
- No single decision package that can honestly say cutover is approved.

## Decision Implication

FAZ 1.5 should continue as a **decision gate**, not as a feature wave.

At the current repo state, the most defensible stance is:

- `NO-GO` for production cutover
- `Narrow GO` remains possible only if the missing matched evals and release-control proof are completed

