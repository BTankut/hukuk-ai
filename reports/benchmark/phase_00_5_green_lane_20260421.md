# Phase 00.5 Benchmark Green Lane Report

## 1. Commit SHA

Pending at report generation time. This report is included in the Phase 0.5 commit; use `git log -1` after commit for the immutable SHA.

## 2. Degisen Dosyalar

- `.github/workflows/benchmark-hardening.yml`
- `.gitignore`
- `configs/evaluation/hukuk_ai_100_legacy_test_debt.json`
- `reports/benchmark/hukuk_ai_repo_hardening_plan_revision_after_phase0.md`
- `reports/benchmark/phase_00_5_green_lane_20260421.md`
- `scripts/benchmark/check_private_guard.py`
- `scripts/benchmark/run_green_lane.sh`
- `scripts/benchmark/validate_hukuk_ai_100_public_questions.py`
- `scripts/benchmark/validate_hukuk_ai_100_run.py`

## 3. Calistirilan Komutlar

```bash
bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260421T102639Z
bash scripts/benchmark/run_green_lane.sh --ci
api-gateway/.venv/bin/python -m pytest api-gateway/tests evaluation -q
```

## 4. Test / Eval Sonuclari

Benchmark green lane resmi komutu:

```bash
bash scripts/benchmark/run_green_lane.sh
```

Local doğrulamada mevcut Phase 0 run artifact'i explicit verildi. Green lane asagidaki kontrolleri yapar:

- Project venv Python disinda benchmark lane calistirmayi reddeder.
- Benchmark Python dosyalarini compile eder.
- Public 100 soru CSV semasini ve qid tekilligini kontrol eder.
- Private answer key ve master dosyalarinin git'e girmedigini kontrol eder.
- Verilen run artifact'i icin 100 answer row, 100 trace row, eksiksiz qid seti, bos olmayan `retrieval_trace_id`, 0 API error ve 0 refusal/empty sartlarini kontrol eder.
- CI modunda live model/private answer key gerekmeden yapisal benchmark guard'lari kosar.

Legacy suite sonucu Phase 0 ile ayni baseline debt olarak observe-only tutuldu: 6 failure.

## 5. Benchmark Delta

Skor degisikligi yok. Bu faz kalite tuning degil, test lane izolasyonu fazidir.

Phase 0 proxy skor referansi: 379.55 / 1000.

## 6. Belge Ailesi Kirilimi

Degismedi; Phase 0 raporu referans alinacak.

## 7. Task Type Kirilimi

Degismedi; Phase 0 raporu referans alinacak.

## 8. En Kotu Kalan 10 Soru

Degismedi; Phase 0 raporu referans alinacak.

## 9. Hata Sinifi Dagilimi

Degismedi; Phase 0 raporu referans alinacak.

Legacy test debt listesi `configs/evaluation/hukuk_ai_100_legacy_test_debt.json` altina yapilandirilmis olarak eklendi.

## 10. Yeni Riskler / Geriye Donuk Uyumluluk

- CI green lane live model veya private answer key gerektirmez; yapisal benchmark guard'lari kosar.
- Full benchmark run artifact validation local run klasoruyle yapilir ve run artifact'leri commit edilmez.
- Legacy suite CI job'u `continue-on-error` ile observe-only tutuldu; benchmark gelistirmeleri unrelated legacy failure'lar tarafindan bloklanmayacak.

## 11. Sonraki Faz Onerisi

Phase 1'e gecilmeli: evaluation metrics schema 12 belge ailesine genisletilmeli ve revizyon dokumanindaki proxy-vs-judge calibration adimi eklenmelidir.
