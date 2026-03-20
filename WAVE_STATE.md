# Wave State
current_wave: faz2-p0-order-restoration
status: running
started_at: 2026-03-20T18:40:00+03:00
last_activity: 2026-03-20T19:55:00+03:00
last_eval: evaluation/reports/eval_live_20260308_080601.json
next_action: "DGX runtime drift'ini netleştirip generation katmanını stabilize etmek; ardından kısa live smoke ve safe-activation canlı koşusu"
blockers:
  - DGX runtime eski varsayımdan sapmış durumda: `30000/vllm_head` yerine `30001/qwen35-base-eval` gözlendi
  - DGX host/endpoint erişimi kararsız: ilk probe sonrası `ssh` ve `http` timeout'ları yaşandı
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

  ### Runtime Recovery
  - `scripts/build_training_dataset.py` held-out contamination bug'i düzeltildi.
  - `data/finetune/sft/final_train.jsonl` 1076 → 923 satıra yeniden üretildi.
  - `scripts/check_training_readiness.py --mode preflight` artık PASS veriyor.
  - 95q ve 170q eval setleri git geçmişinden geri alındı.
  - `scripts/run_eval_matrix.sh all` artık üç seti de plan modunda çözüyor.
  - `evaluation/run_reranker_safe_activation.py` eklendi.
  - `docs/reranker-safe-activation-runbook.md` ile canlı A/B akışı belgelendi.

  ### Bu Turda Kapanan İşler
  - `docker compose -f api-gateway/docker-compose.milvus.yml up -d` ile Milvus hattı geri kaldırıldı.
  - `api-gateway/.venv` temiz repoda `3.12.9` ile kuruldu.
  - `api-gateway[dev,milvus]` bağımlılıkları kuruldu.
  - `en_core_web_lg` kurularak gateway startup blocker'ı aşıldı.
  - Embedding service `localhost:8081` üzerinde ayağa kaldırıldı.
  - API Gateway `localhost:8000` üzerinde ayağa kaldırıldı.
  - Retrieval zinciri `mevzuat_e5_shadow` + remote e5 embedding ile doğrulandı.
  - Runtime notu kaydedildi: `coordination/runtime-bringup-recovery-2026-03-20.md`

  ### Kalan Risk
  - Train set içinde 116 question-level duplicate hâlâ mevcut; şu an yalnızca raporlandı, henüz yeni bir hard gate yapılmadı.
  - Reranker canlı sweep manuel API restart gerektiriyor; otomatik restart bu repo içinde bilinçli olarak yapılmıyor.
  - DGX generation katmanı kararlı değil; ilk `30001` probe'undan sonra timeout gözlendi.

  ### Sonraki Beklenen Çıktı
  - DGX stabilize olduktan sonra kısa live smoke.
  - Ardından ilk canlı karar matrisi: `baseline-off` + `thr=0.1..0.5`.
