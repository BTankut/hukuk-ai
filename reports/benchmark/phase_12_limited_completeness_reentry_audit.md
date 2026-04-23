# Phase 12 Limited Completeness Re-entry Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full`
- rows_analyzed: 100
- evidence_slot_reentry_count: 6
- minimum_answer_facts_present_count: 80
- avg_required_fact_coverage_score: 0.943

## Re-entry Rows
- CBG-01: family=CB_GENELGE, task=precise_retrieval, slots=scenario_applicability, degrade=missing_required_fact_slots:document_selection_reason, score=3.25
- KANUN-12: family=KANUN, task=document_selection, slots=hierarchy_or_conflict_rule, degrade=complete_enough, score=8.65
- KANUN-15: family=KANUN, task=scenario_applicability, slots=scenario_applicability, degrade=complete_enough, score=6.85
- KANUN-17: family=KANUN, task=document_selection, slots=scenario_applicability, degrade=complete_enough, score=8.65
- UY-03: family=UY, task=scenario_applicability, slots=scenario_applicability, degrade=complete_enough, score=9.19
- YON-01: family=YONETMELIK, task=precise_retrieval, slots=procedure_or_consequence, degrade=complete_enough, score=5.75

## Remaining Degrade Reasons
- complete_enough: 80
- missing_required_fact_slots:document_selection_reason: 11
- missing_required_fact_slots:document_selection_reason,hierarchy_or_conflict_rule: 4
- missing_required_fact_slots:hierarchy_or_conflict_rule: 4
- no_answer: 1
