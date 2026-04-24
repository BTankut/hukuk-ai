# Phase 17C Evidence-To-Answer Required Slot Audit

- source_run_dir: `reports/benchmark/runs/20260424T_phase17d_mulga_smoke_post_v5`
- rows: 5
- minimum_answer_facts_present_count: 5/5
- evidence_slot_synthesis_count: 5/5
- avg_evidence_required_slot_value_count: 5.0

## Runtime Completeness
- rubric_sufficient: 5

## Synthesis Reasons
- missing_slots_filled_from_selected_evidence: 4
- slot_values_made_visible_from_selected_evidence: 1

## Failure Classes
- missing_required_content_signal: 5
- partial_grounding_only: 5
- wrong_article: 2
- missing_gold_document_signal: 1
- wrong_document: 1
- hallucinated_identifier: 1

## Rows
- MULGA-01: min_facts=True, synthesis=True:result_or_holding | governing_source | temporal_validity | current_applicability, slot_values=4, must=1/3, score=6.43, failures=missing_required_content_signal | wrong_article | partial_grounding_only
- MULGA-02: min_facts=True, synthesis=True:result_or_holding | governing_source | temporal_validity | current_applicability, slot_values=6, must=0/3, score=8.65, failures=missing_required_content_signal | partial_grounding_only
- MULGA-03: min_facts=True, synthesis=True:result_or_holding | governing_source | temporal_validity | current_applicability, slot_values=5, must=0/3, score=7.55, failures=missing_required_content_signal | partial_grounding_only
- MULGA-04: min_facts=True, synthesis=True:governing_source | article_or_span | current_applicability | transition_or_replacement_rule, slot_values=6, must=1/2, score=8.22, failures=missing_required_content_signal | partial_grounding_only
- MULGA-05: min_facts=True, synthesis=True:result_or_holding | governing_source | temporal_validity | current_applicability, slot_values=4, must=0/3, score=2.50, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | wrong_article | hallucinated_identifier | partial_grounding_only
