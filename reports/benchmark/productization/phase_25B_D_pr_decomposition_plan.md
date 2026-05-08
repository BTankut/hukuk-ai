# Phase25B-D PR Decomposition Plan

Generated: 2026-05-08

## Decision

No direct branch merge.

Use split PRs with explicit scope boundaries. The hardening branch contains 1459 committed diff paths across runtime code, feature flags, tests, reports, run artifacts, raw sources, product policy, and judicial architecture. A wholesale merge would mix safe governance docs with failed/diagnostic runtime work.

## PR 1 - Product Policy Docs

Scope:

```text
guardrails policy
verification policy
privacy / PII policy
audit logging policy
trace exposure policy
manual review workflow
confidence / UX policy
rollback runbook
product readiness reports
Phase25A/Phase25B product-control summaries
```

Allowed paths:

```text
reports/benchmark/productization/*.md
reports/benchmark/productization/*.csv
```

Exclusions:

- runtime source code
- raw source files
- trace files
- run directories
- local legal-review return packages unless converted to compact governance summaries

Review owner: `product_policy_owner`.

## PR 2 - Judicial Corpus Architecture

Scope:

```text
judicial corpus architecture
judicial ingestion checklist
judicial dry-run intake plan
dry-run schema docs
routing design docs
```

Required constraints:

```text
dry_run_only
no_production_index
no_live_retrieval
no_merge_with_mevzuat
```

Review owner: `judicial_corpus_owner`.

## PR 3 - Benchmark / Report Governance

Scope:

```text
trace artifact policy
.gitignore updates
benchmark summary docs
non-large reporting structure
CI/report guard docs
```

Allowed:

- compact summaries
- manifest schemas
- artifact retention rules
- trace exclusion rules

Excluded:

- `trace.jsonl`
- full run directories
- bulky scored dumps
- raw PDF/source packages
- generated local logs

Review owner: `evaluation_owner`.

## PR 4 - Safe Tests / Utilities

Scope:

```text
low-risk utility scripts
tests for accepted docs/governance utilities
tests for accepted runtime code only if runtime PR is later approved
```

Default status: `defer`.

Reason: many tests in the branch target runtime code that is not currently approved for main. Tests should not be merged without the code they validate or they will create misleading main-branch obligations.

Review owner: `test_owner`.

## PR 5 - Runtime Code

Default decision:

```text
do_not_merge_failed_runtime_recovery_code_into_main
```

Runtime code in the branch includes answer contract work, retrieval orchestration, source identity, trace instrumentation, feature flags, and recovery attempts. Some parts may be valuable later, but Phase25B does not approve a runtime merge.

Required before any future runtime PR:

- independent runtime design review
- feature flag default audit
- non-live tests
- regression proof against accepted baseline
- explicit product owner approval
- no QID-specific logic
- no live `8000` or Milvus mutation as part of PR review

Review owner: `runtime_owner`.

## Recommended PR Order

1. PR 1 - product policy docs.
2. PR 2 - judicial corpus architecture and dry-run intake docs.
3. PR 3 - benchmark/report governance and artifact retention.
4. PR 4 - safe tests/utilities only if independent and low risk.
5. PR 5 - runtime code only after a new explicit runtime re-open decision.

## Current Main Readiness

Recommended current action:

```text
Open docs/policy/judicial architecture PRs only.
Exclude runtime code and run/raw/trace artifacts.
```
