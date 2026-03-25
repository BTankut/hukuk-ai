# FAZ12 RC-J Output Parity Freeze

Tarih: 2026-03-25

Referans:
- `coordination/faz9-rc-j-manifest-2026-03-24.json`
- `docs/FAZ11-NON-REPRODUCIBLE-FRONTIER-RESOLUTION-VE-V3-170-FIRST-RUN-AUTHORITY-RECAPTURE-RAPORU-2026-03-25.md`

## Donmus Kural

`RC-J` bu faz boyunca tek diagnostic parity adayidir.

Authority kurali:

- first-run otoritatiftir
- `runtime_error = 0` ise rerun yasaktir
- clean rerun yasaktir
- runtime error varsa yalniz error veren ordinal icin tek ek rerun alinabilir
- gate hesaplari effective view uzerinden yapilir; first-run authority preserve edilir

## Aile Bazli Uygulama

- `faz1-50`
  yeni canonical first-run parity pair icindeki candidate taraftir
- `v2-95`
  yeni canonical first-run parity pair icindeki candidate taraftir
- `v3-170`
  FAZ11 `RC-J` full first-run authority report tek resmi parity input kaynagidir

## Sabit Referanslar

- `candidate_id = rc-j-20260324`
- `checkpoint_ref = rc-j-2026-03-24`
- bu fazda `RC-J` ustune patch veya answer_path_delta uygulanmayacaktir
