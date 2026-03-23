# FAZ 2B Law-Scope Gate v2 Spec

Tarih: 2026-03-23

## Sabit Scope Sınıfları

- `single_law_high_conf`
- `multi_law`
- `ambiguous`

## Atama Kuralı

- tek açık kanun sinyali varsa: `single_law_high_conf`
- iki veya daha fazla açık kanun sinyali varsa: `multi_law`
- diğer tüm durumlar: `ambiguous`

## Davranış

### `single_law_high_conf`

- beklenen kanun kapsamı dışındaki kaynaklar final citation listesinden düşürülür
- beklenen kapsamda geçerli primary source kalmazsa dış mod `refusal`
- `final_reason=law_scope_mismatch`

### `multi_law`

- whitelist içindeki kaynaklarla cevap teslim edilir
- `law_scope` kullanılan tüm kanunları listeler
- scope gerekçesiyle blok yapılmaz

### `ambiguous`

- scope gerekçesiyle doğrudan blok yapılmaz
- tek resolved law scope oluşursa cevap devam eder
- oluşmazsa dış mod `refusal`
- `final_reason=insufficient_supported_evidence`

## Kod Yüzeyi

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
  - `build_law_scope_signal`
  - `apply_law_scope_validation`
  - `harden_answer`

## Doğrulama

- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz2a_hardening.py api-gateway/tests/test_chat_router.py -q`
