# Wave State
current_wave: faz2-p0-order-restoration
status: running
started_at: 2026-03-20T18:40:00+03:00
last_activity: 2026-03-20T23:10:00+03:00
last_eval: api-gateway/benchmarks/results/guardrails_bench_20260320_195504.csv
next_action: "dgxnode2 runtime'da guardrails self_check_input false-positive drift'ini kaldırmak"
blockers: []
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
  - Embedding service `localhost:8081` üzerinde ayağa kaldırıldı.
  - API Gateway `localhost:8000` üzerinde ayağa kaldırıldı.
  - Retrieval zinciri `mevzuat_e5_shadow` + remote e5 embedding ile doğrulandı.
  - Yeni live LLM runtime doğrulandı: `192.168.12.236:8080/v1` / `Qwen3.5-35B-A3B-Q8_0.gguf`
  - Guardrails pipeline, `llama.cpp` runtime'ın stringified refusal cevabını parse edip fail-open davranacak şekilde düzeltildi.
  - Gateway smoke, guardrails açık modda PASS verdi.
  - Unsafe live smoke, `input_unsafe_request` ile doğru şekilde bloklandı.
  - `faz1-50` üzerinde reranker safe-activation sweep tamamlandı: `baseline-off`, `thr=0.1`, `0.2`, `0.3`, `0.4`, `0.5`.
  - Sonuç: hiçbir reranker threshold'u baseline-off varyantını geçemedi; karar `keep-off`.
  - `evaluation/run_reranker_safe_activation.py`, Faz 1 gate fail'inde matrisi yarıda kesmeyecek şekilde düzeltildi.
  - Guardrails canlı benchmark'ı mevcut safe-default modun doğruluğunu yeniden teyit etti.
  - Mevcut repo gerçeği `facts-only` değil, `safe-scope minimal` olarak kayda geçirildi.
  - Runtime notu güncellendi: `coordination/runtime-bringup-recovery-2026-03-20.md`
  - Reranker karar notu kayda geçirildi: `coordination/reranker-safe-activation-decision-2026-03-20.md`
  - Guardrails karar notu kayda geçirildi: `coordination/guardrails-safe-default-decision-2026-03-20.md`
  - Retrieval low-risk kararı kayda geçirildi: `coordination/retrieval-low-risk-decision-2026-03-20.md`
  - Retrieval baseline `top_k=20` olarak güncellendi.
  - Açık madde referanslarında exact article force-include retrieval davranışı eklendi.

  ### Kalan Risk
  - Train set içinde 116 question-level duplicate hâlâ mevcut; şu an yalnızca raporlandı, henüz yeni bir hard gate yapılmadı.
  - Eski DGX node1 hattı (`192.168.12.243`) kararsız; aktif live endpoint şu an dgxnode2 fallback runtime.
  - `self_check_facts` / `self_check_hallucination` hattı bu dalgada shelve; ayrı kalibrasyon olmadan tekrar varsayılan yapılmayacak.
  - `self_check_input`, dgxnode2 `llama.cpp` runtime üzerinde boş completion kaynaklı false-positive üretme riski taşıyor; ayrı runtime-hardening işi olarak ayrıldı.

  ### Sonraki Beklenen Çıktı
  - Guardrails runtime drift fix.
  - Ardından training gate için kalan veri/need ayrımı.
