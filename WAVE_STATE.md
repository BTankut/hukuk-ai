# Wave State
current_wave: faz2-p0-order-restoration
status: running
started_at: 2026-03-20T18:40:00+03:00
last_activity: 2026-03-20T19:02:00+03:00
last_eval: evaluation/reports/eval_live_20260308_080601.json
next_action: "95q ve 170q eval soru setlerini repo içine geri alıp canonical eval matrix'i tamamlamak"
blockers:
  - missing configs/evaluation/test_questions_v2_95.json
  - missing configs/evaluation/test_questions_v3_170.json
notes: |
  ## Faz 2 P0 Hizalama Dalgası

  Amaç, training odaklı ilerlemeyi durdurmak değil; önce P0 kapılarını yeniden sıraya koymak.

  ### Aktif Sıra
  1. Reranker A/B ve threshold sweep
  2. Guardrails facts-only ve latency yolu
  3. Retrieval genişleme kararı
  4. Training gate

  ### Baseline Ayrımı
  - 50q: Faz 1 canlı kabul baz çizgisi
  - 95q: Phase 3 hardening
  - 170q: model misuse / training sınırı

  ### Şu Anki Kural
  - Yeni training run, readiness gate kapanmadan geçerli sayılmaz.
  - Veri provenance'u lawyer-reviewed / pending-review / synthetic olarak açık ayrılacak.
  - Reranker ve guardrails kararları, training'den bağımsız olarak ölçülüp kilitlenecek.

  ### Bu Turda Kapanan İş
  - `scripts/build_training_dataset.py` held-out contamination bug'i düzeltildi.
  - `data/finetune/sft/final_train.jsonl` 1076 → 923 satıra yeniden üretildi.
  - `scripts/check_training_readiness.py --mode preflight` artık PASS veriyor.

  ### Kalan Risk
  - Train set içinde 116 question-level duplicate hâlâ mevcut; şu an yalnızca raporlandı, henüz yeni bir hard gate yapılmadı.

  ### Sonraki Beklenen Çıktı
  - 95q ve 170q soru setleri repo'ya geri alınacak veya yeniden üretilecek.
