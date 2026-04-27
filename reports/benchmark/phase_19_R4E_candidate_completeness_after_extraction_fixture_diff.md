# Phase 19 R4E Candidate Completeness / Materialization Fixture Diff

Before baseline: `reports/benchmark/runs/20260427T_phase19_R4D_article_span_fixture_after_extraction_envparity/candidate_answers.csv`
After run: `reports/benchmark/runs/20260427T_phase19_R4E_candidate_completeness_fixture_after_extraction_envparity/candidate_answers.csv`
After fixture CSV: `reports/benchmark/phase_19_R4E_candidate_completeness_after_extraction_fixture.csv`
Diff CSV: `reports/benchmark/phase_19_R4E_candidate_completeness_after_extraction_fixture_diff.csv`

Note: the R4D fixture CSV remains the official fixture baseline; R4D candidate answers were used for fields introduced by the R4E hard-stop list that were not present in the narrower R4D fixture CSV.

## Summary

- compared_qids: 11
- compared_fields_per_qid: 18
- material_diff_count: 0
- hard_stop_diff_count: 0

## Hard Stop Fields

`selected_document_id`, `selected_source_family`, `selected_identifier`, `selected_main_span_id`, `selected_main_article`, `selected_supporting_span_ids`, `canonical_span_materialized`, `candidate_completeness_score`, `title_only_fallback_used`, `title_only_answer_degraded`, `selected_document_has_body_span`, `selected_document_has_non_title_span`, `insufficient_canonical_span_evidence`, `corpus_materialization_required`, `canonical_span_materialization_reason`, `body_text_available`, `body_text_length`, `selected_document_only_bundle`

## Diffs

No fixture field drift detected.
