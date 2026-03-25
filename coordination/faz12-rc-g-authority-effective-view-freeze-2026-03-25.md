# FAZ12 RC-G Authority Effective View Freeze

Tarih: 2026-03-25

Referans:
- `coordination/faz7-rc-g-freeze-2026-03-24.md`
- `coordination/faz11-authority-run-contract-2026-03-25.md`
- `evaluation/reports/eval_faz11_rc_g_v3_170_authority_20260325.json`
- `evaluation/reports/eval_faz11_rc_g_v3_170_authority_error_rerun_20260325.json`

## Donmus Kural

`RC-G` bu faz boyunca kabul edilmis kalite ve answer-path referansidir.

Authority/effective-view kuralı:

- first-run satirlari preserve edilir
- yalniz gercek runtime-error veren ordinal icin tek error-rerun kullanilir
- error-rerun first-run satirlarini overwrite etmez
- parity ve gate hesaplari effective view uzerinden yapilir

## Aile Bazli Uygulama

- `faz1-50`
  yeni canonical first-run authority ciftinin reference tarafidir
- `v2-95`
  yeni canonical first-run authority ciftinin reference tarafidir
- `v3-170`
  FAZ11 authority pair icindeki `RC-G` first-run + allowed error-rerun effective view tek resmi kaynaktir

## Sabit Referanslar

- `candidate_id = rc-g-faz6-accepted-20260323`
- `checkpoint_ref = rc-g-accepted-20260323`
- frozen family quality reference:
  - `evaluation/reports/eval_faz6_rc_g_faz1-50_20260323.json`
  - `evaluation/reports/eval_faz6_rc_g_v2-95_20260323.json`
  - `evaluation/reports/eval_faz6_rc_g_v3-170_20260323.json`
