# FAZ12 Official Implementation Plan

Tarih: 2026-03-25

Referans:
- `docs/FAZ12-ROTASYON-RC-J-OUTPUT-PARITY-REOPEN-TALIMATI-2026-03-25.md`
- `docs/FAZ11-NON-REPRODUCIBLE-FRONTIER-RESOLUTION-VE-V3-170-FIRST-RUN-AUTHORITY-RECAPTURE-RAPORU-2026-03-25.md`
- `coordination/faz11-authority-run-contract-2026-03-25.md`
- `coordination/faz11-runtime-lane-contract-2026-03-25.md`

## Hedef

Tek resmi hedef:

- `RC-G` ile `RC-J` arasinda `faz1-50`, `v2-95`, `v3-170` ailelerinin tamaminda post-preprojection output parity'yi resmi olarak yeniden acmak

Planner disi hareket yok:

- yeni candidate build yok
- retrieval/prompt/guardrail/model degisikligi yok
- repair build yok
- release-controls retention yok
- cutover rehearsal yok

## Uygulama Sirasi

1. `WP-1`
   `RC-G` effective-view freeze, `RC-J` parity freeze, authority contract ve runtime lane contract dosyalarini sabitle.
2. `WP-2`
   Output parity trace schema, taxonomy ve final equivalence contract dosyalarini yaz.
3. `WP-3`
   `faz1-50` ve `v2-95` icin canonical first-run parity pair'lerini topla.
   `v3-170` icin yalniz FAZ11 authority input ustunden post-preprojection replay kullan.
4. `WP-3A`
   Her aile icin required mismatch sayimlarini ve metric delta sifir kapisini hesapla.
5. `WP-4`
   Yalniz `WP-3A FAIL` ise parity-failing frontier pack uret.
6. `WP-5`
   Yalniz `WP-4 PASS` ise first-divergence ve primary-reason localization tablosunu kapat.
7. `WP-6`
   Plannerin kapali karar kumesinden resmi steering karari uret.

## Ajan Dagilimi

- `Beauvoir`
  WP karar mantigi ve steering karar tablosu capraz kontrolu.
- `Hilbert`
  FAZ7/FAZ9/FAZ11 reuse haritasi ve builder catisi audit'i.
- `Hooke`
  Runtime trace field mapping ve P0..P6 surface audit'i.

## Repo-Native Uygulama Notu

- Yeni runtime enstrumantasyonu eklenmeyecek.
- FAZ12 parity builder'lari mevcut trace/report payload'larindan uretilecek.
- `scripts/faz12/` altinda yalniz orchestration ve reporting katmani kurulacak.
