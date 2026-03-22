# FAZ 1.5 - Post-Train Stabilization and Cutover Readiness Report

**Date:** 2026-03-22  
**Reference:** `docs/FAZ1_5-PLANLAMA-2026-03-22.md`  
**Status:** Draft decision report for master-planner review

## Executive Summary

FAZ 1.5 is not a new feature wave. It is a decision gate for determining whether the promoted `dgx1` candidate can replace the baseline with a defensible scope and rollback posture.

The repo now has the core governance pieces in place:

- eval freeze
- train lineage audit
- production readiness matrix
- scope contract
- promoted candidate serving lane
- baseline serving lane
- matched family runner

The current evidence is strong enough to say the training and promotion process is controlled again. It is not yet enough to declare production cutover readiness for the full target scope.

## What Has Been Closed

### Governance and reproducibility

- `coordination/faz1_5-eval-freeze-2026-03-22.md` freezes the three family sets and the runner contract.
- `scripts/faz1_5/run_matched_eval_family.sh` is the single matched family runner for baseline and candidate comparisons.
- `evaluation/eval_runner.py`, `evaluation/metrics.py`, and `evaluation/report_metadata.py` are the frozen comparison core for this phase.

### Training lineage

- `training/audits/faz1_5-train-lineage-audit-2026-03-22.md` explains the `1076 -> 807` reduction with explicit buckets.
- The audit shows zero train/held-out overlap and preserves the canonicalization story.

### Stabilized serving lane

- The promoted candidate lane is operational on `dgx1`.
- The latest closed cleanup rerun for the candidate shows:
  - citation `88.0%`
  - correct source `86.0%`
  - hallucination `0.0%`
  - refusal `100.0%`
  - average response time `9.116 s`
- The baseline lane remains preserved separately on `dgxnode2`.

### Readiness and scope boundaries

- `coordination/faz1_5-production-readiness-matrix-2026-03-22.md` marks the current state as not cutover-ready.
- `coordination/faz1_5-scope-contract-2026-03-22.md` keeps the claim surface narrow:
  - TBK is primary
  - TMK is narrow
  - broad Turkish law coverage is not claimed
  - unsupported legal domains must refuse or defer

### Matched evidence closed so far

- Official baseline source-of-record was reset to `dgxnode2_base_thinkingoff_r2_20260322` after earlier baseline artefacts were invalidated. See:
  - `coordination/faz1_5-baseline-rerun-reset-2026-03-22.md`
- Closed matched reports at this stage:
  - `evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
  - `evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
  - `evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
- Closed matched manifests at this stage:
  - `evaluation/reports/evidence_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
  - `evaluation/reports/evidence_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
  - `evaluation/reports/evidence_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json`

### Early matched outcome

- Baseline `faz1-50` (`dgxnode2_base_thinkingoff_r2_20260322`) closed strongly:
  - citation `88.0%`
  - correct source `86.7%`
  - hallucination `0.0%`
  - refusal `100.0%`
- Candidate `v2-95` (`dgx1_merged_post_promotion_cleanup_20260322`) also closed above the formal FAZ 1.5 minimum regression bar:
  - citation `86.3%`
  - correct source `72.8%`
  - hallucination `8.4%`
  - refusal `92.6%`
- This means FAZ 1.5 is no longer blocked by a simple `v2-95` regression story. The largest unresolved quality question is now `v3-170`, not `faz1-50`.

## What Is Still Open

The following FAZ 1.5 gates are not fully closed at the time of this draft:

- matched baseline comparator for `v2-95`
- full-family matched evaluation for `v3-170`
- category / root-cause breakdown published from the full family results
- closed rollback rehearsal record
- final steering decision package attached to one evidence bundle

The repo currently contains the machinery for these steps, but the final closed evidence bundle is not yet complete.

## Decision Posture

Based on the repo state available today, the correct posture is:

- `NO-GO` for production cutover
- `CONTINUE FAZ 1.5` for full-family matched evidence and cutover rehearsal closure

The current candidate is technically strong, but the decision standard in FAZ 1.5 is broader than the single `faz1-50` family. A cutover claim should wait until the `v2-95` and `v3-170` family evidence, taxonomy, and rehearsal closure are packaged together.

## Evidence Package Reference

Current supporting artefacts:

- `coordination/faz1_5-eval-freeze-2026-03-22.md`
- `coordination/faz1_5-baseline-rerun-reset-2026-03-22.md`
- `coordination/faz1_5-production-readiness-matrix-2026-03-22.md`
- `coordination/faz1_5-scope-contract-2026-03-22.md`
- `training/audits/faz1_5-train-lineage-audit-2026-03-22.md`
- `evaluation/reports/evidence_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
- `evaluation/reports/evidence_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
- `evaluation/reports/evidence_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
- `evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
- `evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
- `evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_post_promotion_cleanup_20260322.json`

## Conclusion

FAZ 1.5 has re-established a controlled, evidence-backed path from baseline to promoted candidate. The current state supports stabilized operation and a bounded scope contract. It does not yet justify a full production cutover declaration.
