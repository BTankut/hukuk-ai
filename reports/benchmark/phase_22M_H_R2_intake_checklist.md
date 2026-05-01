# Phase 22M-H Phase 22M-R2 Intake Checklist

## Purpose

This checklist defines the preflight checks and expected outputs for Phase 22M-R2 after the filled legal-review CSV files are returned.

Phase 22M-R2 is an intake and decision phase. It is not a runtime remediation phase.

## Required Files Before Opening R2

Confirm all three files exist:

- `filled_phase_22M_P0_manual_legal_review_packet.csv`
- `filled_phase_22M_P1_manual_taxonomy_review_packet.csv`
- `filled_phase_22M_official_source_acquisition_checklist.csv`

## Preflight Checklist

Before Phase 22M-R2 begins, verify:

- filled P0 CSV exists
- filled P1 CSV exists
- filled official source checklist exists
- P0 decisions use allowed enum values
- P1 decisions use allowed enum values
- official URLs are populated
- SHA-256 hashes are populated
- raw file paths are populated where `downloaded=true`
- parser readiness is confirmed where a source is intended for backfill
- article boundaries are detectable where a source is intended for backfill
- no private answer key is included
- no runtime config is included in legal CSVs

## P0 Decision Enum

Allowed P0 legal reviewer decisions:

- `confirmed_expected_source`
- `confirmed_article_or_clause`
- `confirmed_effective_state`
- `confirmed_current_law_relation`
- `confirmed_backfill_required`
- `accepted_as_manual_residual`
- `benchmark_item_legally_invalid`
- `needs_more_official_source_acquisition`

## P1 Decision Enum

Allowed P1 legal reviewer decisions:

- `do_not_relabel`
- `expected_cb_yonetmelik_source_identified`
- `expected_primary_law_identified`
- `benchmark_item_needs_rubric_review`
- `kky_taxonomy_rule_confirmed`
- `keep_yonetmelik_classification`
- `expected_kky_source_identified`
- `expected_tuzuk_article_identified`
- `corpus_backfill_required`
- `expected_yonetmelik_source_identified`
- `defer_needs_more_legal_research`

## Expected Phase 22M-R2 Outputs

Phase 22M-R2 should produce:

```text
reports/benchmark/phase_22M_R2_review_file_validation.md
reports/benchmark/phase_22M_R2_P0_decision_normalization.md
reports/benchmark/phase_22M_R2_P1_taxonomy_decision_normalization.md
reports/benchmark/phase_22M_R2_phase22F_readiness_decision.md
reports/benchmark/phase_22M_R2_legal_review_results_intake_report.md
```

CSV companions should be produced for validation and normalization outputs where row-level decisions are needed.

## R2 Decision Branches

If only the official source checklist is returned but legal decisions are missing:

```text
Continue legal review.
No Phase 22F.
```

If legal decisions are returned but official sources, hashes, or parser readiness are incomplete:

```text
Open Phase 22S Official Source Acquisition.
No Phase 22F yet.
```

If legal decisions and source readiness are complete:

```text
Open Phase 22F P0 Shadow Backfill Implementation.
```

If the legal owner accepts unresolved rows as residual risk:

```text
Record accepted residual risk before any productization readiness audit.
```

## Prohibited During R2

Do not perform:

- runtime code changes
- retrieval/top-k/prompt changes
- source identity patches
- answer synthesis patches
- live collection updates
- shadow collection builds
- benchmark runs
- fine-tuning
- productization
