# Phase 01 Metrics Schema and Calibration Report

## 1. Commit SHA Listesi

- Commit 1: `47280cb` benchmark: phase 1 add canonical source schema groundwork
- Commit 2: `fa51b85` benchmark: phase 1 extend scorer taxonomy
- Commit 3: pending at report generation time; this report is included in the calibration/reporting commit.

## 2. Degisen Dosyalar

- `evaluation/hukuk_ai_100_source_schema.py`
- `evaluation/report_metadata.py`
- `scripts/benchmark/score_hukuk_ai_100.py`
- `scripts/benchmark/calibrate_hukuk_ai_100_proxy.py`
- `configs/evaluation/hukuk_ai_100_calibration_subset.csv`
- `reports/benchmark/hukuk_ai_phase1_execution_brief_after_phase0_5.md`
- `reports/benchmark/phase_01_metric_schema_20260421.md`
- `reports/benchmark/phase_01_calibration_20260421/calibration_scored.csv`
- `reports/benchmark/phase_01_calibration_20260421/calibration_summary.json`
- `reports/benchmark/phase_01_calibration_20260421/calibration_summary.md`
- `reports/benchmark/phase_01_metrics_and_calibration_20260421.md`

## 3. Calistirilan Komutlar

```bash
api-gateway/.venv/bin/python -m py_compile evaluation/hukuk_ai_100_source_schema.py evaluation/report_metadata.py
api-gateway/.venv/bin/python -m py_compile scripts/benchmark/score_hukuk_ai_100.py
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260421T102639Z/candidate_answers.csv --answer-key evaluation/private/hukuk_ai_100_answer_key_private.csv --out-dir reports/benchmark/runs/20260421T102639Z_phase1
api-gateway/.venv/bin/python scripts/benchmark/calibrate_hukuk_ai_100_proxy.py --scored reports/benchmark/runs/20260421T102639Z_phase1/scored.csv --calibration configs/evaluation/hukuk_ai_100_calibration_subset.csv --out-dir reports/benchmark/phase_01_calibration_20260421
bash scripts/benchmark/run_green_lane.sh --ci
bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260421T102639Z
api-gateway/.venv/bin/python -m pytest api-gateway/tests evaluation -q
```

## 4. Test / Eval Sonuclari

Green lane sonucu: pass.

Phase 1 scorer mevcut Phase 0 run artifact'i uzerinde yeniden calisti:

- Run artifact: `reports/benchmark/runs/20260421T102639Z`
- Phase 1 scored output: `reports/benchmark/runs/20260421T102639Z_phase1/scored.csv`
- Phase 1 summary: `reports/benchmark/runs/20260421T102639Z_phase1/score_summary.md`

Legacy suite observe-only sonucu Phase 0.5 ile ayni baseline debt olarak kaldi: 6 failure.

## 5. Phase 0'a Gore Metrik Farklari

Phase 0 proxy scorer ve Phase 1 proxy scorer ayni metrik degildir. Phase 1 alt metrik, canonical family ve penalty sinyalleri ekledigi icin raw skor dogrudan kalite artisi olarak yorumlanmamalidir.

| Metric | Phase 0 proxy | Phase 1 proxy |
|---|---:|---:|
| Raw proxy score | 379.55 / 1000 | 441.70 / 1000 |
| Average proxy score | 3.80 | 4.42 |
| PASS proxy | 14 | 19 |
| FAIL proxy | 86 | 81 |
| Answer contract completeness | 0.00 | 0.00 |
| Missing gold document signal | 28 | 28 |
| Hallucinated source count | not separated | 28 |
| Temporal validity miss count | not separated | 10 |
| Repealed-as-active count | not separated | 2 |

Phase 1 alt skor ortalamalari:

| Sub-metric | Avg |
|---|---:|
| family_match_score | 0.300 |
| document_match_score | 0.570 |
| article_match_score | 0.700 |
| temporal_validity_score | 0.795 |
| grounding_score | 0.410 |
| answer_contract_score | 0.000 |

## 6. Calibration Sonucu

Calibration dosyasi private answer key icermez. QID, expected band ve kritik hata flag'lerinden olusur.

- Calibration set: 20 soru
- High band: 5
- Medium band: 5
- Low band: 10
- Exact band accuracy: 1.0
- Adjacent/exact band accuracy: 1.0
- Low-band recall: 1.0
- Critical flag any-match rate: 1.0
- Calibration report: `reports/benchmark/phase_01_calibration_20260421/calibration_summary.md`

Risk notu: mevcut calibration label kaynagi `phase1_proxy_seed_pending_human_judge_confirmation`. Bu, gercek insan/judge kalibrasyonu yerine gecmez. Script ve format hazir; insan/judge QID band etiketleri geldiginde ayni aracla yeniden kalibrasyon yapilmalidir.

## 7. Yeni Failure Taxonomy Dokumu

| Failure class | Count |
|---|---:|
| answer_contract_missing | 100 |
| auto_fail_triggered | 2 |
| hallucinated_identifier | 62 |
| missing_gold_document_signal | 28 |
| missing_required_content_signal | 99 |
| missing_temporal_qualification | 10 |
| partial_grounding_only | 99 |
| repealed_source_used_as_active | 2 |
| wrong_article | 2 |
| wrong_document | 28 |
| wrong_family | 70 |

Belge ailesi proxy ortalamalari:

| Family | Avg | PASS | FAIL |
|---|---:|---:|---:|
| CB_GENELGE | 2.96 | 1 | 3 |
| CB_KARAR | 1.29 | 0 | 8 |
| CB_KARARNAME | 6.81 | 4 | 2 |
| CB_YONETMELIK | 2.65 | 0 | 6 |
| KANUN | 4.01 | 0 | 21 |
| KHK | 6.63 | 3 | 3 |
| KKY | 6.06 | 6 | 5 |
| MULGA | 2.85 | 1 | 4 |
| TEBLIGLER | 6.92 | 3 | 5 |
| TUZUK | 5.22 | 1 | 4 |
| UY | 3.79 | 0 | 10 |
| YONETMELIK | 3.85 | 0 | 10 |

En kotu 10 QID:

- CBKAR-03
- CBKAR-04
- CBKAR-08
- CBY-01
- CBY-03
- MULGA-03
- MULGA-04
- UY-10
- CBKAR-01
- CBG-01

## 8. Riskler / Bilinen Aciklar

- `answer_contract_score` halen 0.0; `confidence_0_100` ve `final_reason` eksikleri sonraki fazda cozulecek ana blokajdir.
- `wrong_family=70` cok yuksek; bunun bir kismi gercek retrieval/source-selection problemi, bir kismi ise cevapta/surface trace'te birden fazla aile sinyalinin bulunmasindan kaynaklanan heuristic gürültü olabilir.
- Calibration labels su an proxy-seed niteliginde; gercek insan/judge QID etiketleriyle tekrar kosulmadan promotion metriği olarak kullanilmamali.
- Phase 1 scorer private answer key ile local scoring yapar ancak private gold text veya must-include metinlerini committed outputlara yazmaz.

## 9. Sonraki Faz Onerisi

Revize plana uygun olarak bir sonraki faz dogrudan Answer Contract Hardening olmalidir. Retrieval tuning'e gecmeden once:

- `confidence_0_100` zorunlu uretilmeli.
- `final_reason` kontrollu sablonla zorunlu uretilmeli.
- Unsupported confident answer dusurulmeli veya degraded-mode olarak isaretlenmeli.
- Contract completeness hedefi `>= 98/100` seviyesine cikartilmali.
