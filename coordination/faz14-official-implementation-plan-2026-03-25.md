# FAZ14 Official Implementation Plan

Tarih: 2026-03-25

Referans:
- `docs/FAZ14-ROTASYON-RC-L-AUTHORITATIVE-OUTPUT-PARITY-REPAIR-GATE-TALIMATI-2026-03-25.md`
- `docs/FAZ13-OUTPUT-PARITY-AUTHORITY-FORENSICS-RECAPTURE-RAPORU-2026-03-25.md`
- `coordination/faz13-output-parity-authoritative-frontier-pack-2026-03-25.json`

## Amaç

Bu fazın tek işi, FAZ13'te lokalize edilen 6 adet `v3-170` authoritative drift kaydını yalnız izinli `final_mode_mapping -> blocked_reason_set -> response_envelope` zinciri içinde onarmaktır.

## Uygulama Sırası

1. `WP-1`: `RC-G` refreeze, `RC-J` diagnostic refreeze, `RC-L` build contract
2. `WP-2`: repair schema, taxonomy ve diff-surface contract
3. `WP-3`: `RC-L` build, manifest ve answer-path delta doğrulaması
4. `WP-4A`: yalnız 6 kayıtlık authoritative targeted repair gate
5. `WP-5A`: yalnız `WP-4A = PASS` ise `faz1-50`, `v2-95`, `v3-170` full-family authoritative parity reopen
6. `WP-6`: yalnız `WP-4A` veya `WP-5A` fail ise localized reconciliation
7. `WP-7`: resmi steering kararı ve tek cümle kapanış

## Uygulama Notları

- `RC-G` üzerine patch atılmayacak; resmi referans mevcut frozen authoritative report'lar olacak.
- `RC-J` yerinde patch edilmeyecek; yalnız freeze ve forensic kaynak olarak kalacak.
- `RC-L`, `RC-J` frozen manifestinden türetilecek tek yetkili repair adayıdır.
- Runtime code değişikliği yalnız `api-gateway/src/routers/chat.py` içindeki `v3_runtime_parity_trace` response-envelope projection yüzeyinde tutulacaktır.
- Retrieval, prompt, claim binding, source election, citation semantics, request canonicalization ve evaluator logic değiştirilmeyecektir.
