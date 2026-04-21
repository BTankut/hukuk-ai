# Phase 00 Baseline Freeze Report

## 1. Commit SHA

Phase 0 implementation commit: `c5b2098`.

## 2. Degisen Dosyalar

- `.gitignore`
- `configs/evaluation/hukuk_ai_100_public_questions.csv`
- `scripts/benchmark/run_hukuk_ai_100.sh`
- `scripts/benchmark/run_hukuk_ai_100.py`
- `scripts/benchmark/score_hukuk_ai_100.py`
- `reports/benchmark/phase_00_baseline_20260421.md`
- `docs/hukuk_ai_repo_hardening_plan.md`

Private answer key local-only olarak `evaluation/private/hukuk_ai_100_answer_key_private.csv` altinda tutuldu ve `.gitignore` ile commit disi birakildi.

## 3. Calistirilan Komutlar

```bash
python3 -m py_compile scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py
bash scripts/benchmark/run_hukuk_ai_100.sh --limit 1 --allow-missing-trace --out-dir reports/benchmark/runs/smoke_phase0
python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/smoke_phase0/candidate_answers.csv --answer-key evaluation/private/hukuk_ai_100_answer_key_private.csv --out-dir reports/benchmark/runs/smoke_phase0
python3 -m pytest api-gateway/tests evaluation -q
api-gateway/.venv/bin/python -m pytest api-gateway/tests evaluation -q
bash scripts/benchmark/run_hukuk_ai_100.sh
bash scripts/benchmark/run_hukuk_ai_100.sh --out-dir reports/benchmark/runs/20260421T102639Z --resume
python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260421T102639Z/candidate_answers.csv --answer-key evaluation/private/hukuk_ai_100_answer_key_private.csv --out-dir reports/benchmark/runs/20260421T102639Z
```

## 4. Test / Eval Sonuclari

`python3 -m pytest api-gateway/tests evaluation -q` global Python ortaminda `fastapi` eksikligi nedeniyle collection asamasinda durdu.

`api-gateway/.venv/bin/python -m pytest api-gateway/tests evaluation -q` calisti, fakat mevcut repo test borcu nedeniyle 6 failure verdi:

- `api-gateway/tests/test_faz34_perimeter_proxy.py::test_boundary_proxy_perimeter_isolation_skips_local_store_history_and_write`: `conversation_history` NameError.
- `api-gateway/tests/test_faz5_rc_f_hardening.py` altinda 3 test: `harden_answer()` artik `recovery_profile` parametresini kabul etmiyor.
- `api-gateway/tests/test_reranker_ab.py` altinda 2 integration test: reranker baseline / English-control kalite assertion basarisiz.

Benchmark run:

- Run dir: `reports/benchmark/runs/20260421T102639Z`
- Questions: 100
- Answered: 100
- Refused / empty: 0
- API errors: 0
- Trace rows: 100
- Missing retrieval trace id: 0
- Missing `confidence_0_100`: 100
- Missing `final_reason`: 100

Run 78. soruda terminal kapanmasi nedeniyle kesildi; incremental dosyalar korunarak `--resume` ile ayni run klasorunde 79-100 arasi tamamlandi.

## 5. Benchmark Delta

Plan dokumanindaki onceki insan/judge skoru: 415 / 1000.

Phase 0 deterministic proxy scorer sonucu: 379.55 / 1000.

Bu iki skor bire bir ayni metrik degildir. Phase 0 scorer private rubric sinyallerinden otomatik proxy skor uretir; insan/judge skoru yerine gecmez. Amac baseline'i tekrar kosulabilir, trace'li ve private-key guvenli hale getirmektir.

## 6. Belge Ailesi Kirilimi

| Belge ailesi | Count | Avg proxy | PASS | FAIL |
|---|---:|---:|---:|---:|
| CB_GENELGE | 4 | 1.62 | 0 | 4 |
| CB_KARAR | 8 | 1.44 | 0 | 8 |
| CB_KARARNAME | 6 | 4.80 | 1 | 5 |
| CB_YONETMELIK | 6 | 2.91 | 1 | 5 |
| KANUN | 21 | 3.92 | 3 | 18 |
| KHK | 6 | 5.58 | 1 | 5 |
| KKY | 11 | 5.18 | 4 | 7 |
| MULGA | 5 | 2.58 | 0 | 5 |
| TEBLIGLER | 8 | 5.46 | 2 | 6 |
| TUZUK | 5 | 4.65 | 1 | 4 |
| UY | 10 | 3.66 | 1 | 9 |
| YONETMELIK | 10 | 2.60 | 0 | 10 |

## 7. Task Type Kirilimi

| Task type | Count | Avg proxy | PASS | FAIL |
|---|---:|---:|---:|---:|
| compliance_checklist | 8 | 3.02 | 1 | 7 |
| current_update | 5 | 3.48 | 1 | 4 |
| document_selection | 36 | 4.40 | 6 | 30 |
| exception_analysis | 2 | 4.88 | 1 | 1 |
| hierarchy_conflict | 8 | 2.97 | 1 | 7 |
| precise_retrieval | 10 | 4.14 | 1 | 9 |
| scenario_applicability | 12 | 3.44 | 2 | 10 |
| temporal_validity | 19 | 3.33 | 1 | 18 |

## 8. En Kotu Kalan 10 Soru

- CBY-01
- MULGA-03
- CBG-01
- CBG-03
- CBG-04
- CBK-04
- CBKAR-03
- CBKAR-04
- CBKAR-07
- CBKAR-08

## 9. Hata Sinifi Dagilimi

| Failure class | Count |
|---|---:|
| answer_contract_missing | 100 |
| auto_fail_triggered | 2 |
| missing_gold_document_signal | 28 |
| missing_required_content_signal | 99 |

## 10. Yeni Riskler / Geriye Donuk Uyumluluk

- `confidence_0_100` ve `final_reason` alanlari gateway cevabinda bos; bu cevap metni uretimini engellemiyor fakat denetlenebilirlik ve otomatik scoring icin sistematik contract acigi.
- Proxy scorer insan/judge yerine gecmez; Phase 1'de belge ailesi, belge kimligi, madde/bolum ve temporal validity seviyelerinde gercek metrik semasi genisletilmeli.
- Mevcut repo test suite'i Phase 0 disi borclar nedeniyle kirmizi; sonraki fazlarda bu failure'lar baseline risk olarak ayrica takip edilmeli.
- `reports/benchmark/runs/` ignore edildi; run artifact'leri yerelde kalir, phase raporlari commit edilir.

## 11. Sonraki Faz Onerisi

Phase 1'e gecilmeli: `evaluation/metrics.py` ve ilgili raporlama katmani 12 belge ailesini kapsayan canonical source matching semasina genisletilmeli. Ayrica answer contract eksigi Phase 8 konusu olsa da, Phase 1 raporlarinda `answer_contract_missing` regressionsiz takip edilmelidir.
