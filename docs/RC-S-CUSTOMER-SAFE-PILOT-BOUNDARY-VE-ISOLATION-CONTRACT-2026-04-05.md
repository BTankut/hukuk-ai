# RC-S CUSTOMER-SAFE PILOT BOUNDARY VE ISOLATION CONTRACT 2026-04-05

## Boundary Flags

- `answer_path_changed = false`
- `model_changed = false`
- `prompt_changed = false`
- `retrieval_logic_changed = false`
- `reranker_changed = false`
- `guardrail_changed = false`
- `release_controls_topology_changed = false`

## Data Boundary Flags

- `customer_data_allowed_in_this_phase = false`
- `private_documents_allowed = false`
- `YIM_allowed = false`
- `external_ad_hoc_content_allowed = false`
- `internet_dependency_allowed = false`
- `customer_case_input_allowed_in_this_phase = false`

## Pilot Authorization Boundary

- `real_customer_pilot_authorized_in_this_phase = false`
- `pilot_execution_authorized_in_this_phase = false`
- `production_cutover_authorized_in_this_phase = false`
- `field_rollout_authorized_in_this_phase = false`

## Isolation Hükmü

- Customer-safe pilot gate, gerçek customer pilotu açmaz.
- Bu fazda yalnız policy, boundary ve safety exact olarak bağlanır.
- Runtime, retrieval ve productization topology frozen kalır.
