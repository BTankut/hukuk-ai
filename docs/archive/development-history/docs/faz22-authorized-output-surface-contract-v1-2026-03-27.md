# FAZ22 Authorized Output Surface Contract v1

## Authorized F Surface

- `F13 = final_mode_mapping_hash`
- `F14 = blocked_reason_set_hash`
- `F15 = final_answer_payload_hash`
- `F16 = response_envelope_hash`
- `F17 = serialized_output_hash`
- `F18 = answer_body_hash`
- `F19 = citation_body_hash`
- `F20 = refusal_body_hash`

## Rules

- `F0..F12` are upstream and immutable for this phase
- first break in `F0..F12` means `surface_breach_regression = true`
- first break outside `F13..F20` means `stage_outside_authorized_output_surface = true`
