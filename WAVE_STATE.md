# Wave State
current_wave: faz2-p0-order-restoration
status: running
started_at: 2026-03-20T18:40:00+03:00
last_activity: 2026-03-21T03:00:00+03:00
last_eval: api-gateway/benchmarks/results/guardrails_bench_20260320_195504.csv
next_action: "restore edilen fine-tune execution chain uzerinden ilk gercek post-train checkpoint + eval manifest akisını calistirmak"
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
  - Guardrails runtime hardening notu kayda geçirildi: `coordination/guardrails-runtime-hardening-2026-03-20.md`
  - Varsayılan config'ten NeMo `self check input` çıkarıldı; deterministik input moderation resmi safe default oldu.
  - Training duplicate hard gate notu kayda geçirildi: `coordination/training-duplicate-hard-gate-2026-03-20.md`
  - `scripts/check_training_readiness.py` artık question duplicate excess için hard fail veriyor.
  - Duplicate inventory üretildi: `coordination/training-duplicate-inventory-2026-03-20.json`
  - Cleanup plan notu kayda geçirildi: `coordination/training-duplicate-cleanup-plan-2026-03-20.md`
  - Top-5 duplicate cluster review packet üretildi: `coordination/training-duplicate-review-packet-2026-03-20.md`
  - Top-5 duplicate canonicalization manifest'i yazıldı: `coordination/training-duplicate-top5-canonicalization-2026-03-20.json`
  - `scripts/apply_duplicate_canonicalization.py` ile top-5 dry-run doğrulandı.
  - Batch2 (`06-10`) review packet ve canonicalization manifest'i üretildi.
  - Top10 birleşik dry-run sonucu duplicate excess `116 -> 52` seviyesine indirilebiliyor.

  ### Kalan Risk
  - Train set içinde 116 question-level duplicate hâlâ mevcut; readiness gate artık bunu bloklayıcı fail olarak görüyor.
  - Eski DGX node1 hattı (`192.168.12.243`) kararsız; aktif live endpoint şu an dgxnode2 fallback runtime.
  - `self_check_facts` / `self_check_hallucination` hattı bu dalgada shelve; ayrı kalibrasyon olmadan tekrar varsayılan yapılmayacak.
  - Guardrails LLM post-processing hâlâ zaman zaman latency limite çarpıp `draft_answer` fallback kullanabiliyor; bu safe-default içinde kabul ediliyor.
  - Duplicate cleanup henüz yapılmadı; gate artık bunu görünür ve bloklayıcı hale getiriyor.
  - Inventory sonucuna göre blind dedupe güvenli değil; cluster bazlı canonicalization gerekiyor.
  - Duplicate cleanup tamamlandı; `final_train.jsonl` artık `807` unique question içeriyor ve duplicate excess `0`.
  - Readiness gate yeniden `READY` durumuna geldi; bu tek başına training başlatma izni anlamına gelmiyor.
  - Resmi pre-train execution package donduruldu: `coordination/pretrain-execution-package-2026-03-21.md`
  - `scripts/build_training_dataset.py` artık final canonicalization manifest'ini varsayılan olarak uygular ve aktif `807` satırlık paketi yeniden üretebilir.
  - `docs/finetune/TRAINING_LOG.md` aktif package ile tarihsel v2 run anlatısını ayıracak şekilde düzeltildi.
  - Promotion evidence contract sıkılaştırıldı; readiness gate artık baseline/post-train manifest içinde `eval_family`, `checkpoint_ref` ve `report_sha256` doğruluyor.
  - İlk frozen baseline manifest üretildi: `evaluation/reports/evidence_baseline_faz1_50_20260308.json`
  - Raw eval runner'lar artık `schema_version`, `eval_family`, `model_ref`, `checkpoint_ref`, `git_commit` alanlarını doğrudan `report_meta` içinde taşıyor.
  - `scripts/run_eval_matrix.sh` ve `evaluation/run_reranker_safe_activation.py` bu metadata'yı raw raporlara propagate edecek şekilde güncellendi.
  - Tarihsel raporlarda referans verilen ama `main` worktree'de eksik kalan fine-tune bootstrap/config zinciri geri eklendi.
  - `configs/finetune/unsloth_sft_qwen35_35b_a3b.json` artık frozen 807-row package, baseline evidence manifest ve expected eval family ile hizalı.
  - `scripts/finetune/check_finetune_config.py` artık train SHA / row count / held-out row count doğruluyor ve canonical readiness gate'i doğrudan çağırıyor.
  - `configs/training/sft_config.yaml` ve `configs/training/sft_llamafactory.yaml` current canonical package için restore edildi.
  - DGX bootstrap runbook restore edildi: `docs/finetune/dgxnode2-lora-bootstrap.md`
  - `scripts/finetune/plan_posttrain_eval.py` ile ilk post-train raw eval + manifest + promotion zinciri repo içinde planlanabilir hale geldi.
  - Text-only PEFT training entrypoint restore edildi: `scripts/finetune/train_qwen35_textonly_peft.py`
  - Promotion gate artık baseline/post-train arasında aynı eval runner family zorunluluğu getiriyor.
  - Frozen baseline manifest `runner=eval_runner` ile zenginleştirildi.
  - Direct merged-model fallback bu yüzden şu an promotion değil, diagnostic/runtime recovery yolu olarak konumlanıyor.

  ### Sonraki Beklenen Çıktı
  - İlk gerçek trained checkpoint artefact'ının restore edilen zincir üzerinden üretilmesi.
  - Ardından aynı eval family ve aynı runner family ile post-train raw report + evidence manifest üretimi.
  - Sonrasında promotion check'in baseline vs post-train manifest ile çalıştırılması.
