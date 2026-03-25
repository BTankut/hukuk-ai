# FAZ14 Authoritative Output Repair Gate Contract

Tarih: 2026-03-25

## Frontier

- targeted repair gate yalnız `TBK-051, TBK-054, TBK-055, TBK-057, TBK-058, TBK-061`
- ordinals = `1, 4, 5, 7, 8, 11`

## Upstream Immutability

Bu alanlar targeted ve full-family gate boyunca sıfır mismatch kalacaktır:

- `normalized_request_hash`
- `model_request_payload_hash`
- `generation_contract_hash`
- `preprojection_anchor_hash`
- `cited_projection_hash`
- `citation_set_projection_hash`
- `final_answer_payload_hash`
- `answer_body_hash`
- `citation_body_hash`
- `refusal_body_hash`

## Allowed Changed Field Set

- `final_mode_mapping_hash`
- `blocked_reason_set_hash`
- `response_envelope_hash`
- `serialized_output_hash`

## Targeted Gate Kuralı

`WP-4A = PASS` ancak şu şartlarla mümkündür:

- tüm mismatch sayaçları `0`
- `runtime_error_count = 0`
- `mismatch_count = 0`
- `changed_field_outside_contract_count = 0`

## Full-Family Gate Kuralı

`WP-5A = PASS` ancak tüm ailelerde:

- tüm mismatch alanları `0`
- `mismatch_count = 0`
- `family_metric_delta_zero = true`

## Failure Localization Kuralı

- `first_divergence_stage ∈ {O0, O1, O2, O3, O4, O5, O8}` ise `repair_surface_breach`
- `unexplained_count > 0` ise `WP-6 = FAIL`
