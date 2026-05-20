# FAZ 1.5 Implementation Plan

**Date:** 2026-03-22  
**Reference:** `docs/FAZ1_5-PLANLAMA-2026-03-22.md`  
**Intent:** turn the planning document into a repo-native execution order with concrete artefacts, scripts, and gate outputs

## Executive Position

FAZ 1.5 is being executed as a decision gate, not as a feature wave.

Primary question:

> Is the promoted `dgx1` merged candidate actually ready to replace the baseline, and if not, which investment path should come next?

This implementation plan keeps the work ordered as:

1. freeze the comparison ground,
2. run full-family matched eval,
3. classify errors,
4. close the audit and readiness paperwork,
5. run cutover/rollback rehearsal,
6. publish a single decision package.

## Current Repo Reality At Start

- promoted candidate exists and passed `faz1-50` on `dgx1`
- baseline lane is still separate and preserved
- train package is frozen at `807` rows
- readiness gate and evidence contract already exist
- missing evidence before FAZ 1.5:
  - no matched `v2-95` baseline/candidate pair
  - no matched `v3-170` baseline/candidate pair
  - no formal cutover rehearsal record
  - no FAZ 1.5 freeze artefact
  - no formal final decision package

## Work Packages

### WP-1 — Eval Freeze and Reproducibility

Goal:
- freeze the exact datasets, runner, metrics code, and invocation path used for FAZ 1.5

Repo actions:
- freeze question sets:
  - `configs/evaluation/test_questions.json`
  - `configs/evaluation/test_questions_v2_95.json`
  - `configs/evaluation/test_questions_v3_170.json`
- freeze runner and metrics inputs:
  - `evaluation/eval_runner.py`
  - `evaluation/metrics.py`
  - `evaluation/report_metadata.py`
- freeze the matched-run wrapper:
  - `scripts/faz1_5/run_matched_eval_family.sh`
- publish:
  - `coordination/faz1_5-eval-freeze-2026-03-22.md`

Exit:
- all matched eval results must be traceable back to the frozen files above

### WP-2 — Full-Family Matched Eval

Goal:
- produce official matched baseline and candidate reports for `faz1-50`, `v2-95`, `v3-170`

Repo actions:
- baseline lane:
  - `scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh`
  - `http://127.0.0.1:8000`
- promoted candidate lane:
  - `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh`
  - `http://127.0.0.1:8004`
- matched family runner:
  - `scripts/faz1_5/run_matched_eval_family.sh`

Expected artefacts:
- `evaluation/reports/eval_baseline_faz1-50_matched_*.json`
- `evaluation/reports/eval_baseline_v2-95_matched_*.json`
- `evaluation/reports/eval_baseline_v3-170_matched_*.json`
- `evaluation/reports/eval_post_train_faz1-50_matched_*.json`
- `evaluation/reports/eval_post_train_v2-95_matched_*.json`
- `evaluation/reports/eval_post_train_v3-170_matched_*.json`

Exit:
- all six matched reports exist and are produced by the same runner family

### WP-3 — Error Taxonomy and Category Breakdown

Goal:
- convert raw report differences into decision-ready root-cause classes

Repo actions:
- compute family-level deltas
- inspect `by_category` and `per_question`
- classify failures into:
  - retrieval miss
  - wrong source despite evidence
  - cross-law confusion
  - unsupported question answered
  - refusal miss / over-refusal
  - outdated or missing coverage
  - infrastructure / timeout / serving error
- publish:
  - `evaluation/reports/faz1_5-category-breakdown-2026-03-22.md`

Exit:
- every serious regression is assigned at least one root-cause class

### WP-4 — Train Data Lineage Audit

Goal:
- formally explain the `1076 -> 807` shrink

Repo actions:
- consume and verify:
  - `training/audits/faz1_5-train-lineage-audit-2026-03-22.md`
  - `training/audits/faz1_5-train-lineage-audit-2026-03-22.json`

Exit:
- the shrink is auditable and train/held-out separation is evidenced

### WP-5 — Production Readiness Matrix

Goal:
- separate must-close release blockers from deferrable debt

Repo actions:
- review and integrate:
  - `coordination/faz1_5-production-readiness-matrix-2026-03-22.md`

Exit:
- must-close vs defer is explicit

### WP-6 — Topology Contract and Cutover Rehearsal

Goal:
- prove that pilot cutover and rollback are operationally distinct from productization

Repo actions:
- define:
  - internal/pilot topology = `dgx1` primary, `node3` fallback, local gateway/milvus/embedding
  - customer appliance topology = explicitly not yet closed in FAZ 1.5
- perform:
  - controlled cutover rehearsal on the baseline alias lane
  - rollback rehearsal
  - smoke and health verification
- publish:
  - `coordination/faz1_5-cutover-rehearsal-2026-03-22.md`

Exit:
- at least one successful rollback rehearsal record exists

### WP-7 — Scope Contract

Goal:
- state what the system does and does not claim

Repo actions:
- review and integrate:
  - `coordination/faz1_5-scope-contract-2026-03-22.md`

Exit:
- release claims are bounded by a written scope contract

### WP-8 — Final Decision Package

Goal:
- end FAZ 1.5 with exactly one steering outcome

Repo actions:
- consolidate:
  - freeze note
  - matched reports
  - category breakdown
  - lineage audit
  - readiness matrix
  - cutover rehearsal
  - scope contract
- publish:
  - `docs/FAZ1_5-POSTTRAIN-STABILIZATION-AND-CUTOVER-READINESS-RAPORU.md`

Allowed outcomes:
- `GO`
- `NARROW GO`
- `NO-GO — Stabilization`
- `NO-GO — Retrieval/Coverage`
- `NO-GO — Productization`

## Parallelization Plan

Main rollout ownership:
- WP-1 freeze
- WP-2 matched eval execution
- WP-3 taxonomy and breakdown
- WP-6 cutover rehearsal
- WP-8 final decision package

Parallel agent ownership:
- lineage audit:
  - `training/audits/faz1_5-train-lineage-audit-2026-03-22.md`
  - `training/audits/faz1_5-train-lineage-audit-2026-03-22.json`
- readiness and scope:
  - `coordination/faz1_5-production-readiness-matrix-2026-03-22.md`
  - `coordination/faz1_5-scope-contract-2026-03-22.md`

## Gate Discipline

FAZ 1.5 will not claim cutover readiness unless all of the following are true:

- freeze artefact exists
- matched baseline and candidate reports exist for all three families
- no unresolved artefact-integrity ambiguity remains
- category/root-cause breakdown exists
- lineage audit is published
- readiness matrix is published
- rollback rehearsal is recorded
- scope contract is published

If these do not all close, the only valid outcome is a documented `NO-GO` or `NARROW GO`.
