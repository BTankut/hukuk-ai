# AI Hukuk Asistanı

AI Hukuk Asistanı, Türk hukuku için mevzuat-first yaklaşımıyla tasarlanmış bir Retrieval-Augmented Generation (RAG) proof-of-concept projesidir. Faz 1 kapsamında hedef, mevzuat temelli sorulara kaynak gösteren, hallüsinasyon oranı düşük, canlı ortamda doğrulanmış bir hukuk asistanı hattı oluşturmaktır.

## Durum

2026-03-08 itibarıyla Faz 1 kabul kriterleri canlı hat üzerinde karşılanmıştır.

Canlı değerlendirme özeti:

- Citation rate: 88%
- Correct source rate: 77.07%
- Hallucination rate: 8%
- Refusal accuracy: 90%
- Ortalama yanıt süresi: 9.36 saniye

Faz 1 kapsamında aşağıdaki ana bileşenler tamamlanmıştır:

- FastAPI tabanlı API Gateway
- Milvus tabanlı mevzuat retrieval hattı
- Embedding servisi
- Verification engine
- Open WebUI ile uçtan uca canlı smoke doğrulaması
- 50 soruluk canlı evaluation seti

## Mimari

Sistem iki ana makine üzerinde çalışır:

- DGX Spark (`192.168.12.243`): vLLM inference
- M4 Max: API Gateway, Embedding Service, Milvus, Open WebUI ve geliştirme ortamı

Başlıca uç noktalar:

- API Gateway: `http://localhost:8000`
- Embedding Service: `http://localhost:8081`
- Open WebUI: `http://localhost:3001`
- DGX vLLM: `http://192.168.12.243:30000/v1`
- Milvus: `http://localhost:19530`

## Teknoloji Yığını

- Python 3.11+
- FastAPI
- vLLM
- Milvus
- sentence-transformers
- NeMo Guardrails
- Open WebUI
- pytest

Model:

- `Qwen/Qwen3.5-35B-A3B-FP8`

Embedding:

- `intfloat/multilingual-e5-large-instruct`

## Dizin Yapısı

```text
hukuk-ai/
├── README.md
├── .env.example
├── api-gateway/
├── configs/
├── coordination/
├── docs/
├── evaluation/
├── scripts/
└── services/
```

Önemli dizinler:

- `api-gateway/`: Ana uygulama, RAG hattı, router'lar, testler
- `services/embedding-service/`: Embedding servisi
- `configs/evaluation/`: Soru setleri ve değerlendirme girdileri
- `evaluation/`: Evaluation runner, metrik hesapları ve raporlar
- `coordination/`: Planlama, watchdog ve kapanış raporları
- `docs/`: Operasyon ve mimari notları
- `scripts/`: Yardımcı operasyon scriptleri

## Hızlı Başlangıç

### 1. API Gateway bağımlılıkları

```bash
cd api-gateway
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev,milvus]
```

### 2. Embedding Service bağımlılıkları

```bash
cd services/embedding-service
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

### 3. DGX vLLM erişimini doğrula

```bash
bash scripts/dgx-vllm-ensure-running.sh --wait
```

Ayrıntılı prosedür için:

- `docs/DGX_VLLM_STARTUP.md`

### 4. Open WebUI başlat

```bash
docker compose -f api-gateway/docker-compose.yml up -d
```

### 5. Canlı sağlık kontrolleri

```bash
curl http://localhost:8000/v1/health
curl http://localhost:8081/health
curl http://localhost:3001
curl http://192.168.12.243:30000/v1/models
```

## Veri Hattı

Faz 1 veri hattı mevzuat-first yaklaşımıyla ilerler.

Mevcut kapsam:

- TBK ana veri seti
- TMK seçili madde kapsaması
- Milvus üzerinde canlı indeks

TBK loader artık geçici `/tmp` dosyasına bağlı değildir. Kalıcı HTML fixture şu dizindedir:

- `api-gateway/src/data_pipeline/fixtures/tbk_detail.html`

İndeksleme komutları:

```bash
python scripts/run_ingest.py
python scripts/run_ingest.py --online
```

## Test ve Doğrulama

Tüm API Gateway testleri:

```bash
cd api-gateway
. .venv/bin/activate
pytest -q
```

Canlı evaluation:

```bash
./evaluation/run_eval.sh --live
```

Önemli raporlar:

- `evaluation/reports/eval_live_20260308_reindex.json`
- `evaluation/reports/eval_live_20260308_080601.json`

Koordinasyon ve kapanış raporları:

- `coordination/status.md`
- `coordination/openwebui-e2e-closeout-2026-03-08.md`
- `coordination/eval50-verification-2026-03-08.md`
- `coordination/reindex-recall-fix-2026-03-08.md`

## Faz 1 Kapsamı ve Sınırlar

Faz 1 bilinçli olarak dar tutulmuştur.

Dahil:

- mevzuat-first baseline
- dense retrieval + metadata filter
- strict verification yaklaşımı
- canlı evaluation ve canlı smoke testleri

Hariç / sonraki faz:

- YİM tam entegrasyonu
- Resmi Gazete collection hattı
- hybrid BM25 retrieval
- daha gelişmiş reranker optimizasyonu
- genişletilmiş kapsam dışı hukuk alanları

## Mevcut Açık Konular

Faz 1 kabul edilmiş olsa da aşağıdaki konular geliştirme adayları olarak açıktır:

- reranker entegrasyonu ve optimizasyonu
- TBK-001 terminoloji farkı
- TBK-011 retrieval gap
- kapsam dışı TMK sorularında refusal davranışının sertleştirilmesi

Bu konular Faz 2 hazırlık backlog'unda izlenmektedir.

## Lisans ve Kullanım Notu

Bu repo şu anda PoC ve iç geliştirme odağındadır. Hukuki tavsiye verme amacı taşımaz. Üretilen yanıtlar kaynaklı araştırma desteği amacıyla değerlendirilmelidir.
