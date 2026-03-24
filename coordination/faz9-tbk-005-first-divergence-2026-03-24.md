# FAZ9 TBK-005 First Divergence

Tarih: 2026-03-24

## Kaynaklar

- witness replay: `evaluation/reports/faz9-tbk-005-witness-forensics-2026-03-24.md`
- reference report: `evaluation/reports/eval_faz9_rc_g_tbk005_witness_20260324.json`
- candidate report: `evaluation/reports/eval_faz9_rc_i_tbk005_witness_20260324.json`

## Sonuc

- `question_id = TBK-005`
- `first_divergence_stage = auth_enriched_request`
- `primary_reason = auth_visibility_leak`
- `unexplained_count = 0`

## Not

- `raw_input_request` ve `normalized_request` esit.
- Ilk kirilma, `RC-I` auth principal bilgisinin model-visible stage payload'ina tasinmasiyla basliyor.
- Bu durum resmi WP-5 esleme tablosundaki `auth_visibility_leak -> auth principal model-visible payload'dan cikarilacak` kuralina birebir uyuyor.
