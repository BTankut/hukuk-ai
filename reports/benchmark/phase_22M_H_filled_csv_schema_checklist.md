# Phase 22M-H Filled CSV Schema Checklist

## Purpose

This checklist defines the minimum schema required for the filled Phase 22M legal-review and official-source acquisition CSV files.

Phase 22M-R2 must reject or block any file that does not satisfy these fields.

## Required Filled Files

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

## P0 Filled CSV Required Fields

File:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
```

Required fields:

- `qid`
- `legal_reviewer_decision`
- `legal_reviewer_notes`
- `confirmed_expected_source`
- `confirmed_article_or_clause`
- `official_source_url`
- `effective_state_decision`
- `current_law_relation`
- `backfill_required`

Required rows:

- `MULGA-01`
- `TEB-06`

## P1 Filled CSV Required Fields

File:

```text
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
```

Required fields:

- `qid`
- `legal_reviewer_decision`
- `legal_reviewer_notes`
- `expected_source_if_any`
- `taxonomy_decision`
- `runtime_relabel_allowed`
- `backfill_required`

Required rows:

- `CBY-04`
- `KANUN-12`
- `KKY-01`
- `KKY-03`
- `TUZUK-05`
- `YON-04`

## Official Source Acquisition Filled CSV Required Fields

File:

```text
filled_phase_22M_official_source_acquisition_checklist.csv
```

Required fields:

- `source_title`
- `official_url`
- `downloaded`
- `raw_file_path`
- `sha256`
- `parser_ready`
- `article_boundaries_detectable`

Recommended additional fields:

- `source_type`
- `publication_date`
- `official_gazette_no`
- `notes`

## Required Boolean Format

Use lowercase values:

```text
true
false
```

This applies to:

- `backfill_required`
- `runtime_relabel_allowed`
- `downloaded`
- `parser_ready`
- `article_boundaries_detectable`

## Blocking Validation Conditions

Phase 22M-R2 must block Phase 22F if:

- a required file is missing
- a required field is missing
- a required row is missing
- legal reviewer notes are empty
- official URL is empty
- SHA-256 hash is empty
- raw file path is empty for a downloaded source
- parser readiness is not confirmed
- article boundaries are not detectable
- private benchmark answer key content appears in the CSV
- runtime configuration appears in the legal-review CSV

## Gate Rule

Schema validity alone does not open Phase 22F. Phase 22F also requires normalized legal decisions and official source readiness.
