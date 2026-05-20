# FAZ16 Official Implementation Plan

Tarih: 2026-03-25

Referans:
- `docs/FAZ16-ROTASYON-RC-M-REPLACEMENT-BUILD-SURFACE-ISOLATION-GATE-TALIMATI-2026-03-25.md`
- `docs/FAZ15-RC-L-DISCARD-VE-REPAIR-SURFACE-BREACH-FORENSICS-RAPORU-2026-03-25.md`

## Resmi Amaç

- `RC-L` kalici discard olarak kalacak.
- `RC-J` frozen authoritative diagnostic referans olacak.
- `RC-M`, yalniz frozen `RC-J` uzerinden replacement isolation candidate olarak insa edilecek.
- Bu faz yalniz `replacement build-surface isolation` karari uretecek.

## Zorunlu Sira

1. `WP-1` refreeze ve authority/build contract artefact'larini yaz.
2. `WP-2` current `RC-G vs RC-J` authority snapshot'i tek kosuda recapture et.
3. `WP-3` `RC-M` manifest ve build proof uret.
4. `WP-4` targeted 6 gate al.
5. `WP-5` breach sentinel-16 gate al.
6. `WP-6` full-family isolation gate al.
7. `WP-7` reconciliation, next official work ve tek resmi karar yaz.

## Teknik Yurutme

- `RC-G vs RC-J` current authority recapture icin FAZ15 control collector zinciri reuse edilecek.
- `RC-M` lane, frozen `RC-J` runtime-visible surface'ini koruyacak sekilde ayri runner ile acilacak.
- `RC-J vs RC-M` isolation raporlari FAZ14 diff-report builder'i uzerinden, `RC-G vs RC-M` replacement raporlari FAZ13 authoritative parity builder'i uzerinden uretilecek.
- Deterministic `breach_sentinel_16` FAZ15 breach-first-divergence tablosundan turetilecek.

## Faz Siniri

- retrieval degismeyecek
- prompt degismeyecek
- model degismeyecek
- evaluator degismeyecek
- release-controls mantigi degismeyecek
- serving default degismeyecek

