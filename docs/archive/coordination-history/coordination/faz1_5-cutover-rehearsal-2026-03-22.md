# FAZ 1.5 Cutover Rehearsal

**Date:** 2026-03-22  
**Basis:** `docs/FAZ1_5-PLANLAMA-2026-03-22.md`, current `main`, and existing repo artefacts

## Purpose

This document captures the final FAZ 1.5 cutover rehearsal result. It is not a production cutover approval. It records the operational lanes, the rollback path, and the actual rehearsal evidence now attached to the decision package.

## Current Topology Snapshot

| Lane | Local Alias | Upstream | Model / Checkpoint | Status |
| --- | --- | --- | --- | --- |
| Baseline | `http://127.0.0.1:8000` | `dgxnode2` via SSH tunnel | `Qwen/Qwen3.5-35B-A3B-FP8` / `dgxnode2-base-runtime-thinkingoff-20260322` | Ready for matched comparison |
| Promoted candidate | `http://127.0.0.1:8004` | `dgx1` merged via SSH tunnel | `hukuk-ai-sft-qwen35-807` / `dgx1-merged-post-promotion-cleanup-20260322` | Ready for matched comparison |
| Shared support | `http://127.0.0.1:8081` | Local embedding service | Embedding service | Healthy |
| Shared support | `http://127.0.0.1:19530` | Milvus | Vector store | Healthy |

## Topology Contract

### Internal / pilot topology

- baseline comparator lane: `127.0.0.1:8000 -> dgxnode2` base runtime
- promoted candidate lane: `127.0.0.1:8004 -> dgx1` merged runtime
- shared retrieval stack: local embedding service + Milvus
- allowed FAZ 1.5 claim: controlled pilot/internal cutover rehearsal only

### Customer appliance topology

- not yet frozen as a release target
- no bundled single-device runtime proof exists in the current FAZ 1.5 evidence package
- this topology remains a separate productization question and cannot be inferred from the pilot topology

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
- Official baseline source-of-record was reset to the thinking-off `r2` lane for matched comparison
- The promoted candidate has already passed a closed `faz1-50` post-train cleanup run with `88.0%` citation and `86.0%` correct source.

## Current Status

| Item | Status | Note |
| --- | --- | --- |
| Baseline lane smoke | Ready | `8000` lane is available for comparison |
| Candidate lane smoke | Ready | `8004` lane is available for comparison |
| Rollback path | Ready | Alias can be switched back to baseline lane |
| Full-family matched eval | Closed | baseline and candidate `faz1-50`, `v2-95`, `v3-170` are now closed |
| Repo-native rehearsal script | Closed | `scripts/faz1_5/run_cutover_rehearsal.sh` executed successfully after TERM->KILL fallback hardening |
| Formal cutover approval | Not granted | rehearsal success does not override Gate 2 failure |

## Acceptance Criteria

The rehearsal may be closed only when all of the following are true:

- baseline lane and candidate lane both return healthy smoke responses
- the alias switch between lanes is reversible
- the rollback returns the system to the previous known-good lane
- the family reports are matched against the frozen eval contract
- no new evidence-integrity ambiguity is introduced

## Rehearsal Result

Final rehearsal rerun completed successfully.

Observed sequence:

1. baseline lane on `8000` passed health + cited smoke
2. baseline gateway required `TERM -> KILL` fallback; rehearsal script was hardened accordingly
3. candidate launcher was patched to honor alias-specific `pid/log` names
4. candidate alias was launched on `8000` and passed health + cited smoke
5. rollback re-launched the baseline lane on `8000`
6. baseline post-rollback again passed health + cited smoke

Recorded result:

- cutover path: passed
- rollback path: passed
- cited smoke before cutover: passed
- cited smoke after cutover: passed
- cited smoke after rollback: passed

## Current Decision

The repo now supports a proven pilot cutover path, but it still does not support a production cutover declaration. FAZ 1.5 closes with a successful rehearsal and a `NO-GO - Retrieval/Coverage first` steering result.
