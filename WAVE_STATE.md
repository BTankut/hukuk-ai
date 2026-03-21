# Wave State
current_wave: faz2-p0-order-restoration
status: running
started_at: 2026-03-20T18:40:00+03:00
last_activity: 2026-03-21T17:12:00+03:00
last_eval: evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json
next_action: "node3 current adapter icin merged_16bit export tamamlaninca daha hizli serving path'e gecip latency yeniden olcmek"
blockers:
  - "node3 post-train candidate runtime ortalama yanit suresi ~120.3s; FAZ1-FINAL-RAPOR canli kabul hedefi olan <=30s ile uyumlu degil"
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
  - `evaluation/eval_transformers_direct.py` ile merged checkpoint için repo-native diagnostic runner eklendi.
  - `scripts/finetune/plan_posttrain_diagnostic_eval.py` ile serving bloklandığında direct diagnostic eval zinciri planlanabilir hale geldi.
  - dgxnode2 üzerinde `scripts/finetune/check_finetune_config.py` `READY_FOR_TRAINING_GATE` verdi.
  - dgxnode2 Hugging Face cache içinde `Qwen/Qwen3.5-35B-A3B` mevcut.
  - Historical merged checkpoint direct diagnostic fallback ile 100% weight load seviyesine kadar doğrulandı.
  - Text-only PEFT dry-run base model shard loading aşamasına kadar doğrulandı.
  - Uzun dgxnode2 oturumlarında ssh reset/timeout gözlendi; ağır remote işler için detached log-backed launch stratejisine geçildi.
  - Bu amaçla `scripts/finetune/detach_logged_job.py` eklendi.
  - Recovery notu yazıldı: `coordination/dgxnode2-overnight-launch-recovery-2026-03-21.md`
  - Live prompt path'in `rag/prompt_builder.py` değil `llm/client.py` olduğu teyit edildi; ilk Wave 2 prompt-only değişiklik doğrudan active path üzerinde yapıldı.
  - `llm/client.py` explicit article, law-prefix, cross-law citation discipline ve compactness kurallarıyla sertleştirildi.
  - `api-gateway/tests/test_llm_client.py` ile gerçek prompt path test kapsamına alındı.
  - Embedding service local cache + offline startup + cpu fallback ile sertleştirildi: `services/embedding-service/src/model.py`
  - `tests/test_embedding_service_model.py` eklendi.
  - Local embedding service `127.0.0.1:8081` health `ok`.
  - Local gateway `127.0.0.1:8000` health `ok`.
  - Live smoke gateway'den generation aşamasına geçemedi; upstream dgxnode2 model endpoint şu an down.
  - Prompt hardening notu yazıldı: `coordination/wave2-prompt-hardening-2026-03-21.md`
  - dgxnode2 SSH geri geldi; remote repo `/home/btankut/hukuk-ai-git` ile detached log-backed execution yeniden açıldı.
  - Text-only PEFT dry-run detached olarak tamamlandı: `DRY_RUN_OK`, `load_time_s=281.49`, `peak_mem_reserved_gb=64.64`.
  - İlk gerçek one-step training smoke detached olarak tamamlandı: `TRAIN_OK`.
  - Smoke artefact'ları remote path altında üretildi: `artifacts/finetune/unsloth-sft-qwen35-35b-a3b/smoke-step1-20260321/adapter` ve `checkpoint-1`.
  - Smoke telemetry: `step_time_s=33.607`, `train_runtime=35.82`, `train_loss=0.5954`, `peak_mem_reserved_gb=66.79`.
  - `192.168.12.236:8080` için hostta dinleyen aktif runtime bulunamadı; `ss -ltnp` yalnız `unsloth studio` (`0.0.0.0:8000`) ve yardımcı servisleri gösterdi.
  - Önceki node2 runtime izleri `sglang_qwen3_node2.log` içinde bulundu; tarihsel launch `31000` portunda ve scheduler/warmup exception ile kapanmış görünüyor.
  - Historical merged checkpoint varlığı tekrar doğrulandı: `/home/btankut/hukuk-ai-finetune/outputs/hukuk-ai-lora-v2/merged` (~65G).
  - Kullanıcı yönlendirmesiyle proven external FINAL_SETTINGS kaynakları içe alındı.
  - Qwen3.5 stable training ayarları `dgxnode3` üstünde doğrulandı: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/FINAL_SETTINGS.md`
  - GPT-OSS-120B stable training ayarları `dgxnode4` üstünde doğrulandı: `/home/btankut/dgx-spark-gpt-oss-120b/FINAL_SETTINGS.md`
  - Node karar realignment: primary training target `dgxnode3`, inference/recovery target `dgxnode2`, alternative experimental track `dgxnode4`
  - `dgxnode3` üzerindeki proven Qwen path'in ShareGPT `conversations` formatı beklediği doğrulandı; repo içine bunun için resmi exporter eklendi.
  - Repo `dgxnode3` üstüne sync edildi ve preflight gate PASS verdi: `READY_FOR_TRAINING_GATE`
  - `final_train.jsonl` -> `final_train_sharegpt.jsonl` export'u node3 üzerinde `807/807` satırla PASS verdi.
  - External proven Qwen repo `/home/btankut/dgx-spark-unsloth-qwen3.5-training` aktif exported paket ile one-step smoke PASS verdi.
  - Node3 smoke sonucu: `train_loss=1.634`, `train_runtime=72.03s`, adapter `/outputs/hukuk_ai_active_807_smoke/lora_adapter`
  - `scripts/finetune/launch_dgxnode3_qwen_external.sh` ile repo-native node3 launcher donduruldu.
  - Aynı launcher ile detached full node3 run başlatıldı.
  - Full run pid: `869015`
  - Full run log: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/runtime_logs/hukuk_ai_active_807_run.log`
  - dgxnode3 detached full Qwen run başarıyla tamamlandı.
  - Full run sonucu: `3` epoch, `606` step, `train_runtime=1.007e+04`, `train_loss=0.5051`
  - Final adapter üretildi: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/lora_adapter`
  - `scripts/finetune/openai_generate_proxy.py` ile `/generate` -> `/v1/chat/completions` uyum katmanı eklendi.
  - node3 candidate adapter serve `:18000`, OpenAI proxy `:30002`, local SSH tunnel `127.0.0.1:30002` ve local candidate gateway `127.0.0.1:8002` ayağa kaldırıldı.
  - Candidate gateway smoke PASS verdi; `TBK m.49` için cited cevap döndü.
  - İlk `faz1-50` post-train eval koşusu timeout baskısı altında audit artefact üretti: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321.json`
  - Bu ilk koşu `11` hata/time-out içerdiği için promotion zincirinde resmi aday olarak kullanılmadı.
  - `t600` temiz rerun tamamlandı ve resmi post-train raw report donduruldu: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`
  - `t600` summary: citation `0.9000`, correct source `0.7713`, hallucination `0.0200`, refusal accuracy `1.0000`, avg response time `120302.8 ms`, error count `0`
  - Post-train evidence manifest üretildi: `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`
  - Promotion gate matched baseline manifest ile tekrar çalıştırıldı ve `READY` verdi.
  - Baseline/post-train runner parity korundu: her iki artefact da `runner=eval_runner`, `eval_family=faz1-50`
  - Resmi promotion contract geçilmiş olsa da candidate serving hattı Faz 1 canlı latency beklentisinin belirgin üzerinde kaldı.
  - Latency iyilestirme icin current node3 adapter icin resmi `merged_16bit` export yolu eklendi: `scripts/finetune/merge_unsloth_adapter.py`
  - Detached node3 merge launcher eklendi: `scripts/finetune/launch_dgxnode3_qwen_external_merge.sh`
  - `dgxnode3` uzerinde merged export detached olarak baslatildi; hedef artefact `outputs/hukuk_ai_active_807_run/merged_model`
  - Merge tamamlanir tamamlanmaz kullanilacak merged vLLM switchover launcher'i eklendi: `scripts/finetune/launch_dgxnode3_merged_vllm.sh`
  - Merged vLLM runtime'i local RAG zincirine baglayacak candidate gateway switchover launcher'i eklendi: `scripts/finetune/launch_local_candidate_gateway_node3_merged.sh`
  - Merged export helper dogrulandi: resmi Unsloth `merged_16bit` ciktisi gecersizse HF `merge_and_unload()` fallback ile tam checkpoint zorlanıyor.
  - Node3 merged checkpoint gecerli olarak dogrulandi: `outputs/hukuk_ai_active_807_run/merged_model` (~66G, 2 shard).
  - `vllm/vllm-openai:cu130-nightly` merged local checkpoint icin tokenizer safhasinda fail verdi: `TokenizersBackend does not exist`.
  - Faz 1 runtime family image'i `vllm-node-tf5:latest`, tokenizer fail'ini asti ve gercek weight load safhasina gecti.
  - Node3 unified-memory recovery icin launch oncesi `drop_caches` adimi resmilestirildi.
  - Test sonucu: `gpu_memory_utilization=0.50` modeli yukledi ama KV cache icin alan birakmadi; launcher default'u `0.70` olarak guncellendi.
  - Serving recovery kaydi eklendi: `coordination/node3-merged-vllm-recovery-2026-03-21.md`
  - Repo-native `0.70` relaunch basarili oldu; merged vLLM runtime `dgxnode3:30003` uzerinde health verdi.
  - Merged runtime load/serve kaniti: weight load `612.58s`, model load memory `65.53 GiB`, available KV cache `15.58 GiB`.
  - Local loopback tunnel acildi: `127.0.0.1:30003 -> dgxnode3:30003`
  - Local merged candidate gateway acildi: `127.0.0.1:8003`
  - Merged gateway health PASS verdi: `guardrails=enabled`, `retriever=milvus`
  - Timed cited smoke PASS verdi: `TBK m.49` sorusunda `15.889s`, citation=`TBK m.49`, blocked=`false`

  ### Sonraki Beklenen Çıktı
  - merged gateway icin kisa latency/quality slice.
  - eski node3 adapter/proxy yolu ile net serving karari.
  - node3 serving hattinda latency iyilestirme notu ve/veya alternatif serving stratejisi.
  - promotion sonucu ile Faz 1 canli latency farkinin net karar kaydi.
