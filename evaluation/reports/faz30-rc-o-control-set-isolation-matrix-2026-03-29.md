# FAZ30 RC-O Control-Set Isolation Matrix

- control_set_row_count = `9`
- source_basis = `faz27_inherited_control_surface_plus_faz30_current_twin_capture`
- minimal_failing_control_set = `none`
- dominant_interaction_class = `boundary_pack_orchestration_runtime_mutation`
- single_control_root_cause_found = `false`
- interaction_root_cause_found = `false`
- unexplained_count = `0`

| control_set_id | source | record_count | mismatch_count | runtime_error_count | first_runtime_error_stage | dominant_primary_reason | capture_stability_match |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C0 | inherited_faz27_effective_control_surface | 190 | 159 | 0 |  | multi_control_interaction_runtime_mutation | true |
| C1 | inherited_faz27_b4 | 190 | 159 | 0 |  | multi_control_interaction_runtime_mutation | true |
| C2 | inferred_faz27_tokenizer_non_causal | 190 | 159 | 0 |  | multi_control_interaction_runtime_mutation | true |
| C3 | inferred_faz27_api_non_causal | 190 | 159 | 0 |  | multi_control_interaction_runtime_mutation | true |
| C4 | inferred_faz29_smoke_non_causal | 190 | 159 | 0 |  | multi_control_interaction_runtime_mutation | true |
| C5 | inherited_faz27_b5 | 190 | 159 | 0 |  | multi_control_interaction_runtime_mutation | true |
| C6 | inferred_faz27_pii_smoke_non_causal | 190 | 159 | 0 |  | multi_control_interaction_runtime_mutation | true |
| C7 | inferred_faz27_api_smoke_non_causal | 190 | 159 | 0 |  | multi_control_interaction_runtime_mutation | true |
| C8 | current_faz30_rc_o_twin_capture | 190 | 156 | 0 |  | boundary_pack_orchestration_runtime_mutation | false |
