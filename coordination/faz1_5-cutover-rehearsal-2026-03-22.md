# FAZ 1.5 Cutover Rehearsal

**Date:** 2026-03-22  
**Basis:** `docs/FAZ1_5-PLANLAMA-2026-03-22.md`, current `main`, and existing repo artefacts

## Purpose

This document captures the current cutover rehearsal posture for FAZ 1.5. It is not a production cutover approval. It records the operational lanes, the rollback path, and the evidence that currently exists in the repo.

## Current Topology Snapshot

| Lane | Local Alias | Upstream | Model / Checkpoint | Status |
| --- | --- | --- | --- | --- |
| Baseline | `http://127.0.0.1:8000` | `dgxnode2` via SSH tunnel | `Qwen/Qwen3.5-35B-A3B-FP8` / `dgxnode2-base-runtime-20260322` | Ready for matched comparison |
| Promoted candidate | `http://127.0.0.1:8004` | `dgx1` merged via SSH tunnel | `hukuk-ai-sft-qwen35-807` / `dgx1-merged-post-promotion-cleanup-20260322` | Ready for matched comparison |
| Shared support | `http://127.0.0.1:8081` | Local embedding service | Embedding service | Healthy |
| Shared support | `http://127.0.0.1:19530` | Milvus | Vector store | Healthy |

## Rehearsal Design

The rehearsal pattern is:

1. Bring up the baseline lane through `scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh`.
2. Bring up the promoted candidate lane through `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh`.
3. Validate both lanes with the same family runner wrapper:
   `scripts/faz1_5/run_matched_eval_family.sh`
4. Flip the local alias between the two lanes.
5. Execute a rollback to the previous lane and re-run smoke checks.

The repo-native rehearsal procedure is now captured in:

- `scripts/faz1_5/run_cutover_rehearsal.sh`

The rehearsal is considered successful only if the rollback restores the previous lane without breaking health checks or citation-grounded smoke responses.

## What Is Already Evidenced

- Eval freeze exists: `coordination/faz1_5-eval-freeze-2026-03-22.md`
- Readiness matrix exists: `coordination/faz1_5-production-readiness-matrix-2026-03-22.md`
- Scope contract exists: `coordination/faz1_5-scope-contract-2026-03-22.md`
- Training lineage audit exists: `training/audits/faz1_5-train-lineage-audit-2026-03-22.md`
- The promoted candidate has already passed a closed `faz1-50` post-train cleanup run with `88.0%` citation and `86.0%` correct source.

## Current Status At Draft Time

| Item | Status | Note |
| --- | --- | --- |
| Baseline lane smoke | Ready | `8000` lane is available for comparison |
| Candidate lane smoke | Ready | `8004` lane is available for comparison |
| Rollback path | Ready | Alias can be switched back to baseline lane |
| Full-family matched eval | In progress | Baseline and candidate family runs are still the decision source of record |
| Repo-native rehearsal script | Ready | `scripts/faz1_5/run_cutover_rehearsal.sh` exists but has not yet been executed against the freed lanes |
| Formal cutover approval | Not granted | FAZ 1.5 remains a decision gate |

## Acceptance Criteria

The rehearsal may be closed only when all of the following are true:

- baseline lane and candidate lane both return healthy smoke responses
- the alias switch between lanes is reversible
- the rollback returns the system to the previous known-good lane
- the family reports are matched against the frozen eval contract
- no new evidence-integrity ambiguity is introduced

## Current Decision

As of this draft, the repo supports a controlled rehearsal path, but it does not yet support a production cutover declaration. FAZ 1.5 should remain in decision-gate mode until the full-family matched results and rehearsal closure are attached to the same evidence package.
