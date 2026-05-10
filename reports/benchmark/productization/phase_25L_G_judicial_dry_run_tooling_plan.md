# Phase25L-G Judicial Dry-Run Tooling Plan

Generated: 2026-05-10

## Decision

Plan only. Judicial corpus remains dry-run only.

Phase25L does not receive a judicial package, parse a judicial corpus, create a production index, connect judicial decisions to live retrieval, merge judicial data with mevzuat, expose a public endpoint, or start fine-tuning.

## Required Constraints

```text
dry_run_only
no production index
no live retrieval
no mevzuat merge
no fine-tuning
no public endpoint
```

## Tooling Plan

The detailed tool matrix is in:

```text
reports/benchmark/productization/phase_25L_G_judicial_dry_run_tooling_plan.csv
```

Required dry-run tools:

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

## Dry-Run Directory Boundary

Recommended future layout:

```text
reports/benchmark/judicial_dry_run/
  incoming/
  manifests/
  samples/
  reports/
  redacted_exports/
```

The `incoming/` package area must be excluded from commits unless it contains tiny synthetic fixtures. Raw judicial files must not be committed.

## Tool Sequence

1. `package_inventory` records file paths, byte sizes, and basic receipt metadata.
2. `checksum_manifest` computes SHA-256 for every file.
3. `file_format_classifier` classifies files without production conversion.
4. `dedup_sampler` samples exact and near-duplicate risk.
5. `metadata_extraction_sampler` samples court/date/docket fields.
6. `citation_extraction_sampler` samples legal citation extraction.
7. `PII_risk_sampler` estimates PII exposure and redaction needs.
8. `chunking_simulator` simulates chunks without embeddings or index creation.
9. `embedding_index_sample_plan` defines a future offline sample only.
10. `dry_run_report_generator` consolidates outputs and asserts dry-run constraints.

## Guard Conditions

Each tool must write a guard section to its report:

```text
live_retrieval_connected=false
production_index_created=false
mevzuat_collection_merged=false
public_endpoint_exposed=false
fine_tuning_started=false
raw_artifacts_committed=false
```

If any guard would become true, the tooling must stop and report.

## PII Handling

The `PII_risk_sampler` must run before any wider text export. Sample reports must redact personal data by default and should include only entity type counts, risk levels, and redacted snippets when necessary.

## Index Boundary

`embedding_index_sample_plan` is intentionally plan-only in this phase. A future offline sample index, if authorized, must be:

- isolated from live Milvus collections
- named as dry-run only
- inaccessible to public chat routes
- excluded from serving-candidate config
- destroyed or archived under an explicit retention decision

## Gate Result

Judicial dry-run is documentation-ready but not tooling-ready until the Phase25M dry-run tools exist and pass guard checks. Live retrieval and mevzuat merge remain closed.
