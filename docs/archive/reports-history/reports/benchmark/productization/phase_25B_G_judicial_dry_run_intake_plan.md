# Phase25B-G Judicial Corpus Dry-Run Intake Plan

Generated: 2026-05-08

## Constraints

```text
dry_run_only
no_production_index
no_live_retrieval
no_merge_with_mevzuat
no_fine_tuning
no_public_endpoint
```

This plan defines the first safe operation when the 1.5M+ judicial decision package is available. It does not authorize production indexing, live retrieval, or corpus merge.

CSV artifact: `reports/benchmark/productization/phase_25B_G_judicial_dry_run_intake_plan.csv`

## Dry-Run Stages

| stage | output | success gate |
| --- | --- | --- |
| 1. package inventory | `judicial_package_inventory.csv` | every file inventoried |
| 2. file format classification | `judicial_format_classification.csv` | parser route or quarantine reason for every file |
| 3. checksum manifest | `judicial_raw_sha256_manifest.jsonl` | raw SHA-256 for every file |
| 4. dedup sample | `judicial_dedup_sample_report.csv` | raw duplicates and canonical-case duplicates separated |
| 5. metadata extraction sample | `judicial_metadata_extraction_sample.csv` | court/chamber/date/case/decision fields extracted or unknown |
| 6. citation extraction sample | `judicial_citation_extraction_sample.csv` | citation label reconstructable or flagged |
| 7. PII risk scan sample | `judicial_pii_risk_scan_sample.md` | PII risk band and redaction recommendation recorded |
| 8. chunking simulation | `judicial_chunking_simulation_report.md` | every chunk preserves judicial identity metadata |
| 9. embedding/index dry-run sample | `judicial_index_dry_run_sample_report.md` | separate judicial schema validated without production index |
| 10. evaluation sample design | `judicial_eval_sample_design.csv` | stratified evaluation sample plan created |

## Non-Negotiable Separation Rules

- Judicial decisions are not written into the mevzuat collection.
- Judicial decision citation labels are not reused as mevzuat source identity.
- Judicial retrieval is not attached to live `8000`.
- Judicial dry-run outputs are summaries/manifests only unless a raw artifact store is explicitly designated.
- PII risk scan must precede any broad reviewer sharing.

## Dry-Run Success Definition

The dry-run is successful only if it produces:

- complete inventory
- raw hash manifest
- format/parser classification
- duplicate-risk report
- sampled metadata and citation extraction report
- PII risk report
- chunking simulation report
- separate-index dry-run schema report
- evaluation sample design

The dry-run is not a product readiness gate and does not open serving.

## Stop Conditions

Stop and report if:

- package contains uncontrolled PII at scale
- parser cannot reliably extract court/case identity
- duplicate rate cannot be measured
- chunks cannot preserve `canonical_case_key`
- any process attempts production index creation
- any process attempts live retrieval connection
- any process attempts merge into mevzuat collection
