# Phase 14 Candidate Completeness Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- rows_analyzed: 100
- avg_candidate_completeness_score: 0.912
- avg_required_fact_coverage_score: 0.882
- minimum_answer_facts_present_count: 75
- evidence_slot_reentry_count: 8

## Completeness Degrade Reason
- complete_enough: 75
- insufficient_canonical_span_evidence: 13
- missing_required_fact_slots:document_selection_reason: 7
- missing_required_fact_slots:hierarchy_or_conflict_rule: 3
- no_answer: 2

## Runtime Rubric-Aligned Completeness Class
- rubric_sufficient: 75
- legally_aligned_but_partial: 12
- structurally_full_but_legally_misaligned: 10
- insufficient_both: 3

## Task Type Answer Template
- direct: 33
- comparison_or_temporal: 27
- procedure: 24
- condition: 11
- exception: 5

## Lowest Completeness Rows
- CBG-04: expected=CB_GENELGE, task=temporal_validity, candidate=0.2, fact_coverage=0.592, degrade=insufficient_canonical_span_evidence, missing_slots=document_selection_reason | temporal_validity | hierarchy_or_conflict_rule, score=2.50
- CBKAR-08: expected=CB_KARAR, task=temporal_validity, candidate=0.2, fact_coverage=0.867, degrade=insufficient_canonical_span_evidence, missing_slots=none, score=6.80
- KANUN-06: expected=KANUN, task=precise_retrieval, candidate=0.3, fact_coverage=0.067, degrade=insufficient_canonical_span_evidence, missing_slots=result_or_holding | governing_source | hierarchy_or_conflict_rule, score=7.15
- CBG-02: expected=CB_GENELGE, task=compliance_checklist, candidate=0.55, fact_coverage=0.729, degrade=insufficient_canonical_span_evidence, missing_slots=document_selection_reason, score=3.25
- TEB-01: expected=TEBLIGLER, task=current_update, candidate=0.65, fact_coverage=0.867, degrade=insufficient_canonical_span_evidence, missing_slots=none, score=2.95
- CBG-01: expected=CB_GENELGE, task=precise_retrieval, candidate=0.65, fact_coverage=0.683, degrade=insufficient_canonical_span_evidence, missing_slots=document_selection_reason | scenario_applicability, score=3.25
- CBG-03: expected=CB_GENELGE, task=compliance_checklist, candidate=0.65, fact_coverage=0.647, degrade=insufficient_canonical_span_evidence, missing_slots=document_selection_reason | scenario_applicability, score=3.25
- TUZUK-05: expected=TUZUK, task=hierarchy_conflict, candidate=0.65, fact_coverage=0.867, degrade=insufficient_canonical_span_evidence, missing_slots=none, score=3.25
- TEB-03: expected=TEBLIGLER, task=document_selection, candidate=0.65, fact_coverage=0.867, degrade=insufficient_canonical_span_evidence, missing_slots=none, score=7.15
- TEB-04: expected=TEBLIGLER, task=temporal_validity, candidate=0.65, fact_coverage=0.757, degrade=insufficient_canonical_span_evidence, missing_slots=document_selection_reason, score=7.25
- YON-04: expected=YONETMELIK, task=compliance_checklist, candidate=0.65, fact_coverage=0.867, degrade=insufficient_canonical_span_evidence, missing_slots=none, score=7.55
- CBKAR-07: expected=CB_KARAR, task=hierarchy_conflict, candidate=0.65, fact_coverage=0.867, degrade=insufficient_canonical_span_evidence, missing_slots=none, score=8.65
- KHK-05: expected=KHK, task=document_selection, candidate=0.65, fact_coverage=0.9, degrade=insufficient_canonical_span_evidence, missing_slots=none, score=9.10
- TUZUK-02: expected=TUZUK, task=precise_retrieval, candidate=0.8, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=9.32
- KANUN-04: expected=KANUN, task=compliance_checklist, candidate=0.9, fact_coverage=0.757, degrade=missing_required_fact_slots:document_selection_reason, missing_slots=document_selection_reason, score=1.45
- TUZUK-04: expected=TUZUK, task=temporal_validity, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=2.50
- YON-06: expected=YONETMELIK, task=document_selection, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=3.59
- MULGA-05: expected=MULGA, task=temporal_validity, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=4.25
- MULGA-01: expected=MULGA, task=temporal_validity, candidate=0.9, fact_coverage=0.9, degrade=complete_enough, missing_slots=none, score=4.90
- YON-08: expected=YONETMELIK, task=current_update, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=5.45
- CBKAR-03: expected=CB_KARAR, task=temporal_validity, candidate=0.9, fact_coverage=0.757, degrade=missing_required_fact_slots:hierarchy_or_conflict_rule, missing_slots=hierarchy_or_conflict_rule, score=6.80
- KKY-04: expected=KKY, task=document_selection, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=6.85
- KHK-03: expected=KHK, task=temporal_validity, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=7.25
- KKY-05: expected=KKY, task=document_selection, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=7.55
- YON-01: expected=YONETMELIK, task=precise_retrieval, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=7.55
- CBY-01: expected=CB_YONETMELIK, task=document_selection, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=7.75
- CBKAR-01: expected=CB_KARAR, task=current_update, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=8.58
- UY-06: expected=UY, task=hierarchy_conflict, candidate=0.9, fact_coverage=0.775, degrade=missing_required_fact_slots:hierarchy_or_conflict_rule, missing_slots=hierarchy_or_conflict_rule, score=8.65
- CBY-03: expected=CB_YONETMELIK, task=temporal_validity, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=8.80
- UY-08: expected=UY, task=temporal_validity, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=8.80
- KANUN-13: expected=KANUN, task=compliance_checklist, candidate=0.9, fact_coverage=0.9, degrade=complete_enough, missing_slots=none, score=8.92
- UY-03: expected=UY, task=scenario_applicability, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=8.92
- UY-02: expected=UY, task=scenario_applicability, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=8.99
- CBKAR-04: expected=CB_KARAR, task=precise_retrieval, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=9.10
- KKY-07: expected=KKY, task=document_selection, candidate=0.9, fact_coverage=0.867, degrade=complete_enough, missing_slots=none, score=9.10
