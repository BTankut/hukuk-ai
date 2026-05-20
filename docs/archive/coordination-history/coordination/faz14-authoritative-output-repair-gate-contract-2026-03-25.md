# FAZ14 Authoritative Output Repair Gate Contract

Tarih: 2026-03-25

Targeted gate:
- `WP-4A` yalniz sabit 6 satirlik `v3-170` frontier uzerinde kosar.
- `WP-4A PASS` icin tum mismatch alanlari `0`, `runtime_error_count = 0`, `mismatch_count = 0`, `changed_field_outside_contract_count = 0` olmali.

Full-family gate:
- `WP-5A` yalniz `WP-4A PASS` ise acilir.
- `WP-5A PASS` icin tum ailelerde:
  - `mismatch_count = 0`
  - tum mismatch alanlari `0`
  - `family_metric_delta_zero = true`
  - `runtime_error_count = 0`
- `v3-170` icin su upstream authority alanlari ayrica `0` kalmak zorundadir:
  - `normalized_request_hash_mismatch_count`
  - `model_request_payload_hash_mismatch_count`
  - `generation_contract_hash_mismatch_count`
  - `preprojection_anchor_mismatch_count`

Localization gate:
- `WP-6` yalniz `WP-4A FAIL` veya `WP-5A FAIL` ise acilir.
- `unexplained_count > 0` ise `WP-6 FAIL`.
- `first_divergence_stage ∈ {O0, O1, O2, O3, O4, O5, O8}` ise `repair_surface_breach`.
