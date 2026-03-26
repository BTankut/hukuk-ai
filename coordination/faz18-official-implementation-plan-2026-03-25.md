# FAZ18 Official Implementation Plan

Tarih: 2026-03-25

Referans:
- `docs/FAZ18-ROTASYON-RC-M-DISCARD-VE-OUTPUT-PARITY-SURFACE-FORENSICS-TALIMATI-2026-03-25.md`
- `docs/FAZ17-RC-M-AUTHORITATIVE-OUTPUT-PARITY-REOPEN-RAPORU-2026-03-25.md`

## Faz Kapsami

FAZ18 yalniz `RC-M discard` ve `output-parity surface forensics` paketidir.

Bu fazda:
- yeni build yok
- yeni patch yok
- yeni rerun yok
- yeni repair gate yok
- yeni cutover veya release-controls isi yok

## Resmi Pair Seti

- `control_pair = RC-G vs RC-J`
- `breach_pair_primary = RC-G vs RC-M`
- `breach_pair_secondary = RC-J vs RC-M`

## WP Sirasi

1. `WP-1` freeze ve authority / forensic contract
2. `WP-2` schema / taxonomy / stage ladder / authorized surface contract
3. `WP-3` `RC-G vs RC-J` control-pair authority recapture
4. `WP-4` `RC-G vs RC-M` authoritative summary truth recapture
5. `WP-5` tek kayitlik surface-breach frontier localization
6. `WP-6` resmi reconciliation ve tek karar

## Frozen Evidence Kaynaklari

- `evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-*.json`
- `evaluation/reports/faz17-rc-m-output-parity-authoritative-*.json`
- `evaluation/reports/faz17-output-parity-authoritative-frontier-replay-2026-03-25.json`
- `evaluation/reports/faz17-rc-j-vs-rc-m-frontier-diagnostic-containment-2026-03-25.json`

## Beklenen Karar Mantigi

- `WP-3 FAIL` ise `NO-GO - Current Authority Unstable`
- `WP-3 PASS` ve `WP-4 FAIL` ise planner karar kurali uygulanir
- `WP-3 PASS`, `WP-4 PASS`, `WP-5 PASS` ise localization `PASS`
