# Phase 17C Evidence-To-Answer Required Slot Audit

- source_run_dir: `reports/benchmark/runs/20260424T_phase17e_cbgenelge_smoke_post5`
- rows: 4
- minimum_answer_facts_present_count: 2/4
- evidence_slot_synthesis_count: 3/4
- avg_evidence_required_slot_value_count: 6.25

## Runtime Completeness
- insufficient_both: 2
- rubric_sufficient: 2

## Synthesis Reasons
- slot_values_made_visible_from_selected_evidence: 3
- no_confident_missing_slot_values: 1

## Failure Classes
- missing_required_content_signal: 4
- partial_grounding_only: 4
- missing_gold_document_signal: 2
- wrong_document: 2
- hallucinated_identifier: 2

## Rows
- CBG-01: min_facts=False, synthesis=False:-, slot_values=6, must=0/2, score=3.25, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- CBG-02: min_facts=False, synthesis=True:document_selection_reason | current_applicability, slot_values=6, must=0/3, score=3.25, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- CBG-03: min_facts=True, synthesis=True:scenario_applicability | temporal_validity | current_applicability, slot_values=7, must=0/3, score=8.65, failures=missing_required_content_signal | partial_grounding_only
- CBG-04: min_facts=True, synthesis=True:current_applicability, slot_values=6, must=1/3, score=8.35, failures=missing_required_content_signal | partial_grounding_only
