# FAZ14 Final-Mode Diff Surface Contract v1

Tarih: 2026-03-25

`RC-J -> RC-L` diff containment kuralı:

- `allowed_changed_field_set ⊆ {final_mode_mapping_hash, blocked_reason_set_hash, response_envelope_hash, serialized_output_hash}`

Bu küme dışında değişen herhangi bir alan:

- `repair_surface_breach`
- `WP-4A auto fail`

olarak kabul edilir.

Kapanış kuralı:

- `final_mode_mapping_hash`, `blocked_reason_set_hash`, `response_envelope_hash`, `serialized_output_hash` dışında hiçbir hash veya body alanı değişmeyecektir.
