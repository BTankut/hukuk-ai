# Training Duplicate Cleanup Complete

Date: 2026-03-20
Scope: full cluster canonicalization and official train rewrite
Decision: `final_train.jsonl` canonicalized and readiness restored

## Inputs

- Source packet: `coordination/training-duplicate-review-packet-final-2026-03-20.json`
- Canonicalization manifest: `coordination/training-duplicate-final-canonicalization-2026-03-20.json`
- Train file: `data/finetune/sft/final_train.jsonl`

## Uygulama

1. Tüm `24` duplicate-question cluster için canonical variant seçimi kayda geçirildi.
2. `scripts/apply_duplicate_canonicalization.py` ile resmi train set yeniden yazıldı.
3. Ajan review ile kalan kuyruk cluster'lar ikinci kez kontrol edildi.
4. Ajan itirazları içinden yalnız `cluster-22` kabul edildi; `cluster-11` cited ve yeterince net olduğu için korundu.

## Sonuç

- total records: `923 -> 807`
- unique questions: `807 -> 807`
- duplicate question groups: `24 -> 0`
- duplicate excess rows: `116 -> 0`

## Readiness Doğrulaması

Komut:

`python3 scripts/check_training_readiness.py --mode preflight --baseline-evidence-path evaluation/reports/eval_live_20260308_080601.json`

Sonuç:

- held-out leakage: `PASS`
- duplicate question excess: `PASS`
- baseline evidence: `PASS`
- overall: `READY`

## Not

Bu milestone yalnız veri temizliği ve readiness geri kazanımıdır. Yeni training run kararı bundan sonra da Faz planındaki provenance, eval ve promotion kapılarına bağlı kalacaktır.
