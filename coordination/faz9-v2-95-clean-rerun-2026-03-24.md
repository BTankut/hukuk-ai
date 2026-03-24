# FAZ9 v2-95 Clean Rerun

Tarih: 2026-03-24

Karar:
- `v2-95` ilk candidate replay'i resmi closure kaniti sayilmadi.
- ilk run'da yalniz `raw_answer_hash_mismatch` ve `preprojection_hash_mismatch` goruldu; upstream stage drift yoktu.
- ayni aile RC-J uzerinde tek basina, concurrency kapali bicimde yeniden kosuldu.

Sonuc:
- clean rerun report: `evaluation/reports/eval_faz9_rc_j_preprojection_v2_95_r2_20260324.json`
- canonical gate: `evaluation/reports/faz9-rc-j-preprojection-v2-95-2026-03-24.md`
- clean rerun gate:
  - `normalized_request_hash_mismatch_count = 0`
  - `model_request_payload_hash_mismatch_count = 0`
  - `generation_contract_hash_mismatch_count = 0`
  - `preprojection_hash_mismatch_count = 0`
  - `raw_answer_hash_mismatch_count = 0`
  - `parity_runtime_error_count = 0`

Yorum:
- `v2-95` aile sonucu `PASS` olarak kapatildi.
- resmi WP-8 blocker yalniz `v3-170` ailesinde kaldi.
