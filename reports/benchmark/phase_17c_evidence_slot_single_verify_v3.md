# Phase 17C Evidence-To-Answer Required Slot Audit

- source_run_dir: `reports/benchmark/runs/20260424T_phase17c_slot_synthesis_single_verify_v3`
- rows: 1
- minimum_answer_facts_present_count: 1/1
- evidence_slot_synthesis_count: 1/1
- avg_evidence_required_slot_value_count: 5.0

## Runtime Completeness
- rubric_sufficient: 1

## Synthesis Reasons
- slot_values_made_visible_from_selected_evidence: 1

## Failure Classes
- missing_required_content_signal: 1
- partial_grounding_only: 1

## Rows
- KANUN-01: min_facts=True, synthesis=True:governing_source | procedure_or_consequence | temporal_validity | current_applicability, slot_values=5, must=2/6, score=9.10, failures=missing_required_content_signal | partial_grounding_only
