# FAZ9 Bind Ladder First Break

Tarih: 2026-03-24

## Kaynaklar

- replay summary: `evaluation/reports/faz9-bind-ladder-witness-replay-2026-03-24.md`
- L0 report: `evaluation/reports/eval_faz9_bind_l0_tbk005_v2_20260324.json`
- L1 report: `evaluation/reports/eval_faz9_bind_l1_tbk005_v2b_20260324.json`
- L2 report: `evaluation/reports/eval_faz9_bind_l2_tbk005_v2_20260324.json`

## Resmi Okuma

- `L0 = PASS`
- `L1 = PASS`
- `L2 = FAIL`

## First Break

- `first_divergence_level = L2`
- `first_divergence_stage = auth_enriched_request`
- `primary_reason = auth_visibility_leak`
- `unexplained_count = 0`

## Not

- L1 icin eszamanli denemede gorulen tekil raw drift resmi first-break olarak alinmadi.
- Sabit seed / no-retry / streaming-off ile seri witness replay tekrarinda `L1` parity verdi.
- Bu nedenle resmi bind ladder first-break `L2 auth principal resolution` katmani olarak donduruldu.
