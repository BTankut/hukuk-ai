# Phase 10B Completeness Calibration

- source_run_dir: `reports/benchmark/runs/20260422T204628Z_phase11_full`
- rows_analyzed: 100

## Task-Type Must-Have Fact Slots
- compliance_checklist: governing_source | article_or_span | procedure_or_consequence | exception_or_limitation
- current_update: governing_source | exact_source_identity | temporal_validity
- document_selection: governing_source | exact_source_identity | document_selection_reason
- exception_analysis: governing_source | article_or_span | exception_or_limitation | scenario_applicability
- hierarchy_conflict: governing_source | exact_source_identity | hierarchy_or_conflict_rule | scenario_applicability
- precise_retrieval: governing_source | exact_source_identity | article_or_span
- scenario_applicability: governing_source | exact_source_identity | scenario_applicability | procedure_or_consequence
- temporal_validity: governing_source | exact_source_identity | temporal_validity

## Rubric-Aligned Completeness Classes
- structurally_full_but_legally_misaligned: 68
- insufficient_both: 29
- rubric_sufficient: 3

## Private-Rubric Failure Signals
- missing_required_content_signal: 97
- partial_grounding_only: 97

## Completeness Class by Task Type
- compliance_checklist: insufficient_both=5, structurally_full_but_legally_misaligned=3
- current_update: insufficient_both=2, structurally_full_but_legally_misaligned=3
- document_selection: insufficient_both=8, rubric_sufficient=3, structurally_full_but_legally_misaligned=25
- exception_analysis: structurally_full_but_legally_misaligned=2
- hierarchy_conflict: insufficient_both=3, structurally_full_but_legally_misaligned=5
- precise_retrieval: insufficient_both=4, structurally_full_but_legally_misaligned=6
- scenario_applicability: insufficient_both=4, structurally_full_but_legally_misaligned=8
- temporal_validity: insufficient_both=3, structurally_full_but_legally_misaligned=16

## Calibration Interpretation
- `structurally_full_but_legally_misaligned` means runtime structural completeness passed, but private-rubric required content or grounding still failed.
- `rubric_sufficient` is the only class that should map to `complete_enough` after runtime gating.
- The calibration is generic by task type and fact slot; it does not encode any benchmark QID-specific rule.
