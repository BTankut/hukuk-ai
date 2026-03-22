# AI Hukuk Asistanı

AI Hukuk Asistanı, Türk hukuku için mevzuat-first RAG ve gate-first fine-tuning disipliniyle geliştirilen bir hukuk asistanı reposudur. Repo yalnızca bir model servisi değil; retrieval, guardrails, evaluation, training readiness ve promotion karar zincirini birlikte taşır.

## Güncel Durum

Bu repo için iki ayrı referans fotoğraf vardır:

| Lane | Tarih | Citation | Correct Source | Hallucination | Refusal | Avg Response |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Frozen Faz 1 baseline | 2026-03-08 | 88.0% | 77.1% | 8.0% | 90.0% | 9.36s |
| Resmi promoted aday (`dgx1` merged cleanup) | 2026-03-22 | 88.0% | 86.0% | 0.0% | 100.0% | 9.116s |

Resmi güncel aday artefact'ları:

- raw report: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`
- evidence manifest: `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`
- promotion sonucu: `coordination/dgx1-posttrain-promotion-result-2026-03-22.md`
- serving lane kararı: `coordination/dgx1-merged-serving-decision-2026-03-22.md`

Aktif repo gerçekliği:

- Faz 1 baseline korunur; yeni aday baseline yerine örtük production kabul edilmez.
- Primary promoted lane: `dgx1` üzerindeki merged fine-tuned model.
- Fallback/debug lane: `node3` merged serving hattı.
- Reranker varsayılanı: `off`
- Guardrails varsayılanı: `safe-scope minimal`
- Retrieval varsayılanı: `top_k=20` + explicit article force-include
- Canonical active training package: `data/finetune/sft/final_train.jsonl` (`807` satır, `807` unique soru)

## Mimari

Çalışan zincir mantıksal olarak şöyledir:

```text
Client / Eval Runner
        |
        v
API Gateway (FastAPI, localhost:8000 veya candidate lane 8004)
        |
        +--> Guardrails
        +--> Milvus Retriever (localhost:19530)
        +--> Embedding Service (localhost:8081)
        |
        v
Remote OpenAI-compatible LLM endpoint
```

Lane ayrımı:

- Baseline / default gateway lane:
  `localhost:8000` üzerinde çalışan genel gateway; hangi upstream LLM'e gideceği env ile belirlenir.
- Promoted candidate lane:
  `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh` ile açılan `localhost:8004` gateway'i; `dgx1` merged modeli loopback tunnel üzerinden kullanır.
- Node3 fallback lane:
  `scripts/finetune/launch_local_candidate_gateway_node3_merged.sh` ile açılan `localhost:8003` gateway'i.

Ana servisler:

- API Gateway: `api-gateway/`
- Embedding Service: `services/embedding-service/`
- Milvus compose: `api-gateway/docker-compose.milvus.yml`
- Evaluation runner: `evaluation/eval_runner.py`
- Training / promotion gate: `scripts/check_training_readiness.py`

## Repo Haritası

- `api-gateway/`: FastAPI gateway, RAG orchestration, guardrails, router testleri
- `services/embedding-service/`: OpenAI-compatible embedding servisi
- `configs/evaluation/`: Faz 1, 95q, 170q ve weak-slice soru setleri
- `evaluation/`: eval runner, raporlar, evidence manifest'ler
- `data/finetune/`: canonical train/eval veri paketleri
- `scripts/`: ingest, eval, dataset build, readiness gate ve fine-tune yardımcıları
- `coordination/`: karar notları, milestone kayıtları, promotion ve recovery raporları
- `docs/`: ana referans raporlar, runbook'lar, quality gate dokümanları
- `WAVE_STATE.md`: dalga seviyesi durum ve karar özeti

## Kurulum

Önkoşullar:

- Python 3.11+
- Docker / Docker Compose
- Milvus için lokal container çalıştırabilme
- Remote inference kullanacaksanız ilgili DGX endpoint'ine erişim

### 1. API Gateway ortamı

```bash
cd api-gateway
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev,milvus]
```

### 2. Embedding Service ortamı

```bash
cd services/embedding-service
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

### 3. Milvus'u başlat

```bash
docker compose -f api-gateway/docker-compose.milvus.yml up -d
```

### 4. Embedding Service'i başlat

```bash
cd services/embedding-service
. .venv/bin/activate
python -m uvicorn src.main:app --host 127.0.0.1 --port 8081 --log-level info
```

### 5. Baseline / genel gateway lane'ini başlat

Bu lane upstream LLM endpoint'ini env ile alır. Aşağıdaki örnek, remote OpenAI-compatible bir servisle gateway'i ayağa kaldırır.

