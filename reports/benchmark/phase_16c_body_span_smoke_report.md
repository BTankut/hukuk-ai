# Phase 16C Body-Span Smoke Report

- run_dir: `reports/benchmark/runs/20260424T112937Z_phase16c_body_span_smoke`
- qids: `CBG-01 CBG-02 CBG-03 CBG-04 CBKAR-07 CBKAR-08 TEB-01 TEB-03 TEB-04`
- gateway: `http://127.0.0.1:8000/v1`
- model: `hukuk-ai-poc`
- errors: 0
- missing_trace: 0
- contract_valid: 9/9

## Materialization Result

- canonical_span_materialized_count: 7/9
- corpus_materialization_required_count: 2/9
- title_only_answer_degraded_count: 2/9
- selected_document_document_level_body_span_count: 7/9
- selected_document_materialized_body_span_count: 7/9
- legacy_source_key_collision_detected_count: 3/9
- source_key_v2_collision_detected_count: 0/9

## Family Result

- CB_GENELGE: 3/4 materialized; remaining row `CBG-04` is blocked by legacy source-key collision without selected-family body span.
- CB_KARAR: 1/2 materialized; remaining row `CBKAR-08` is blocked by legacy source-key collision without selected-family body span.
- TEBLIGLER: 3/3 materialized.

## Score Snapshot

- raw_score_proxy: 45.05 / 90
- pass_proxy: 3/9
- avg_required_fact_coverage_score: 0.779
- minimum_answer_facts_present_count: 4/9
- unsupported_confident_answer_count: 0

## Conclusion

- The systemic document-level body-span rule works for CB_GENELGE, CB_KARAR and TEBLIGLER when the selected span is `m.0` but body text is readable.
- The rule does not depend on a specific question id and does not override explicit article requests.
- The remaining body-span blockers are collision rows where the selected legacy key still lacks selected-family body materialization; source-key v2 trace now shows no v2 collision, so the next remediation should use v2 document keys for selected-family body lookup.
