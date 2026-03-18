# Wave State
current_wave: faz3-lora-v2-training
status: running
started_at: 2026-03-18T07:55:00+03:00
last_activity: 2026-03-18T08:47:00+03:00
last_eval: evaluation/reports/eval_faz3_base.json
next_action: "LoRA v2 eğitimi tamamlanınca merge → serve → 170q eval (FT vs base)"
blockers: []
notes: |
  ## Faz 3 — LoRA v2 Eğitimi (1076 avukat onaylı veri)
  
  ### Önceki Eğitim (v1) — GEÇERSİZ
  - 388 sentetik veri ile eğitildi (sft_training_v1.jsonl)
  - 1076'lık avukat onaylı final_train.jsonl KULLANILMADI
  - Eski dosyalar silindi (v1, v3, merged-v3)
  
  ### Yeni Eğitim (v2) — ÇALIŞIYOR
  - Veri: final_train.jsonl (1076 kayıt, avukat onaylı/düzeltmeli)
  - dgxnode2 üzerinde Axolotl + LoRA (r=16, q_proj+v_proj)
  - 405 step toplam (3 epoch), ~30s/step
  - Şu an: step 86/405 (%21), loss=0.63, epoch 0.59
  - GPU: 86.7GB / 121.7GB, eğitim stabil
  - Tahmini bitiş: ~2.5 saat sonra (~10:30)
  
  ### Eğitim Sonrası Plan
  1. Merge (LoRA → merged model)
  2. Serve (vLLM cu130-nightly, enforce-eager)
  3. 170q V3 eval (FT vs base karşılaştırma)
  4. Base eval zaten tamamlandı: src=50.9%, hal=26.5%, ref=94.1%, cit=88.8%
  
  ### Bilinen Sorunlar
  - Merged model torch.compile ile crash → enforce-eager zorunlu
  - LoRA adapter vLLM'de IndexError → merged model serve edilmeli
  - dgxnode1'de base model eval tamamlandı (170q, 0 error)
