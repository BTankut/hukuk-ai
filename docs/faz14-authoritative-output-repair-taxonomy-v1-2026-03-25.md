# FAZ14 Authoritative Output Repair Taxonomy v1

Tarih: 2026-03-25

Izinli localized reason set:

- `final_mode_mapping_delta`
- `blocked_reason_projection_delta`
- `response_envelope_projection_delta`

Fail reason set:

- `repair_surface_breach`
- `unexplained_authoritative_output_repair_drift`

Yorum:

- `final_mode_mapping_delta` = ilk divergence `final_mode_mapping_hash`
- `blocked_reason_projection_delta` = ilk divergence `blocked_reason_set_hash`
- `response_envelope_projection_delta` = ilk divergence `response_envelope_hash` veya `serialized_output_hash`
- `{O0, O1, O2, O3, O4, O5, O8}` aileleri = `repair_surface_breach`
