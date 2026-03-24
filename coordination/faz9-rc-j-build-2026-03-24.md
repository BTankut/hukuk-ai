# FAZ9 RC-J Build

Tarih: 2026-03-24

## RC-J Tanimi

- taban: `RC-G`
- release-controls kapsamı: retained
- model-visible parity onarimi: applied
- varsayilan serving lane: degil

## Runtime

- lane: `rc_j`
- clean gateway port: `8118`
- clean tunnel port: `30128`

## Gecen Kapilar

- `TBK-005` witness replay: pass
- `faz1 witness pack A preprojection gate`: pass
  - `normalized_request_hash_mismatch_count = 0`
  - `model_request_payload_hash_mismatch_count = 0`
  - `generation_contract_hash_mismatch_count = 0`
  - `preprojection_hash_mismatch_count = 0`
  - `raw_answer_hash_mismatch_count = 0`
  - `parity_runtime_error_count = 0`
- `sentinel-12 preprojection gate`: pass
  - tum mismatch sayaclari `0`

## Acik Is

- `WP-8 full-family preprojection gate reopen`
- `WP-9 full-family output parity gate reopen`
- `WP-10 release-controls retention revalidation`
- `WP-11 cutover rehearsal / rollback proof reopen`
