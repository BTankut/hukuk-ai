# FAZ 3 Final-Mode Mapping v3 Delta

Tarih: 2026-03-23

Referans:
- [faz3-final-mode-mapping-v3-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz3-final-mode-mapping-v3-spec-2026-03-23.md)
- [faz3-selective-claim-binding-v3-delta-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz3-selective-claim-binding-v3-delta-2026-03-23.md)

## Delta

Final-mode mapping `v3` artik claim-binding sonucu ile deterministik sekilde calisiyor.

Kurallar:

- hard-fail -> `refusal`
- hard-fail yok + kept `0` -> `refusal`
- hard-fail yok + kept `>=1` + dropped `0` -> `answer`
- hard-fail yok + kept `>=1` + dropped `>=1` -> `partial`

## Korunan Yuzey

- internal `blocked` dis API'ye sizmiyor
- external mode kumesi hala yalniz `answer`, `partial`, `refusal`
- whitelist / temporal / law-scope hard-fail'leri `partial`e dusurulmuyor

## Kod Yuzeyi

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)

Degisen ana seam:

- `apply_final_mode_mapping_v3`
- refusal body artik bos string
- answer/partial citation listesi yalniz kept claim-unit'lerden geliyor

## Focused Proof

Gecen testler:

- [test_faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/tests/test_faz2a_hardening.py)
- [test_chat_router.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/tests/test_chat_router.py)

Kanitan ana noktalar:

- `partial` router cikisi bozulmuyor
- broad basic request yanlis refusal'a dusmuyor
- hard-fail refusal'larda body bos kaliyor
- public/internal mode uyumu korunuyor