```bash
cd api-gateway
. .venv/bin/activate

DGX_BASE_URL=http://<openai-compatible-endpoint>/v1 \
DGX_MODEL=<model-id> \
MILVUS_ENABLED=true \
MILVUS_URI=http://localhost:19530 \
MILVUS_COLLECTION=mevzuat_e5_shadow \
EMBEDDING_BACKEND=remote \
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
RERANKER_ENABLED=false \
GUARDRAILS_ENABLED=true \
PRESIDIO_ENABLED=false \
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

`.env.example` temel gateway ayarları için bir başlangıç noktasıdır; promoted lane için gereken model/endpoint genellikle ayrıca override edilir.

### 6. Promoted `dgx1` merged lane'ini başlat

Repo içindeki resmi candidate bridge script'i:

```bash
bash scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh
```

Varsayılan davranış:

- remote host: `btankut@192.168.12.243`
- remote vLLM port: `30000`
- local tunnel: `127.0.0.1:30004`
- local candidate gateway: `127.0.0.1:8004`
- model id: `/models/merged_model_fabric_stage_20260321`

İhtiyaç halinde env override edebilirsin:

```bash
REMOTE_HOST=btankut@192.168.12.243 \
REMOTE_VLLM_PORT=30000 \
LOCAL_TUNNEL_PORT=30004 \
GATEWAY_PORT=8004 \
MODEL_NAME=/models/merged_model_fabric_stage_20260321 \
bash scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh
```

### 7. Sağlık kontrolleri

```bash
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8000/v1/health
curl http://127.0.0.1:8004/v1/health
curl http://127.0.0.1:30004/v1/models
```

Opsiyonel UI kullanımı için:

```bash
docker compose -f api-gateway/docker-compose.yml up -d
```

## Evaluation

Canonical eval aileleri:

- `faz1-50`: resmi kabul ve promotion karşılaştırma seti
- `phase3-95`: hardening / genişletilmiş slice
- `faz2-170`: stres / misuse / training sınırı

### Matrix plan modu

```bash
./scripts/run_eval_matrix.sh
./scripts/run_eval_matrix.sh all
```

### Canlı Faz 1 eval örnekleri

Baseline lane:

```bash
MODEL_REF=gateway-api \
CHECKPOINT_REF=gateway-live \
GIT_COMMIT=$(git rev-parse --short HEAD) \
./scripts/run_eval_matrix.sh faz1-50 --run --live --url http://127.0.0.1:8000
```

Promoted `dgx1` candidate lane:

```bash
MODEL_REF=hukuk-ai-sft-qwen35-807 \
CHECKPOINT_REF=dgx1-merged-post-promotion-cleanup-20260322 \
GIT_COMMIT=$(git rev-parse --short HEAD) \
./scripts/run_eval_matrix.sh faz1-50 --run --live --url http://127.0.0.1:8004
```

Rapor farkı görmek için:

```bash
python3 scripts/compare_eval_reports.py \
  --baseline evaluation/reports/eval_live_20260308_080601.json \
  --candidate evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json
```

## Training, Readiness ve Promotion

Bu repo'da fine-tune zinciri doğrudan “train et ve bakarız” şeklinde ilerlemez. Önce canonical veri paketi ve evidence gate geçmelidir.

### Canonical training package

- aktif train dosyası: `data/finetune/sft/final_train.jsonl`
- aktif boyut: `807`
- unique soru sayısı: `807`
- builder: `scripts/build_training_dataset.py`

### Dataset'i yeniden üret

```bash
python3 scripts/build_training_dataset.py --dry-run
python3 scripts/build_training_dataset.py
```

### Pre-train readiness gate

```bash
python3 scripts/check_training_readiness.py \
  --mode preflight \
  --expected-eval-family faz1-50 \
  --max-question-duplicate-excess 0 \
  --baseline-evidence-path evaluation/reports/evidence_baseline_faz1_50_20260308.json
```

### Fine-tune config doğrulama

```bash
python3 scripts/finetune/check_finetune_config.py \
  --config configs/finetune/unsloth_sft_qwen35_35b_a3b.json
```

### Promotion gate

```bash
python3 scripts/check_training_readiness.py \
  --mode promotion \
  --expected-eval-family faz1-50 \
  --max-question-duplicate-excess 0 \
  --baseline-evidence-path evaluation/reports/evidence_baseline_faz1_50_20260308.json \
  --post-train-evidence-path evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json
```

### Fine-tune / merge / serving runbook'ları

- readiness ve gate kuralları: `docs/finetune/TRAINING_READINESS.md`
- training geçmişi ve audit: `docs/finetune/TRAINING_LOG.md`
- proven external node3 eğitim hattı: `docs/finetune/dgxnode3-qwen-external-runbook.md`
- inference notları: `docs/INFERENCE_SETUP.md`

## Önemli Referanslar

- Faz 1 ana rapor: `docs/FAZ1-FINAL-RAPOR.md`
- Faz 1 cevap raporu: `docs/FAZ1-FINAL-RAPOR-CEVAP-2026-03-22.md`
- quality gate workflow: `docs/quality_gate_workflow.md`
- current wave özeti: `WAVE_STATE.md`
- promoted lane kararı: `coordination/dgx1-merged-serving-decision-2026-03-22.md`
- promotion sonucu: `coordination/dgx1-posttrain-promotion-result-2026-03-22.md`

## Bilinen Kararlar

- Reranker şu an production default değil; karar `keep-off`.
- Guardrails strict-facts hattı varsayılan değil; stabil safe-default korunuyor.
- Promotion kararları yalnız matched eval family + matched runner + evidence manifest ile geçerlidir.
- `final_train.jsonl` dışındaki türetilmiş dataset görünümleri ikinci kaynak değil, yalnız uyumluluk/export çıktısıdır.

## Uyarı

Bu repo iç kullanım ve kontrollü araştırma amaçlıdır. Hukuki tavsiye yerine geçmez. Üretilen yanıtlar mevzuat araştırma desteği olarak değerlendirilmelidir; doğrudan profesyonel hukuki görüş olarak kullanılmamalıdır.
