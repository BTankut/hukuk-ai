# RC-S CUSTOMER-SAFE PILOT ALLOWLIST VE ADMISSION CONTRACT 2026-04-05

## Admission Flags

- `allowlist_required = true`
- `named_operator_ownership_required = true`
- `real_customer_identity_admission_required = true`
- `unlisted_user_admission_allowed = false`
- `anonymous_access_allowed = false`
- `shared_pool_execution_allowed = false`

## Ownership Rules

- Her olası müşteri-güvenli pilot oturumu named operator ownership taşımalıdır.
- Allowlist dışı hiçbir kullanıcı veya vaka bu fazda kabul edilmez.
- Admission kaydı olmadan hiçbir execution başlamaz.

## Gate Boundary

- Bu faz `pilot gate` olduğu için admission contract yazılır, fakat fiili admission açılmaz.
- `pilot_execution_authorized_in_this_phase = false` hükmü geçerlidir.
