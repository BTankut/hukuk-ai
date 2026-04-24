# Phase 17C Evidence-To-Answer Required Slot Audit

- source_run_dir: `reports/benchmark/runs/20260424T_phase17d_mulga_smoke_pre`
- rows: 5
- minimum_answer_facts_present_count: 4/5
- evidence_slot_synthesis_count: 0/5
- avg_evidence_required_slot_value_count: 3.8

## Runtime Completeness
- rubric_sufficient: 4
- insufficient_both: 1

## Synthesis Reasons
- final_mode_not_answer_or_no_contract: 5

## Failure Classes
- missing_required_content_signal: 5
- partial_grounding_only: 5
- missing_gold_document_signal: 4
- wrong_document: 4
- hallucinated_identifier: 3
- wrong_article: 2

## Rows
- MULGA-01: min_facts=True, synthesis=False:-, slot_values=4, must=1/3, score=6.43, failures=missing_required_content_signal | wrong_article | partial_grounding_only
- MULGA-02: min_facts=True, synthesis=False:-, slot_values=6, must=0/3, score=3.25, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- MULGA-03: min_facts=True, synthesis=False:-, slot_values=5, must=0/3, score=3.25, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- MULGA-04: min_facts=False, synthesis=False:-, slot_values=0, must=0/2, score=3.25, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | partial_grounding_only
- MULGA-05: min_facts=True, synthesis=False:-, slot_values=4, must=0/3, score=2.50, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | wrong_article | hallucinated_identifier | partial_grounding_only
