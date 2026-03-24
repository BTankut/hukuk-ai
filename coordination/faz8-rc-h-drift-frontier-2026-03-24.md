# FAZ8 RC-H Drift Frontier

Tarih: 2026-03-24

## Kaynaklar

- frontier report: `evaluation/reports/faz8-rc-h-parity-frontier-2026-03-24.md`
- frontier json: `evaluation/reports/faz8-rc-h-parity-frontier-2026-03-24.json`
- replay report: `evaluation/reports/faz8-rc-h-first-divergence-replay-2026-03-24.md`
- replay json: `evaluation/reports/faz8-rc-h-first-divergence-replay-2026-03-24.json`

## Frozen Frontier Ozeti

- frontier_total = `242`
- mismatch_total = `234`
- parity_runtime_error_total = `8`

## Family Breakdown

- `faz1-50` frontier `34`, mismatch `34`, error `0`
- `v2-95` frontier `86`, mismatch `82`, error `4`
- `v3-170` frontier `122`, mismatch `118`, error `4`

## First-Divergence Ozeti

- trace_completion = `242`
- unexplained_count = `0`
- first_divergence_breakdown:
  - `eval_client_parsed_object = 242`
- primary_reason_breakdown:
  - `eval_client_parse_drift = 234`
  - `parity_runtime_error = 8`

## Sonuc

- `RC-H` parity fail frontier FAZ8 icin tek drift hakikati olarak donduruldu.
- Yeni kalite frontier acilmadi.
