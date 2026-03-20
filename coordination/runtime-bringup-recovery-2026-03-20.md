# Runtime Bring-Up Recovery — 2026-03-20

## Amaç

Temiz klonlanan `/Users/btmacstudio/Projects/hukuk-ai` üzerinde, backup klasörünü yalnız referans olarak kullanıp canlı servis zincirini yeniden ayağa kaldırmak.

## Sonuç Özeti

- `localhost:19530` Milvus hattı aynı Docker volume'larla başarıyla ayağa kaldırıldı.
- `localhost:8081` embedding service başarıyla ayağa kaldırıldı.
- `localhost:8000` API gateway başarıyla ayağa kaldırıldı.
- `localhost:3001` Open WebUI zaten çalışır durumdaydı.
- DGX tarafındaki eski varsayım (`192.168.12.243:30000`, container=`vllm_head`) artık güncel değil.
- Bu turda ajan probunda görülen ve gateway env'ine yansıtılan aday DGX runtime: container=`qwen35-base-eval`, port=`30001`, model id=`qwen35-base`.
- DGX endpoint'i ilk sağlık probunda cevap verdi, ancak sonrasında hem LAN HTTP hem SSH erişimi timeout vermeye başladı. Bu yüzden tam E2E generation çağrısı kararlı biçimde tamamlanamadı.
- Kullanıcı yönlendirmesi sonrası yeni fallback runtime doğrulandı: `dgxnode2` (`192.168.12.236:8080/v1`), model=`Qwen3.5-35B-A3B-Q8_0.gguf`, server=`llama.cpp`.
- Bu fallback runtime ile doğrudan OpenAI-compatible chat çağrısı geçti.
- Gateway de bu runtime'a çevrilerek kısa RAG smoke PASS alındı.
- Ancak `GUARDRAILS_ENABLED=true` iken NeMo guardrails yeni runtime üzerinde false-positive refusal üretiyor; bu nedenle smoke doğrulaması guardrails kapalı modda tamamlandı.

## Backup vs Temiz Repo

- Backup içindeki `scripts/dgx-vllm-ensure-running.sh`, `.env.example` ve `api-gateway/docker-compose.milvus.yml` dosyaları güncel repo ile içerik olarak aynıydı.
- Bu nedenle backup'tan repo içine dosya taşımaya ihtiyaç olmadı.
- Esas fark kodda değil runtime ortamındaydı:
  - temiz klonda `api-gateway/.venv` yoktu,
  - DGX runtime eski dokümandaki container/port'tan sapmıştı,
  - gateway startup için gerekli `en_core_web_lg` spaCy modeli kurulu değildi.

## Doğrulanan Runtime Gerçekleri

### Lokal

- Docker volume'lar mevcuttu:
  - `api-gateway_milvus-data`
  - `api-gateway_milvus-etcd`
  - `api-gateway_milvus-minio`
- Milvus collection'ları:
  - `mevzuat` (`666`)
  - `mevzuat_bge_m3_shadow` (`3390`)
  - `mevzuat_e5_shadow` (`3390`)
- Embedding service modeli:
  - `intfloat/multilingual-e5-large-instruct`
  - dimension=`1024`

### DGX

- Ajan tarafından raporlanan ilk başarılı probe:
  - `GET http://192.168.12.243:30001/v1/models`
  - model id=`qwen35-base`
- Ajan raporunda görülen aktif container:
  - `qwen35-base-eval`
- Eski script default'u bu host için başarısız oldu:
  - container=`vllm_head`
  - port=`30000`
- Kullanıcı sonrası doğrulanan fallback runtime:
  - `GET http://192.168.12.236:8080/v1/models`
  - model id=`Qwen3.5-35B-A3B-Q8_0.gguf`
  - `GET/POST` çağrıları LAN IP üzerinden başarılı, fabric IP (`192.168.101.12`) timeout
  - OpenAI client + `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` uyumlu

## Uygulanan Bring-Up Sırası

### 1. Milvus

```bash
docker compose -f api-gateway/docker-compose.milvus.yml up -d
```

### 2. API Gateway Python ortamı

```bash
uv venv --python 3.12.9 api-gateway/.venv
uv pip install --python api-gateway/.venv/bin/python -e 'api-gateway[dev,milvus]'
api-gateway/.venv/bin/python -m spacy download en_core_web_lg
```

### 3. Embedding Service

Ortak interpreter olarak `api-gateway/.venv` kullanıldı:

```bash
cd services/embedding-service
../../api-gateway/.venv/bin/python src/main.py
```

Beklenen sağlık:

```bash
curl http://localhost:8081/health
```

### 4. API Gateway

`embedding-service` ile tutarlı retrieval için `mevzuat_e5_shadow` kullanıldı:

```bash
cd api-gateway
DGX_BASE_URL=http://192.168.12.243:30001/v1 \
DGX_MODEL=qwen35-base \
DGX_API_KEY=not-needed \
MILVUS_ENABLED=true \
MILVUS_URI=http://localhost:19530 \
MILVUS_COLLECTION=mevzuat_e5_shadow \
EMBEDDING_BACKEND=remote \
EMBEDDING_BASE_URL=http://localhost:8081/v1 \
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
EMBEDDING_DIM=1024 \
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Beklenen sağlık:

```bash
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/models
```

## Gateway Startup Notu

- Gateway ilk denemede Presidio startup'ında düştü.
- Kök neden: `PresidioMasker.__post_init__()` analyzer/anonymizer'ı `presidio_enabled` ayarından bağımsız kuruyor.
- Bu yüzden `PRESIDIO_ENABLED=false` tek başına startup blocker'ını çözmüyor.
- Runtime düzeltmesi olarak `en_core_web_lg` modeli kuruldu ve gateway bundan sonra başarıyla açıldı.

## Kalan Bloker

- `192.168.12.243` üzerindeki eski / drifting runtime hâlâ kararsız.
- Yeni çalışan runtime `192.168.12.236:8080/v1` üzerinde generation katmanı hazır.
- Asıl yeni blocker guardrails uyumluluğu:
  - `GUARDRAILS_ENABLED=true` iken kısa hukuki soruda false-positive refusal (`I'm sorry, I can't respond to that.`)
  - `GUARDRAILS_ENABLED=false` iken aynı soru için gateway doğru, kaynaklı yanıt üretiyor.
- Sonuç: lokal RAG + new LLM hattı hazır; safe-activation canlı koşusu öncesi guardrails runtime uyumu ayrı karar/iyileştirme işi olarak ele alınmalı.

## Sonraki Adım

1. `192.168.12.236:8080/v1` runtime'ını geçici değilse resmi live endpoint olarak kayda geçir.
2. Guardrails false-positive'ı bu runtime üzerinde izole et ve karar ver:
   - ya extraction/prompt/parser uyarlaması yap,
   - ya da reranker canlı sweep'i guardrails kapalı baseline olarak koş.
3. Ardından `evaluation/run_reranker_safe_activation.py --live` çalıştır.
