# FAZ13 Official Implementation Plan

Tarih: 2026-03-25

Referans:
- `docs/FAZ13-ROTASYON-RC-J-OUTPUT-PARITY-AUTHORITY-FORENSICS-RECAPTURE-TALIMATI-2026-03-25.md`
- `docs/FAZ12-RC-J-OUTPUT-PARITY-REOPEN-RAPORU-2026-03-25.md`
- `coordination/faz11-wp3-gate-2026-03-25.md`

## Amaç

Bu fazın tek işi `RC-G` ile `RC-J` arasında full-family output parity authority hakikatini yeniden toplamaktır. Drift kapanırsa faz `PASS` ile kapanacaktır. Drift kalırsa yalnız authoritative mismatch ordinals üzerinden frontier ve localization üretilecektir.

## Uygulama Sırası

1. `WP-1`: freeze ve authority run contract
2. `WP-2`: authority schema, taxonomy ve authoritative frontier contract
3. `WP-3`: `faz1-50`, `v2-95`, `v3-170` authoritative output parity toplama / replay
4. `WP-4`: yalnız `WP-3A = FAIL` ise authoritative frontier ve first-divergence localization
5. `WP-5`: resmi steering kararı ve tek-cümle faz kapanışı

## Uygulama Notları

- `faz1-50` ve `v2-95` serial authoritative recapture ile yürütülecek.
- `v3-170` için yeni upstream authority toplanmayacak; FAZ11 authority tabanı üstünde replay açılacak.
- Yeni candidate build edilmeyecek.
- Retrieval, prompt, guardrail, answer-path, serializer ve release-controls yüzeyi değiştirilmeyecek.
