# FAZ8 Parity Reconciliation Table

Tarih: 2026-03-24

| Yuzey | Durum | Kanit | Yorum |
| --- | --- | --- | --- |
| `RC-H` frozen frontier | `COMPLETED` | `evaluation/reports/faz8-rc-h-parity-frontier-2026-03-24.md` | Uc ailede mismatch ve runtime error frontier donduruldu |
| first-divergence replay | `COMPLETED` | `evaluation/reports/faz8-rc-h-first-divergence-replay-2026-03-24.md` | frontier kapsam `100%`, unexplained `0` |
| `RC-I` build contract | `COMPLETED` | `coordination/faz8-rc-i-build-contract-2026-03-24.md`, `coordination/faz8-rc-i-manifest-2026-03-24.json` | allowed diff surface resmi talimatla sinirli |
| `RC-I` witness replay | `FAIL` | `evaluation/reports/eval_faz8_rc_g_faz1_witness_20260324.json`, `evaluation/reports/eval_faz8_rc_i_faz1_witness_20260324.json` | `TBK-005` kaydinda stage 1,2,4 ayni; stage 3 auth drift beklenen; stage 5 raw answer ayrisiyor |
| pre-projection hash gate | `FAIL` | `evaluation/reports/faz8-rc-i-preprojection-hash-gate-2026-03-24.md` | `preprojection_hash_mismatch_count = 1` |
| normalized parity witness | `FAIL` | `evaluation/reports/faz8-rc-i-output-parity-witness-2026-03-24.md` | `TBK-005` answer body ve citation/source projection farkli |

## Witness Notu

- `TBK-005` icin `RC-G` ve `RC-I` stage 4 `pre_answer_handler_payload` hash'i aynidir.
- Stage 5 `raw_answer_object` farki yalniz auth/session drift ile aciklanamaz:
  - `RC-G` answer_text daha genis ve `4` citation tasir
  - `RC-I` answer_text daralir ve `2` citation tasir
- Bu nedenle fail, yalniz envelope/projection sonrasi bir gorunum farki olarak kaydedilmedi.
