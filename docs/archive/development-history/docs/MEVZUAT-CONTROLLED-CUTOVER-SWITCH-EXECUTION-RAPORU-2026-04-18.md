# Mevzuat Controlled Cutover Switch Execution Raporu 2026-04-18

## Switch Execution Fields
- `switch_started = true`
- `switch_completed = true`
- `active_runtime_before = mevzuat_e5_shadow`
- `active_runtime_after = mevzuat_faz1_shadow_20260416`
- `switch_error_count = 0`
- `rollback_invoked = true`
- `backout_invoked = false`

## Observed Execution Trace
- Candidate binding ile baseline gateway `127.0.0.1:8000` uzerinde yeniden baslatildi.
- Gateway log'unda `collection=mevzuat_faz1_shadow_20260416` ve `entities=349191` teyit edildi.
- Post-switch health endpoint `200 OK` dondu.
- Serving smoke `POST /v1/chat/completions` cagrisi `500` ile kirdi.
- Smoke kirilimi sonrasinda rollback tetiklendi.

## Rollback Outcome
- `final_active_runtime_restored = true`
- `final_active_runtime_collection = mevzuat_e5_shadow`
- Rollback sonrasi baseline gateway yeniden baslatildi.
- Gateway log'unda `collection=mevzuat_e5_shadow` ve `entities=12923` teyit edildi.
