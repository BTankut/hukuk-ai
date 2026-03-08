# Phase 2 Reranker Recovery — 2026-03-08

## Karar
**Safe activation achieved: HAYIR**

Reranker `RERANKER_ENABLED=true` ile test edilen threshold’larda (0.1, 0.2) Faz 1 gate’leri geçse de, en iyi baseline (`reranker off`) karşısında kaliteyi net biçimde iyileştirmedi; özellikle `correct_source_rate` ve `phrase_hit_rate` tarafında regresyon var. Bu nedenle P0 için güvenli aktivasyon kararı verilmedi.

## Canlı Eval Varyantları (50 soru, mock=false)

| Variant | citation_rate | correct_source_rate | hallucination_rate | refusal_accuracy | avg_response_time_ms | blocked_rate |
|---|---:|---:|---:|---:|---:|---:|
| off (run A) `eval_live_phase2_reranker_off_20260308.json` | 0.86 | 0.7653 | 0.04 | 0.90 | 10024.8 | 0.04 |
| off (run B) `eval_live_phase2_reranker_off_20260308b.json` | **0.88** | **0.7953** | 0.04 | 0.92 | 10852.3 | 0.02 |
| on thr=0.1 `eval_live_phase2_reranker_on_thr_01_20260308.json` | 0.88 | 0.7753 | 0.04 | 0.94 | 10350.3 | 0.02 |
| on thr=0.2 `eval_live_phase2_reranker_on_thr_02_20260308.json` | 0.82 | 0.7453 | 0.04 | 0.98 | 11126.3 | 0.08 |

## Değerlendirme
- **Best enabled threshold:** `0.1` (0.2’den daha dengeli).
- `thr=0.1`, baseline-off (run B) ile kıyaslandığında:
  - citation_rate: eşit (0.88)
  - correct_source_rate: **-0.02** (0.7953 → 0.7753)
  - phrase_hit_rate: **-0.0233** (0.6977 → 0.6744)
  - refusal_accuracy: +0.02 (0.92 → 0.94)
- `thr=0.2` kaliteyi daha belirgin düşürüyor (citation/correct_source/blocked_rate kötüleşiyor).

## Sonuç / Öneri
1. **Prod default-off korunmalı** (`RERANKER_ENABLED=false`).
2. Reranker aktivasyonu için yeniden tuning gerekli:
   - daha düşük/adaptif threshold denemeleri,
   - query intent’e göre conditional reranking,
   - fallback stratejisinin kalite etkisi ölçümü (`RERANKER_FALLBACK_TOPK`).
3. Aktivasyon kararı, baseline-off’a karşı en azından `correct_source_rate` ve `citation_rate` tarafında non-regression (tercihen iyileşme) sağlandıktan sonra tekrar değerlendirilmeli.

