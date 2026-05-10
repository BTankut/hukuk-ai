# Phase25M-B Hardening Branch Archive Report

Generated: 2026-05-10

## Decision

```text
hardening_active_development = false
hardening_reference_only = true
main_active_development = true
```

The hardening branch is no longer the active implementation base. It remains available only for audit, historical reference, and recovery evidence.

## Required Fields

```text
hardening_branch_name = bt/hukuk-ai-100-benchmark-hardening
last_known_hardening_head = 79803da
reason_not_merged_wholesale = mixed branch containing benchmark hardening history, runtime recovery attempts, diagnostic feature flags, reports, and artifacts
```

## Merged Subset Summary

Already merged to `main`:

- PR1 product policy docs
- PR2 judicial corpus architecture and dry-run docs
- product-control policy baseline under `reports/benchmark/productization/`
- judicial dry-run architecture/intake docs under `reports/benchmark/productization/`

Current main head used for Phase25M:

```text
origin/main = 3778fa4
```

## Remaining Unmerged Categories

The hardening branch still contains categories that must not be merged wholesale:

- benchmark hardening history
- runtime recovery attempts
- failed or diagnostic-only feature flags
- source-selection residual work
- large diagnostic/report history
- trace/run/raw artifacts or local artifact references
- experimental candidate gateway material
- QID-specific or benchmark-derived runtime logic
- product transition reports that are useful as history but not implementation base

## Allowed Future Use

The hardening branch may be used only for:

- audit reference
- historical evidence
- comparing previous decisions
- cherry-picking docs/reference material after explicit review
- reconstructing why a path was rejected

## Forbidden Future Use

The hardening branch must not be used for:

- active runtime implementation
- direct product-control implementation base
- wholesale merge into `main`
- re-opening source-selection residual recovery
- moving failed diagnostic flags into main
- moving trace/run/raw artifacts into main
- opening productization, internal eval, reviewer-only eval, serving candidate, or fine-tuning
- connecting judicial corpus to live retrieval or mevzuat collection

## Final Archive Status

```text
hardening_status = reference_only
mainline_status = active_development_base
implementation_base_for_future_work = origin/main
```
