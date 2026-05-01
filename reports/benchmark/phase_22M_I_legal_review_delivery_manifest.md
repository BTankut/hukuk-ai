# Phase 22M-I Legal Review Delivery Manifest

## Purpose

This manifest defines the complete legal-review delivery package and the expected return files for Phase 22M-R2 intake.

Current gate decision:

```text
Await filled legal review CSV files.
No runtime work.
No productization.
No fine-tuning.
```

## Files To Send To Reviewers

CSV input packets:

- `reports/benchmark/phase_22M_P0_manual_legal_review_packet.csv`
- `reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.csv`
- `reports/benchmark/phase_22M_official_source_acquisition_checklist.csv`

Reviewer instructions and handoff documents:

- `reports/benchmark/phase_22M_C_legal_review_followup_packet.md`
- `reports/benchmark/phase_22M_C_legal_review_followup_checklist.md`
- `reports/benchmark/phase_22M_C_P0_reviewer_instructions.md`
- `reports/benchmark/phase_22M_C_P1_taxonomy_reviewer_instructions.md`
- `reports/benchmark/phase_22M_C_official_source_acquisition_instructions.md`
- `reports/benchmark/phase_22M_C_legal_review_handoff_summary.md`

## Expected Return Files

Reviewers must return:

- `filled_phase_22M_P0_manual_legal_review_packet.csv`
- `filled_phase_22M_P1_manual_taxonomy_review_packet.csv`
- `filled_phase_22M_official_source_acquisition_checklist.csv`

Repository drop folder:

```text
reports/benchmark/legal_review_returns/
```

## Minimum Review Decisions

P0 rows must have legal decisions for:

- expected source
- confirmed article or clause
- effective-state/current-law relation
- official source URL
- backfill requirement

P1 rows must have taxonomy decisions for:

- expected source if any
- taxonomy decision
- runtime relabel permission
- backfill requirement

Official source rows must include URL, hash, and parser readiness where required.

## Prohibited Content

No private benchmark answer key should be shared with reviewers or returned in CSV files.

Returned CSV files must not include runtime configuration, prompt configuration, Milvus collection configuration, or QID-specific runtime patch instructions.

## Gate Rule

Phase 22M-R2 may proceed only after all required return files are present and the intake guard passes.

Phase 22F remains closed until Phase 22M-R2 validates legal decisions and official source readiness.
