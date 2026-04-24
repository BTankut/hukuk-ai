# Phase 14 Full Diagnostic Summary

## Verdict
- phase14_diagnostic_scope: FULL_100_RERUN_AFTER_PHASE14C
- diagnostic_rerun_status: COMPLETE
- diagnostic_acceptance_gate: FAILED
- forensic_artifacts: COMPLETE
- productization_gate: CLOSED
- fine_tuning_gate: CLOSED
- next_phase_recommendation: continue systemic retrieval/document identity/article-span/corpus materialization and confidence-policy hardening before any fine-tune cycle

## Run Integrity
- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- full_benchmark_total: 100
- answered: 100
- errors: 0
- refused_or_empty: 0
- contract_valid: 100
- green_lane_status: pass

## Score Results
- raw_score_proxy: 729.32 / 1000.0
- average_score_0_10_proxy: 7.29
- pass_proxy: 70
- fail_proxy: 30
- wrong_family: 15
- wrong_document: 13
- wrong_article: 2
- hallucinated_identifier: 21
- hallucinated_source_count: 13
- unsupported_confident_claim: 25
- selected_article_equals_claimed_article_count: 80
- selected_article_equals_claimed_article_rate: 0.8
- right_document_wrong_article_or_span: 70
- missing_required_content_signal: 96
- partial_grounding_only: 96

## Canonical Span Materialization
- canonical_span_materialized_count: 87
- corpus_materialization_required_count: 13
- insufficient_canonical_span_evidence_count: 13
- title_only_fallback_used_count: 13
- title_only_answer_degraded_count: 13
- source_key_collision_detected_count: 6
- selected_document_has_body_span_count: 97
- selected_document_has_non_title_span_count: 87
- candidate_completeness_score_avg: 0.912

## Family-Broken Canonical Metrics
- CB_GENELGE: rows=4, pass=0, materialized=0, corpus_required=4, insufficient_span=4, title_only_degraded=4, collision=2, candidate_avg=0.513
- CB_KARAR: rows=8, pass=6, materialized=6, corpus_required=2, insufficient_span=2, title_only_degraded=2, collision=1, candidate_avg=0.806
- CB_KARARNAME: rows=6, pass=6, materialized=6, corpus_required=0, insufficient_span=0, title_only_degraded=0, collision=0, candidate_avg=1.000
- CB_YONETMELIK: rows=6, pass=4, materialized=6, corpus_required=0, insufficient_span=0, title_only_degraded=0, collision=0, candidate_avg=0.967
- KANUN: rows=21, pass=15, materialized=20, corpus_required=1, insufficient_span=1, title_only_degraded=1, collision=3, candidate_avg=0.957
- KHK: rows=6, pass=6, materialized=5, corpus_required=1, insufficient_span=1, title_only_degraded=1, collision=0, candidate_avg=0.925
- KKY: rows=11, pass=9, materialized=11, corpus_required=0, insufficient_span=0, title_only_degraded=0, collision=0, candidate_avg=0.973
- MULGA: rows=5, pass=0, materialized=5, corpus_required=0, insufficient_span=0, title_only_degraded=0, collision=0, candidate_avg=0.960
- TEBLIGLER: rows=8, pass=6, materialized=5, corpus_required=3, insufficient_span=3, title_only_degraded=3, collision=0, candidate_avg=0.869
- TUZUK: rows=5, pass=2, materialized=4, corpus_required=1, insufficient_span=1, title_only_degraded=1, collision=0, candidate_avg=0.870
- UY: rows=10, pass=10, materialized=10, corpus_required=0, insufficient_span=0, title_only_degraded=0, collision=0, candidate_avg=0.910
- YONETMELIK: rows=10, pass=6, materialized=9, corpus_required=1, insufficient_span=1, title_only_degraded=1, collision=0, candidate_avg=0.935

## Blocker Classification
- routing_family_blockers: 15
- document_identity_blockers: 13
- article_or_span_blockers: 70
- corpus_materialization_blockers: 13
- insufficient_canonical_span_blockers: 13
- unsupported_confident_blockers: 25

## Decision Tree
- diagnostic_acceptance: FAIL
- productization_gate: CLOSED
- fine_tuning_gate: CLOSED
- reason: Full diagnostic can be accepted only as an instrumentation/audit rerun; product/fine-tune gates remain closed until routing, document identity, article/span precision, and corpus materialization blockers clear on stable full-set reruns.

## Diagnostic Checks
- contract_valid=100/100: PASS
- green_lane PASS: PASS
- no API errors/refusals: PASS
- no hallucinated-source regression: PASS
- unsupported confident low: FAIL
- canonical metrics present: PASS
- title-only/insufficient rows classified: PASS
- corpus/materialization blockers surfaced: PASS

## Produced Artifacts
- phase_14_run_summary.md/json
- phase_14_score_summary.md/json
- phase_14_scored.csv
- phase_14_trace_forensics.md/csv
- phase_14_coverage_backlog.md/csv
- phase_14_visibility_truth_audit.md and phase_14_visibility_truth_table.csv
- phase_14_family_routing_audit.md/csv
- phase_14_document_identity_audit.md/csv
- phase_14_article_alignment_audit.md/csv
- phase_14_canonical_span_materialization_audit.md/csv
- phase_14_candidate_completeness_audit.md/csv
- phase_14_source_key_collision_report.csv
- phase_14_phase_comparison.md
- phase_14_green_lane_summary.md/json
