# Phase 22M-B P1 Manual Taxonomy Review Packet

Purpose: obtain legal taxonomy/document identity sign-off for P1 residuals before any runtime or corpus change. Runtime behavior was not changed.

Input artifacts:

- `reports/benchmark/phase_22E_P1_legal_taxonomy_review.md`
- `reports/benchmark/runs/20260501T062248Z_phase22D_full_clean`

## Reviewer Instructions

For each row, fill `legal_reviewer_decision` and `legal_reviewer_notes` in the CSV. The key question is not whether the current answer is good; it is whether the family/document taxonomy can be safely encoded for future backfill or runtime source selection.

Allowed decisions:

```text
do_not_relabel
expected_cb_yonetmelik_source_identified
expected_primary_law_identified
benchmark_item_needs_rubric_review
kky_taxonomy_rule_confirmed
keep_yonetmelik_classification
expected_kky_source_identified
expected_tuzuk_article_identified
corpus_backfill_required
expected_yonetmelik_source_identified
defer_needs_more_legal_research
```

## Row Questions

### CBY-04

- Does the benchmark expect a CB regulation or a CB decree?
- Is the selected `Devlet Arşivleri Başkanlığı Hakkında Cumhurbaşkanlığı Kararnamesi` legally correct as primary source?
- If CB_YONETMELIK is expected, what is the exact source title?
- Confirm that runtime must not relabel CB_KARARNAME as CB_YONETMELIK.

### KANUN-12

- Which law is the primary source?
- Is the selected research reactor regulation only a supporting source?
- Is the expected law already in corpus?
- Would KANUN-over-regulation promotion be legally safe, or should the item wait for exact expected-law identification?

### KKY-01 / KKY-03

- Should the selected/institutional regulation be categorized as KKY or generic YONETMELIK?
- What legal taxonomy rule distinguishes KKY from generic YONETMELIK?
- Is runtime family relabel ever allowed for these rows?
- What is the exact expected source identity?

### TUZUK-05

- What is the correct tüzük source?
- Is article-zero evidence sufficient?
- Which article/span should be materialized?
- Is corpus backfill required?

### YON-04

- Is the expected document the personal data deletion/destruction/anonymization regulation?
- What is the exact source title and identifier?
- Why is nuclear safety regulation selected, and can a source retention fix be legally constrained?
- Should this wait for corpus/legal mapping rather than runtime patching?

CSV: `reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.csv`

