# Phase 22M-C Legal Review Follow-Up Checklist

## Required Return Files

| File | Required | Status before return |
|---|---:|---|
| `filled_phase_22M_P0_manual_legal_review_packet.csv` | yes | missing |
| `filled_phase_22M_P1_manual_taxonomy_review_packet.csv` | yes | missing |
| `filled_phase_22M_official_source_acquisition_checklist.csv` | yes | missing |

## P0 Completion Checklist

For `MULGA-01` and `TEB-06`, each row must include:

- `qid`
- `legal_reviewer_decision`
- `legal_reviewer_notes`
- `confirmed_expected_source`
- `confirmed_article_or_clause`
- `official_source_url`
- `effective_state_decision`
- `current_law_relation`
- `backfill_required`

## P1 Completion Checklist

For `CBY-04`, `KANUN-12`, `KKY-01`, `KKY-03`, `TUZUK-05`, and `YON-04`, each row must include:

- `qid`
- `legal_reviewer_decision`
- `legal_reviewer_notes`
- `expected_source_if_any`
- `taxonomy_decision`
- `runtime_relabel_allowed`
- `backfill_required`

## Official Source Completion Checklist

For each required source, each row must include:

- `source_title`
- `official_url`
- `source_type`
- `publication_date`
- `official_gazette_no`
- `downloaded`
- `raw_file_path`
- `sha256`
- `parser_ready`
- `article_boundaries_detectable`
- `notes`

## Blocking Conditions

Phase 22F remains blocked if:

- any filled CSV is missing
- any mandatory field is empty
- legal reviewer notes are missing
- official URL is missing
- raw source was not downloaded
- SHA-256 is missing
- parser readiness is not confirmed
- article boundaries are not detectable

## Non-Runtime Scope

This checklist does not authorize runtime changes, source identity patches, QID-specific rules, live collection updates, shadow collection builds, productization, or fine-tuning.
