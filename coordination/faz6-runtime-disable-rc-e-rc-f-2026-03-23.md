# FAZ 6 Runtime Disable RC-E RC-F

Tarih: 2026-03-23

Referans:
- [FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md)
- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)

## Runtime Karari

Default/runtime path acik bicimde `RC-D` davranisina donduruldu.

## Uygulanan Ayrim

- public runtime entrypoint:
  - `harden_answer(...)`
  - her zaman `recovery_profile = "rc_d"`
- diagnostic-only entrypoint:
  - `harden_answer_diagnostic(...)`
  - yalniz offline replay ve historical candidate rerun icin kullanilir

## RC-E ve RC-F Durumu

`RC-E` ve `RC-F` davranis kodu default path'te aktif degildir.

Bu profiller yalniz su offline replay kutuphanelerinde korunur:

- [rc_e_offline_lib.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/rc_e_offline_lib.py)
- [rc_f_offline_lib.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz5/rc_f_offline_lib.py)

Bu kutuphaneler:

- runtime serving path'e bagli degildir
- offline diagnostic replay icin `harden_answer_diagnostic(...)` kullanir
- default davranisi degistirmez

## Smoke Parity Notu

FAZ 6 boyunca hedefli testler `RC-D` runtime lock ve diagnostic-only ayrimini dogruladi:

- `api-gateway/tests/test_faz2a_hardening.py`
- `api-gateway/tests/test_chat_router.py`

Sonuc:

- runtime path `RC-D`
- `RC-E` / `RC-F` diagnostic-only
