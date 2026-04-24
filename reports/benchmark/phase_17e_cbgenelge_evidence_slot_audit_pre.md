# Phase 17C Evidence-To-Answer Required Slot Audit

- source_run_dir: `reports/benchmark/runs/20260424T_phase17e_cbgenelge_smoke_pre`
- rows: 4
- minimum_answer_facts_present_count: 0/4
- evidence_slot_synthesis_count: 1/4
- avg_evidence_required_slot_value_count: 6.0

## Runtime Completeness
- insufficient_both: 3
- legally_aligned_but_partial: 1

## Synthesis Reasons
- no_confident_missing_slot_values: 2
- slot_values_made_visible_from_selected_evidence: 1
- canonical_evidence_gap: 1

## Failure Classes
- missing_required_content_signal: 4
- partial_grounding_only: 4
- missing_gold_document_signal: 3
- wrong_document: 3
- hallucinated_identifier: 3
- insufficient_canonical_span_evidence: 1

## Rows
- CBG-01: min_facts=False, synthesis=False:-, slot_values=6, must=0/2, score=3.25, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- CBG-02: min_facts=False, synthesis=True:document_selection_reason | current_applicability, slot_values=6, must=0/3, score=3.25, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- CBG-03: min_facts=False, synthesis=False:-, slot_values=6, must=0/3, score=3.25, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- CBG-04: min_facts=False, synthesis=False:-, slot_values=6, must=0/3, score=7.90, failures=missing_required_content_signal | partial_grounding_only | insufficient_canonical_span_evidence
