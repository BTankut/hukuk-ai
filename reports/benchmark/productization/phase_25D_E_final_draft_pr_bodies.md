# Phase25D-E Final Draft PR Bodies

Generated: 2026-05-09

These are final draft bodies only. No PR is opened by this artifact.

## PR1 — Product Policy Docs

### Scope

Add Hukuk-AI product policy and control-completion documentation for owner review and future governance.

### Included Files

Use final manifest:

- `reports/benchmark/productization/phase_25D_B_pr1_final_manifest.md`
- `reports/benchmark/productization/phase_25D_B_pr1_final_manifest.csv`

Core included groups:

- guardrails, verification, privacy/PII, audit logging
- trace exposure and artifact retention
- manual review workflow
- confidence / UX policy
- rollback / incident runbook
- access-control policy
- monitoring / metrics policy
- reviewer-only eval template
- residual acceptance matrix
- product controls closure workplan

### Explicit Exclusions

- runtime code
- feature flag code
- benchmark runner changes
- scorer changes
- run directories
- `trace.jsonl`
- raw source artifacts
- candidate collection configs
- model / prompt / top-k changes

### Required Statements

No runtime code included.

No live 8000 change.

No productization.

No internal eval opening.

No fine-tuning.

No yargı-live retrieval.

Reviewer-only eval remains not opened.

### Risk Assessment

Low if this remains docs-only. The main risk is interpreting policy documents as runtime enforcement. The PR should be reviewed as governance documentation only.

### Runtime Impact Statement

Runtime impact: none.

### Live Impact Statement

Live impact: none. The live `8000` endpoint is not changed.

### Test / Validation Notes

- CSV manifests/templates parse as CSV.
- No runtime tests are required for this docs-only PR.
- Review should verify no run/raw/trace artifacts are included.

### Review Checklist

- Confirm PR1 final manifest includes only allowed policy/control docs.
- Confirm no runtime code or feature flag code.
- Confirm no `trace.jsonl`, run directories, or raw source artifacts.
- Confirm no eval/productization/serving/fine-tuning enablement.

### Rollback / Close Plan

Close or revert the PR if runtime code, live config changes, trace/run/raw artifacts, or eval/product enablement enters scope.

## PR2 — Judicial Corpus Architecture and Dry-Run Docs

### Scope

Add judicial corpus architecture and dry-run intake documentation for future 1.5M+ judicial decision package handling.

### Included Files

Use final manifest:

- `reports/benchmark/productization/phase_25D_C_pr2_final_manifest.md`
- `reports/benchmark/productization/phase_25D_C_pr2_final_manifest.csv`

Core included groups:

- judicial corpus architecture
- judicial ingestion readiness checklist
- judicial dry-run intake plan
- judicial merge-readiness context docs

### Explicit Exclusions

- production judicial index
- live retrieval wiring
- mevzuat collection merge
- raw judicial decision files
- raw source PDFs
- runtime code
- fine-tuning
- public endpoint exposure

### Required Statements

No runtime code included.

No live 8000 change.

No productization.

No internal eval opening.

No fine-tuning.

No yargı-live retrieval.

Judicial corpus remains dry-run only.

### Risk Assessment

Low if this remains docs-only. The primary risk is premature ingestion or live judicial retrieval. The PR must preserve dry-run-only constraints.

### Runtime Impact Statement

Runtime impact: none.

### Live Impact Statement

Live impact: none. No live retrieval endpoint, production index, or Milvus collection change is introduced.

### Test / Validation Notes

- CSV checklists/manifests parse as CSV.
- No live retrieval, Milvus mutation, or runtime test should run for this PR.

### Review Checklist

- Confirm judicial corpus is separate from mevzuat.
- Confirm dry-run-only constraint.
- Confirm no production index or live retrieval.
- Confirm no raw source package.
- Confirm no fine-tuning or public endpoint change.

### Rollback / Close Plan

Close or revert the PR if production indexing, live retrieval, mevzuat merge, runtime code, or raw judicial artifacts enter scope.

## PR3 — Optional Benchmark / Report Governance

### Scope

Optional governance PR for artifact retention, trace exclusion, compact benchmark/report governance, and possibly `.gitignore` updates if owner approves.

Current Phase25D decision:

```text
defer_PR3
```

### Included Files If Later Approved

Use optional manifest:

- `reports/benchmark/productization/phase_25D_D_optional_pr3_governance_manifest.md`
- `reports/benchmark/productization/phase_25D_D_optional_pr3_governance_manifest.csv`

Potential included groups:

- artifact retention policy
- trace exclusion guard report
- compact diff/report governance summaries
- `.gitignore` updates only after separate review

### Explicit Exclusions

- large run dirs
- `trace.jsonl`
- full trace payloads
- raw source blobs
- full diagnostic dumps
- local logs
- runtime code

### Required Statements

No runtime code included.

No live 8000 change.

No productization.

No internal eval opening.

No fine-tuning.

No yargı-live retrieval.

### Risk Assessment

Medium because governance PRs can accidentally include generated artifacts. Open only after strict staged-file review.

### Runtime Impact Statement

Runtime impact: none.

### Live Impact Statement

Live impact: none.

### Test / Validation Notes

- Run staged-file review before opening.
- Confirm no excluded trace/run/raw artifacts.
- Confirm all included files are compact governance artifacts.

### Review Checklist

- Confirm PR3 is owner-approved.
- Confirm `.gitignore` changes are reviewed separately if included.
- Confirm no `reports/benchmark/runs/**`.
- Confirm no `trace.jsonl`.
- Confirm no raw source artifacts or local logs.

### Rollback / Close Plan

Close or revert the PR if excluded generated artifacts or runtime code enter scope.
