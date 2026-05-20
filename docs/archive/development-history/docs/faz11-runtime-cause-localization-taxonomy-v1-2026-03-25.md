# FAZ11 Runtime Cause Localization Taxonomy v1

Tarih: 2026-03-25

## Izinli Primary Reason Kumesi

- `process_reuse_state_leak`
- `request_reset_missing`
- `session_namespace_leak`
- `cache_namespace_bleed`
- `post_payload_context_shadow`
- `release_control_bind_effect`
- `unexplained`

## Atama Sirasi

1. mismatch `C1`'de kayboluyorsa `process_reuse_state_leak`
2. aksi halde mismatch `C2`'de kayboluyorsa `request_reset_missing`
3. aksi halde mismatch `C3`'te kayboluyorsa `session_namespace_leak`
4. aksi halde mismatch `C4`'te kayboluyorsa `cache_namespace_bleed`
5. aksi halde mismatch `C5`'te kayboluyorsa `post_payload_context_shadow`
6. aksi halde mismatch `C6`'da kayboluyorsa `release_control_bind_effect`
7. hicbirinde kaybolmuyorsa `unexplained`

Bu liste disinda primary reason kullanilmayacak.
