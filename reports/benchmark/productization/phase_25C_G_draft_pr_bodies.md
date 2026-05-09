# Phase25C-G Draft PR Bodies

Generated: 2026-05-09

These are draft bodies only. Phase25C does not open PRs.

## PR 1 — Product Policy Docs

### Scope

Add product-governance policy docs and control-completion artifacts for Hukuk-AI.

### Included Files

- `reports/benchmark/productization/guardrails_policy.md`
- `reports/benchmark/productization/verification_policy.md`
- `reports/benchmark/productization/privacy_pii_policy.md`
- `reports/benchmark/productization/audit_logging_policy.md`
- `reports/benchmark/productization/trace_exposure_policy.md`
- `reports/benchmark/productization/manual_review_workflow.md`
- `reports/benchmark/productization/confidence_ux_policy.md`
- `reports/benchmark/productization/rollback_incident_runbook.md`
- `reports/benchmark/productization/access_control_policy.md`
- `reports/benchmark/productization/monitoring_metrics_policy.md`
- `reports/benchmark/productization/reviewer_only_eval_form_template.md`
- `reports/benchmark/productization/reviewer_only_eval_form_template.csv`
- `reports/benchmark/productization/artifact_retention_and_trace_exclusion_policy.md`
- selected compact product readiness and residual/control reports from Phase25A/B/C

### Explicit Exclusions

- runtime code
- diagnostic feature flags
- run directories
- `trace.jsonl`
- raw source artifacts
- candidate collection configs
- productization, internal eval, reviewer-only eval, serving candidate, or fine-tuning enablement

### Risk Assessment

Risk is low if the PR remains docs-only. The main risk is misreading policy artifacts as proof of runtime enforcement. PR text must state that guardrails, verification, monitoring, and access-control runtime enforcement are not evidenced yet.

### Test / Validation Notes

- CSV manifests/templates parse as CSV.
- No runtime tests are expected because this is docs-only.
- Review should verify no run/raw/trace artifacts are included.

### Rollback / Close Plan

Close or revert the PR if any runtime code, trace artifact, raw source artifact, or eval-opening change enters scope.

### Review Checklist

- Confirm docs-only scope.
- Confirm runtime code excluded.
- Confirm reviewer-only eval remains not opened.
- Confirm productization/internal eval/serving/fine-tuning remain closed.
- Confirm no raw traces or source blobs are included.

## PR 2 — Judicial Corpus Architecture and Dry-Run Docs

### Scope

Add judicial corpus architecture and dry-run intake documentation for future 1.5M+ judicial decision package handling.

### Included Files

- `reports/benchmark/productization/phase_25A_judicial_corpus_architecture.md`
- `reports/benchmark/productization/phase_25A_judicial_ingestion_readiness_checklist.md`
- `reports/benchmark/productization/phase_25A_judicial_ingestion_readiness_checklist.csv`
- `reports/benchmark/productization/phase_25B_G_judicial_dry_run_intake_plan.md`
- `reports/benchmark/productization/phase_25B_G_judicial_dry_run_intake_plan.csv`
- `reports/benchmark/productization/phase_25C_B_pr2_judicial_architecture_packet.md`
- `reports/benchmark/productization/phase_25C_B_pr2_judicial_architecture_manifest.csv`

### Explicit Exclusions

- production judicial index
- live retrieval wiring
- mevzuat collection merge
- raw judicial decision files
- raw source PDFs
- fine-tuning
- public endpoint exposure

### Risk Assessment

Risk is low if this remains architecture/dry-run documentation. The primary risk is premature ingestion or live retrieval connection. The PR must preserve `dry_run_only`, `no_production_index`, `no_live_retrieval`, and `no_merge_with_mevzuat`.

### Test / Validation Notes

- CSV checklists/manifests parse as CSV.
- No live retrieval, Milvus mutation, or runtime test should be run for this PR.

### Rollback / Close Plan

Close or revert the PR if it introduces production indexing, live retrieval, mevzuat merge, or raw judicial corpus artifacts.

### Review Checklist

- Confirm judicial corpus is separate from mevzuat.
- Confirm dry-run-only constraint.
- Confirm no production index or live retrieval.
- Confirm no raw source package included.
- Confirm no fine-tuning or public endpoint change.

## PR 3 — Benchmark / Report Governance

### Scope

Optional PR for artifact retention, trace exclusion, compact benchmark/report governance, and `.gitignore`/CI guard changes if selected by owner.

### Included Files

- `reports/benchmark/productization/artifact_retention_and_trace_exclusion_policy.md`
- `reports/benchmark/productization/phase_25C_F_artifact_retention_guard_report.md`
- selected compact report-governance docs
- `.gitignore` changes only if reviewed separately

### Explicit Exclusions

- `reports/benchmark/runs/**`
- `trace.jsonl`
- full trace payloads
- raw source blobs
- large scored dumps
- local logs

### Risk Assessment

Risk is medium because governance PRs can accidentally pull in large generated artifacts. Use a strict staged-file review before opening.

### Test / Validation Notes

- Run `git diff --cached --name-only` before PR opening.
- Confirm no `trace.jsonl`, run directory, raw source artifact, or oversized file is staged.

### Rollback / Close Plan

Close PR or remove offending files if any excluded artifact enters scope.

### Review Checklist

- Confirm artifact retention policy is present.
- Confirm trace/run/raw exclusions are followed.
- Confirm all included files are compact governance artifacts.
- Confirm no runtime code is included.
