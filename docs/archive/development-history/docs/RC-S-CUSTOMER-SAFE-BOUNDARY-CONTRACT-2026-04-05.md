# RC-S Customer Safe Boundary Contract 2026-04-05

## Data Boundary

- customer_data_allowed = `false`
- private_documents_allowed = `false`
- YIM_allowed = `false`
- external_ad_hoc_content_allowed = `false`
- local_only_data_handling_required = `true`
- internet_dependency_allowed = `false`

## Product Surface Boundary

- customer_pilot_authorized = `false`
- production_cutover_authorized = `false`
- appliance_bundle_authorized = `false`
- implementation_authorized = `false`

## User-Facing Safety Boundary

- human_review_required = `true`
- citation_visible_required = `true`
- refusal_visible_required = `true`
- accepted_expanded_source_set_exact = `[TMK core corpus, TCK, HMK, CMK, TTK, İK]`
- excluded_source_classes = `[YİM, customer/private documents, external internet-derived ad hoc content]`
