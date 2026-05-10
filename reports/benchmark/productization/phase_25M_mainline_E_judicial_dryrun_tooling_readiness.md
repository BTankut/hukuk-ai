# Phase25M-E Mainline Judicial Dry-Run Tooling Readiness

Generated: 2026-05-10

## Decision

Judicial dry-run tooling may start from `origin/main` on a dedicated dry-run-only branch.

Recommended branch:

```text
bt/mainline-judicial-dryrun-tools
```

## Required Constraints

```text
dry_run_only = true
no live retrieval = true
no production index = true
no mevzuat merge = true
no fine-tuning = true
```

## Readiness Matrix

Detailed matrix:

```text
reports/benchmark/productization/phase_25M_mainline_E_judicial_dryrun_tooling_readiness.csv
```

Tools:

- package_inventory
- checksum_manifest
- file_format_classifier
- dedup_sampler
- metadata_extraction_sampler
- citation_extraction_sampler
- PII_risk_sampler
- chunking_simulator
- embedding_index_sample_plan
- dry_run_report_generator

## Main Docs Baseline

Judicial dry-run docs present on main:

- `phase_25A_judicial_corpus_architecture.md`
- `phase_25A_judicial_ingestion_readiness_checklist.md`
- `phase_25A_judicial_ingestion_readiness_checklist.csv`
- `phase_25B_G_judicial_dry_run_intake_plan.md`
- `phase_25B_G_judicial_dry_run_intake_plan.csv`

## Future Implementation Boundary

Allowed in the future judicial dry-run branch:

- package inventory tooling
- checksum manifest tooling
- file format classification
- sampling-only metadata/citation/PII utilities
- chunk simulation without index creation
- dry-run report generator
- tests using synthetic or tiny redacted fixtures only

Forbidden:

- live retrieval connection
- production judicial index
- Milvus production collection mutation
- mevzuat/yargı collection merge
- fine-tuning
- public endpoint
- raw judicial package commit
- bulk raw text export

## Required Guard Checks

Every future tool should emit or support these guard values:

```text
live_retrieval_connected=false
production_index_created=false
mevzuat_collection_merged=false
fine_tuning_started=false
public_endpoint_exposed=false
raw_artifacts_committed=false
```

## Readiness Result

Mainline judicial dry-run tooling is ready to start as a separate branch from `origin/main`. It is not ready for production indexing, live retrieval, mevzuat merge, or fine-tuning.
