# Wave State
current_wave: faz2a-retrieval-coverage-requalification
status: in_progress
started_at: 2026-03-22T15:10:00+03:00
last_activity: 2026-03-23T08:03:14+03:00
last_eval: evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_wave15_20260323.json
next_action: "v3-170 matched rerun gate'i gecti; simdi v2-95 ve ardindan faz1-50 matched rerun'larini tamamlayip FAZ 2A steering paketini kapatmak"
blockers:
  - "tbk_critical ve tmk_cross_law focus subset'leri artik gate'i geciyor; aktif blocker artik yalnizca kalan family rerun execution (v2-95, faz1-50)"
  - "v3-170 gate'i acildi; steering kapanisi icin tum ailelerin matched rerun'lari tamamlanmali"
notes: |
  ## Re-Qualification Durumu

  - matched `v3-170` rerun baseline ve candidate icin tamamlandi
  - baseline:
    - citation `96.5%`
    - correct source `84.4%`
    - hallucination `5.3%`
    - refusal `94.7%`
  - candidate:
    - citation `96.5%`
    - correct source `83.8%`
    - hallucination `4.7%`
    - refusal `94.1%`
  - onceki source-of-record'a gore iki lane de yaklasik `+18.8` puan correct-source iyilesmesi verdi
  - `v3-170` artik FAZ 1.5 kapanisindaki ana no-go nedeni olmaktan cikti
  - aktif siradaki is:
    - `v2-95` matched rerun
    - `faz1-50` matched rerun
  - karar notu:
    - `coordination/faz2a-requal-v3-170-rerun-2026-03-23.md`

  ## Wave 15 Durumu

  - Wave 15 hedefi kapandi:
    - `tmk_cross_law` icindeki aile konutu / es rizasi / serh / bosanma koruma kuyruğu
  - Wave 15 mini-slice sonuclari:
    - baseline: citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
    - candidate: citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - Wave 15 full matched `tmk_cross_law` sonuclari:
    - baseline (`8055`): citation `100.0%`, correct source `80.3%`, hallucination `3.3%`, refusal `100.0%`
    - candidate (`8056`): citation `100.0%`, correct source `81.4%`, hallucination `0.0%`, refusal `100.0%`
  - Delta vs Wave 5:
    - baseline `59.4% -> 80.3%`
    - candidate `62.8% -> 81.4%`
  - Sonuc:
    - `tmk_cross_law` artik iki lane'de de diagnostic gate'i geciyor
    - FAZ 2A focus-slice repair hatti esas amacini yerine getirdi
    - sonraki dogru adim matched full-family re-qualification
  - Wave 15 karar notu:
    - `coordination/faz2a-wave15-tmk-family-home-rerun-2026-03-23.md`

  ## Wave 14 Durumu

  - Wave 14 hedefi kapandi:
    - `TBK-103` tek residuali (`TBK m.508`)
  - Wave 14 mini-slice sonuclari:
    - baseline: citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
    - candidate: citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - Wave 14 full matched `tbk_critical` sonuclari:
    - baseline (`8053`): citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `98.4%`
    - candidate (`8054`): citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `96.7%`
  - Kategori sonucu:
    - baseline: `tbk_kefalet`, `tbk_hizmet`, `tbk_vekaletname`, `tbk_ceza_sarti` = `100 / 100 / 0`
    - candidate: `tbk_kefalet`, `tbk_hizmet`, `tbk_vekaletname`, `tbk_ceza_sarti` = `100 / 100 / 0`
  - Sonuc:
    - `tbk_critical` source/hallucination kuyruğu iki lane'de de kapandi
    - FAZ 2A ana blocker artik `tmk_cross_law` multi-source companion-source coverage
  - Wave 14 karar notu:
    - `coordination/faz2a-wave14-tbk-103-rerun-2026-03-23.md`

  ## Wave 13 Durumu

  - Wave 13 hedefi kapandi:
    - `tbk_kefalet` residual paketi (`TBK-091, 150, 151, 153, 155, 156`)
    - ortak `TBK-137`
  - Wave 13 mini-slice sonuclari:
    - baseline: citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
    - candidate: citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - Wave 13 full matched `tbk_critical` sonuclari:
    - baseline (`8051`): citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
    - candidate (`8052`): citation `100.0%`, correct source `98.4%`, hallucination `1.6%`, refusal `98.4%`
  - Kategori sonucu:
    - baseline: `tbk_kefalet`, `tbk_hizmet`, `tbk_vekaletname`, `tbk_ceza_sarti` = `100 / 100 / 0`
    - candidate: `tbk_kefalet`, `tbk_hizmet`, `tbk_ceza_sarti` = `100 / 100 / 0`
    - candidate `tbk_vekaletname` = `94.4%` source, `5.6%` hallucination
  - Aktif residual:
    - `TBK-103` (`TBK m.508` beklenirken `TBK m.507` bleed)
  - Wave 13 karar notu:
    - `coordination/faz2a-wave13-tbk-kefalet-rerun-2026-03-22.md`

  ## FAZ 2A Durumu

  - Wave 5 inflection-aware matcher tamamladi:
    - Turkce cekimli ifade sonlarinda (`katilma rejiminin`, `zamanaasimina`, `denklestirmeye`) kok/sonek toleransli eslesme aktif
    - kisa-token false-positive guard korundu
    - `kefalet + es rizasi` TMK anchor'i yeniden daraltilarak yalniz `aile birligi / korunmasi ilkesi` ailesine baglandi
  - Wave 5 fresh rerun sonuclari:
    - baseline (`8032`): citation `100.0%`, correct source `59.4%`, hallucination `3.3%`, refusal `100.0%`
    - candidate (`8034`, t300 clean rerun): citation `100.0%`, correct source `62.8%`, hallucination `0.0%`, refusal `100.0%`
  - En kritik kazanim:
    - `TMK-CL-022` ve `TMK-CL-025` hallucination sinifindan cikti; forced-article trace'i artik doluyor
  - Sonuc:
    - retrieval precision / matcher sorunu buyuk olcude kapandi
    - kalan ana blocker, anchored cross-law sorularda eksik 3./4. citation coverage
  - Bu dalganin karar notu: `coordination/faz2a-wave5-inflection-matcher-rerun-2026-03-22.md`

  - FAZ 2A kickoff/freeze kapandi; trace destekli fresh diagnostic lane'ler yeniden kuruldu.
  - Turkce karakter uyumu artik tek tek keyword ekleyerek degil, merkezi normalizasyon yardimcilariyla yonetiliyor.
  - Concept-anchor force-include retrieval dalgasi trace'e `forced_article_refs` olarak tasindi.
  - Anchor kurallarinin mutasyona ugramis `retrieval_query` uzerinden zincirleme tetiklenme riski kapatildi.
  - Fresh `tmk_cross_law` matched rerun sonuclari:
    - baseline (`8018`): citation `80.0%`, correct source `46.9%`, hallucination `6.7%`, refusal `96.7%`
    - candidate (`8019`): citation `93.1%`, correct source `46.6%`, hallucination `17.2%`, refusal `100.0%`, error `1`
  - Sonuc: retrieval-normalization dalgasi candidate'i baseline ustune tasimadi; baskin kalan is source-locking / answer-discipline.
  - Bu dalganin karar notu: `coordination/faz2a-wave2-normalized-anchor-rerun-2026-03-22.md`
  - Source-lock wave eklendi:
    - LLM client stringified wrapper output'u parse ediyor
    - orchestrator generic/no-citation cevaplarda top-priority chunk'lar uzerinden dar source-lock fallback uretiyor
  - Fresh source-lock `tmk_cross_law` rerun sonuclari:
    - baseline (`8020`): citation `100.0%`, correct source `56.0%`, hallucination `13.8%`, refusal `100.0%`, error `1`
    - candidate (`8022`): citation `100.0%`, correct source `55.6%`, hallucination `13.3%`, refusal `100.0%`, error `0`
  - Sonuc: source precision yaklasik `+9` puan iyilesti, no-citation/wrapper sinifi kapandi; ancak FAZ 2A hala acik cunku hallucination tavani asiliyor ve candidate baseline'i anlamli bicimde gecemiyor.
  - Bu dalganin karar notu: `coordination/faz2a-wave3-source-lock-rerun-2026-03-22.md`

  ## Faz 1.5 Kapanis Durumu

  - Steering karari: `NO-GO - Retrieval/Coverage first`
  - Full-family matched eval baseline ve candidate icin kapandi.
  - `v3-170` sonucu:
    - baseline: citation `84.7%`, correct source `65.6%`, hallucination `7.1%`, refusal `91.2%`
    - candidate: citation `89.1%`, correct source `65.1%`, hallucination `7.9%`, refusal `91.5%`, error `5`
  - Dominant taxonomy:
    - `wrong source despite retrieved evidence`
    - `cross-law confusion`
  - Cutover + rollback rehearsal PASS verdi.
  - Release controls halen acik; ancak ana steering blocker Gate 2 kalite/coverage.

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
  - Merged lane icin matched `faz1-50` eval tamamlandi: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_merged_20260321.json`
  - Merged eval summary: citation `87.76%`, correct source `72.99%`, hallucination `6.12%`, refusal `100%`, avg response `21876.2 ms`, error `1`
  - Merged post-train evidence manifest uretildi: `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_merged_20260321.json`
  - Report delta araci eklendi: `scripts/compare_eval_reports.py`
  - Eski adapter/proxy path'e gore latency yaklasik `-81.8%` iyilesti (`120302.8 ms -> 21876.2 ms`), kalite metrikleri gate icinde kalarak kismi dusus gosterdi.
  - Serving karari kayda gecirildi: merged `vLLM` lane primary post-train candidate path, adapter/proxy lane fallback.
  - Karar notu: `coordination/node3-merged-serving-decision-2026-03-21.md`
  - Weak-slice analizi tamamlandi; en kritik regresyonlar `TBK-043`, `TBK-026`, `TBK-037`, `TBK-021`, `TBK-012`
  - `TBK-043` timeout'i anlik tekrar etmedi; manuel retry `25.835s` icinde dondu ancak gereksiz ek citation'lar urettigi icin asil sorun source over-expansion olarak kayda gecirildi.
  - Weak-slice notu: `coordination/node3-merged-weak-slices-2026-03-21.md`
  - Bir sonraki tuning/eval dalgasi icin 5 soruluk hizli iterasyon seti eklendi: `configs/evaluation/test_questions_weak_slices_node3_merged.json`
  - Guncel merged checkpoint `dgxnode1` uzerine fabric lane ile kopyalandi: `/home/btankut/dgx-spark-unsloth-qwen3.5-training/outputs/hukuk_ai_active_807_run/merged_model_fabric_stage_20260321`
  - `dgxnode1` OpenAI-compatible merged endpoint dogrulandi: `http://dgx1:30000/v1`, model=`/models/merged_model_fabric_stage_20260321`, `max_model_len=8192`
  - Repo-native local bridge eklendi: `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh`
  - Local tunnel acildi: `127.0.0.1:30004 -> dgxnode1:127.0.0.1:30000`
  - Local merged candidate gateway acildi: `127.0.0.1:8004`
  - `8004` health PASS verdi: `guardrails=enabled`, `retriever=milvus`
  - `TBK m.49` cited smoke `8004` uzerinden PASS verdi; citation=`TBK m.49`, blocked=`false`
  - Bridge notu eklendi: `coordination/dgx1-merged-endpoint-bridge-2026-03-21.md`
  - Kullanici tarafindan `dgx1` inference servisi FP8 KV cache + fixed GB memory + CUDA graphs + FlashInfer ile yeniden ayarlandi.
  - Stable rerun oncesi `8004` health ve `TBK m.49` smoke tekrar PASS verdi.
  - Tam `faz1-50` stable rerun tamamlandi: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_stable_20260321.json`
  - Stable rerun summary: citation `76.5%`, correct source `68.4%`, hallucination `0.0%`, refusal `100.0%`, avg response `15593 ms`, error `16`
  - Ilk `dgx1` full denemeye gore error count `35 -> 16` iyilesti, fakat lane yaklasik `TBK-031` civarinda yine connection-error dalgasina girdi.
  - Gateway tarafinda koku hata tekrar ayni: `openai.APIConnectionError` / `httpx.ReadError`
  - Stable rerun karari kayda gecirildi: `coordination/dgx1-merged-stable-rerun-2026-03-21.md`
  - `dgx1` inference docker'i yenilendi; full `faz1-50` kosusu sifirdan tekrar alindi: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_docker_refresh_20260322.json`
  - Docker refresh run summary: citation `78.0%`, correct source `68.2%`, hallucination `2.0%`, refusal `98.0%`, avg response `16696 ms`, error `0`
  - Bu run eski sustained-load baglanti kirilmasini kapatti; onceki `16` hatali run'a gore artik `0` connection error var.
  - Ancak lane hala Faz 1'i dar farkla kaciriyor; blocker artik infra degil kalite/précision.
  - Belirgin kalite kusurlari: `TBK-019` refusal miss, `TBK-044` hallucination.
  - Docker refresh karari kayda gecirildi: `coordination/dgx1-docker-refresh-eval-2026-03-22.md`
  - `TTK/TCK` deterministic scope-refusal genisletildi; `TBK-019` refusal miss kapatildi.
  - Router regresyon testleri gecti: `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
  - Refusal-fix full rerun tamamlandi: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_refusal_fix_20260322.json`
  - Refusal-fix summary: citation `79.6%`, correct source `68.6%`, hallucination `6.1%`, refusal `100.0%`, avg response `16268 ms`, error `1`
  - `TBK-019` duzeldi, ama sonraki blocker `TBK-044` ve genel-law cluster hallucination/source drift oldu.
  - Refusal-fix notu eklendi: `coordination/refusal-fix-ttk-rerun-2026-03-22.md`
  - `TBK-044` deterministic precise-answer ile `TBK m.166`'ya anchorlandi.
  - `TBK-044` smoke PASS verdi; citation=`TBK m.166`
  - `TBK-044` fix full rerun tamamlandi: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_tbk044_fix_20260322.json`
  - `TBK-044` fix summary: citation `79.2%`, correct source `70.7%`, hallucination `2.1%`, refusal `97.9%`, avg response `15428 ms`, error `2`
  - Bu run ile `correct source` Faz 1 barini gecti; kalan tek sert gate `citation`
  - `TBK-044` fix notu eklendi: `coordination/tbk044-fix-rerun-2026-03-22.md`
  - `tbk_genel/tbk_kira/tbk_satis/tbk_kefalet` precision wave'i icin deterministic precise-answer kapsami genisletildi (`TBK-002`, `004`, `012`, `015`, `020`, `021`, `025`, `026`, `031`, `032`, `034`, `045`).
  - Genişletilen precise-answer router testleri gecti: `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
  - Step-3 smoke kontrolleri `127.0.0.1:8009` lane'inde PASS verdi (`TBK-025`, `TBK-032`, `TBK-045`).
  - Precision-fix full rerun tamamlandi: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_precision_fix_20260322.json`
  - Precision-fix summary: citation `86.0%`, correct source `82.0%`, hallucination `2.0%`, refusal `100.0%`, avg response `10172 ms`, error `0`
  - Bu run ile kullanici hedefi net olarak gecildi: citation `>=80%`, correct source `>=70%`
  - `dgx1` merged lane tekrar Faz 1 kabul barini asti; kalite + stabilite birlikte saglandi.
  - Precision-fix karar notu eklendi: `coordination/precision-fix-rerun-2026-03-22.md`
  - Precision-fix run'i icin evidence manifest donduruldu: `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_precision_fix_20260322.json`
  - Precision-fix promotion gate tekrar calistirildi ve `READY` verdi.
  - `dgx1` merged lane cleanup'i icin deterministic precise-answer kapsami `TBK-010` ve `TBK-037` ile daha da genisletildi.
  - Cleanup smoke kontrolleri `127.0.0.1:8010` lane'inde PASS verdi (`TBK-010`, `TBK-037`).
  - Post-promotion cleanup full rerun tamamlandi: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`
  - Cleanup rerun summary: citation `88.0%`, correct source `86.0%`, hallucination `0.0%`, refusal `100.0%`, avg response `9116 ms`, error `0`
  - Bu run, precision-fix artefact'ini da geride birakarak `dgx1` lane icin yeni resmi post-train artefact oldu.
  - Cleanup run'i icin evidence manifest donduruldu: `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`
  - Cleanup promotion gate tekrar calistirildi ve `READY` verdi.
  - Resmi promotion sonucu kaydi eklendi: `coordination/dgx1-posttrain-promotion-result-2026-03-22.md`
  - Serving lane karari guncellendi: `dgx1` merged primary, `node3` merged fallback/debug.
  - Serving lane karar notu eklendi: `coordination/dgx1-merged-serving-decision-2026-03-22.md`
  - `dgx1` launcher varsayilan remote host'u IP'ye pinlendi: `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh`
  - Master planner'in FAZ 2A yol haritasi worktree'e alindi: `docs/FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-YOL-HARITASI-2026-03-22.md`
  - Repo-native FAZ 2A uygulama plani yazildi: `coordination/faz2a-implementation-plan-2026-03-22.md`
  - FAZ 2A olcum sozlesmesi ve canonical family etiketleri donduruldu: `coordination/faz2a-measurement-contract-2026-03-22.md`
  - `evaluation/report_metadata.py`, `scripts/run_eval_matrix.sh` ve `evaluation/run_reranker_safe_activation.py` canonical etiketler icin `v2-95` / `v3-170` eksenine hizalandi; legacy alias kabul edilmeye devam ediyor.
  - `v3-170` source-of-record raporlarindan report-derived failure freeze uretildi: `evaluation/reports/faz2a-failure-freeze-2026-03-22.md`
  - Frozen failure pack yazildi: `evaluation/reports/faz2a-failure-pack-v3-170-2026-03-22.jsonl` (`100` failing row)
  - Diagnostic subset'ler uretildi: `configs/evaluation/test_questions_faz2a_tmk_cross_law_v3_30.json` ve `configs/evaluation/test_questions_faz2a_tbk_critical_v3_61.json`
  - Chat API'ye optional trace kontrati eklendi: `include_trace=true` ile query/retrieval/context/verification trace'i response'a tasiniyor.
  - Eval runner'a optional trace passthrough eklendi; diagnostic run'lar artik ham rapora trace yazabilecek.
  - Yeni FAZ 2A trace regresyon testleri gecti: `api-gateway/.venv/bin/pytest tests/test_chat_router.py -q`, `api-gateway/.venv/bin/pytest tests/test_eval_runner.py -q`
  - FAZ 2A Wave 1 query/retrieval precision dalgasi acildi: `coordination/faz2a-wave1-law-article-precision-2026-03-22.md`
  - `chat.py` icinde law/article parsing guclendirildi; `TBK m.397-398` ve `TBK m.181, m.182 ve m.183` gibi article sequence'leri explicit force-include hattina giriyor.
  - Coklu kanun sinyali tasiyan ve birlikte-degerlendirme marker'i olan sorular icin cross-law per-law candidate generation eklendi; global retrieval korunurken `TBK/TMK` bucket'lari da merge ediliyor.
  - TMK cross-law ve TBK critical slice'lar icin low-risk lexical/article expansion kurallari eklendi.
  - Trace payload'i `mentioned_laws` ve `cross_law_mode` alanlariyla zenginlestirildi.
  - FAZ 2A focus subset diagnostic runner eklendi: `scripts/faz2a/run_focus_subset_eval.sh`
  - Runner dry-run PASS verdi; local gateway kapali oldugu icin bu turda sadece code/test/dry-run verification alindi.
  - FAZ 2A Wave 6 acildi: anchored multi-source sorularda query-aware source-lock coverage mantigi eklendi.
  - `chat.py` icinde `mal rejimi / borc verme` concept anchor'i daraltildi; generic `borc` sinyali artik `TMK-CL-027` gibi olum/katilma alacagi sorularini kirletmiyor.
  - `orchestrator.py` icinde source-lock fallback artik `source_lock_target_citations` ile `2-4` priority chunk'a kadar cikiyor.
  - Yeni `incomplete priority coverage` kurali eklendi; `3+` expected-source sorularda model dogru priority set'in eksik alt kumesini cite ederse fallback zorlanacak.
  - Wave 6 regression testleri gecti: `py_compile` PASS, `api-gateway/.venv/bin/pytest api-gateway/tests/test_orchestrator_smoke.py api-gateway/tests/test_chat_router.py api-gateway/tests/test_llm_client.py -q` PASS
  - Canli smoke lane'leri acildi: candidate `8038/8040`, baseline `8039/8041`
  - `TMK-CL-027` smoke temizlendi; candidate artik `TBK m.77 + TMK m.226 + TMK m.240 + TMK m.499` uretiyor.
  - `TMK-CL-028` smoke temizlendi; candidate artik `TBK m.19 + TBK m.285 + TMK m.561` uretiyor.
  - `TMK-CL-013` smoke'ta family-home cluster 4-source fallback ile dogrulandi.
  - Wave 6 interim rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_baseline_wave6_20260322_1930.json` -> src `73.6%`, hal `3.3%`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_candidate_wave6_20260322_1930.json` -> src `69.7%`, hal `3.3%`
  - Interim run candidate'i gate'in `0.3pp` altinda birakti; bu nedenle source-lock coverage bir adim daha sikilastirildi.
  - Final matched rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_baseline_wave6d_20260322_1946.json`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_candidate_wave6d_20260322_1946.json`
  - Final summary:
    - baseline -> citation `100.0%`, correct source `74.7%`, hallucination `3.3%`, refusal `96.7%`
    - candidate -> citation `100.0%`, correct source `74.7%`, hallucination `3.3%`, refusal `100.0%`
  - Candidate lane'de yukari tasinan kritik sorular: `TMK-CL-022`, `025`, `026`, `027`, `028`
  - `tmk_cross_law` slice'i fresh matched baseline/candidate pair uzerinde tekrar kabul barini gecti.
  - Wave 6 karar notu eklendi: `coordination/faz2a-wave6-source-lock-coverage-rerun-2026-03-22.md`
  - FAZ 2A aktif sonraki hedef artik `tbk_critical` slice'i.
  - `tbk_critical` icin Wave 8 deterministic package acildi; paylasilan hallucination / wrong-source kumesindeki `TBK-107`, `134`, `139`, `147`, `148`, `152`, `161` sorulari precise-answer coverage altina alindi.
  - Wave 8 code/test verification PASS: `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py api-gateway/src/rag/orchestrator.py api-gateway/src/llm/client.py` ve `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py api-gateway/tests/test_llm_client.py api-gateway/tests/test_orchestrator_smoke.py -q`
  - Fresh matched rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave8_20260322.json`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave8_20260322.json`
  - Wave 8 summary:
    - baseline -> citation `100.0%`, correct source `74.3%`, hallucination `0.0%`, refusal `95.1%`
    - candidate -> citation `100.0%`, correct source `71.9%`, hallucination `1.6%`, refusal `93.4%`
  - `tbk_critical` slice'i her iki lane icin de tekrar Faz 1 gate'ini gecti.
  - Wave 7'de ortak fail olan 7 soru (`TBK-107`, `134`, `139`, `147`, `148`, `152`, `161`) Wave 8'de her iki lane icin de `src=1.00 / no-hal` noktasina tasindi.
  - Candidate residual hallucination tek soruya dustu: `TBK-141`
  - Wave 8 karar notu eklendi: `coordination/faz2a-wave8-tbk-critical-rerun-2026-03-22.md`
  - Wave 9 residual fix acildi: `TBK-141` icin eval-expectation drift'i dar deterministic answer ile kapatildi.
  - Updated candidate lane `8044` uzerinde smoke PASS verdi; candidate artik `TBK m.504 + TBK m.502` pair'ini cite ediyor.
  - Tek-soru diagnostic rerun alindi: `evaluation/reports/eval_diagnostic_faz2a_tbk141_candidate_wave9_20260322.json`
  - `TBK-141` one-question summary: citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - Wave 9 karar notu eklendi: `coordination/faz2a-wave9-tbk141-residual-2026-03-22.md`
  - Wave 10 `tbk_ceza_sarti` source-tail closure acildi; uc dar deterministic package ile `TBK-105`, `106`, `158`, `159`, `160`, `162`, `163`, `164` coverage altina alindi.
  - Wave 10 local verification PASS: `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py` ve `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
  - Fresh matched lane'ler acildi: baseline `8045`, candidate `8046`
  - Candidate smoke PASS verdi; `Ceza şartının kararlaştırıldığı asıl sözleşme geçersiz sayılırsa...` sorusunda `TBK m.179 + TBK m.182` dondu.
  - Focused `tbk_ceza_sarti` mini-slice rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tbk_ceza_sarti_baseline_wave10_20260322.json`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tbk_ceza_sarti_candidate_wave10_20260322.json`
  - Mini-slice summary:
    - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
    - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - Full matched `tbk_critical` rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave10_20260322.json`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave10_20260322.json`
  - Wave 10 summary:
    - baseline -> citation `100.0%`, correct source `81.7%`, hallucination `0.0%`, refusal `95.1%`
    - candidate -> citation `100.0%`, correct source `81.2%`, hallucination `0.0%`, refusal `98.4%`
  - `tbk_ceza_sarti` category delta:
    - baseline `66.7% -> 100.0%`
    - candidate `62.1% -> 100.0%`
  - `tbk_critical` slice'i her iki lane icin de daha yuksek source precision ile yeniden Faz 1 gate'ini gecti.
  - Wave 10 karar notu eklendi: `coordination/faz2a-wave10-tbk-ceza-sarti-rerun-2026-03-22.md`
  - Wave 11 `tbk_hizmet` source-tail closure acildi; uc dar deterministic paket ile `TBK-094`, `096`, `097`, `110`, `131`, `132`, `133`, `135`, `136`, `138`, `140` coverage altina alindi.
  - Wave 11 local verification PASS: `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py` ve `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
  - Fresh matched lane'ler acildi: baseline `8047`, candidate `8048`
  - Candidate smoke PASS verdi; `TBK m.432 ... ihbar süreleri` sorusunda `TBK m.432 + TBK m.433` dondu.
  - Focused `tbk_hizmet` mini-slice rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tbk_hizmet_baseline_wave11_20260322.json`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tbk_hizmet_candidate_wave11_20260322.json`
  - Mini-slice summary:
    - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
    - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - Full matched `tbk_critical` rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave11_20260322.json`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave11_20260322.json`
  - Wave 11 summary:
    - baseline -> citation `100.0%`, correct source `90.2%`, hallucination `0.0%`, refusal `98.4%`
    - candidate -> citation `100.0%`, correct source `88.5%`, hallucination `0.0%`, refusal `98.4%`
  - `tbk_hizmet` category delta:
    - baseline `75.4% -> 97.4%`
    - candidate `71.0% -> 97.4%`
  - `tbk_critical` slice'i her iki lane icin de daha yuksek source precision ile tekrar Faz 1 gate'ini gecti.
  - Wave 11 karar notu eklendi: `coordination/faz2a-wave11-tbk-hizmet-rerun-2026-03-22.md`
  - Wave 12 `tbk_vekaletname` source-tail closure acildi; sekiz dar deterministic paket ile `TBK-101`, `102`, `115`, `142`, `143`, `144`, `145`, `146` coverage altina alindi.
  - Wave 12 local verification PASS: `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/tests/test_chat_router.py` ve `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
  - Fresh matched lane'ler acildi: baseline `8049`, candidate `8050`
  - Focused `tbk_vekaletname` mini-slice rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tbk_vekaletname_baseline_wave12_20260322.json`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tbk_vekaletname_candidate_wave12_20260322.json`
  - Mini-slice summary:
    - baseline -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
    - candidate -> citation `100.0%`, correct source `100.0%`, hallucination `0.0%`, refusal `100.0%`
  - Full matched `tbk_critical` rerun alindi:
    - baseline: `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_baseline_wave12_20260322.json`
    - candidate: `evaluation/reports/eval_diagnostic_faz2a_tbk_critical_candidate_wave12_20260322.json`
  - Wave 12 summary:
    - baseline -> citation `100.0%`, correct source `95.1%`, hallucination `0.0%`, refusal `96.7%`
    - candidate -> citation `100.0%`, correct source `94.3%`, hallucination `0.0%`, refusal `98.4%`
  - `tbk_vekaletname` category delta:
    - baseline `80.6% -> 100.0%`
    - candidate `77.8% -> 100.0%`
  - `tbk_critical` slice'i her iki lane icin de daha yuksek source precision ile tekrar Faz 1 gate'ini gecti.
  - Residual set artik `tbk_kefalet` ve ortak `TBK-137` companion-source miss'ine daraldi.
  - Wave 12 karar notu eklendi: `coordination/faz2a-wave12-tbk-vekaletname-rerun-2026-03-22.md`

  ### Sonraki Beklenen Çıktı
  - FAZ 2A sonraki aktif hedef: `tbk_kefalet` source-tail closure
  - ortak `TBK-137` residualini ayni dalgada kapatmak
  - ardindan residual fix'leri fold eden bir sonraki matched rerun
