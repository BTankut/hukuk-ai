# Open WebUI E2E + Teknik Borç Kapanış Özeti

**Tarih:** 2026-03-08  
**Subagent:** `hukuk-ai-openwebui-live-e2e` (sonnet)  
**Başlangıç:** ~07:50 GMT+3  
**Bitiş:** ~08:10 GMT+3

---

## Özet

Faz 1 kalite gate'leri geçildikten sonra açık kalan 3 teknik borç kapandı.  
Open WebUI tam E2E zinciri doğrulandı: **✅ PASS (4/4 test)**

---

## Çalıştırılan Komutlar

```bash
# 1. DGX vLLM durumu kontrol
curl -s http://192.168.12.243:30000/v1/models   # → Qwen3.5-35B-A3B-FP8 ✅

# 2. HTML cache fixture oluştur
cp /tmp/tbk_detail.html api-gateway/src/data_pipeline/fixtures/tbk_detail.html

# 3. Loader testi (HTML cache→651 madde)
api-gateway/.venv/bin/python3 -c "
  from src.data_pipeline.loaders.tbk_loader import TBKMevzuatLoader
  r = TBKMevzuatLoader().load(prefer_online=False)
  print(r.source_kind, len(r.document.articles))
"
# → html_cache 651 ✅

# 4. docker-compose port fix (3000→3001) + container başlat
cd api-gateway && docker compose up -d

# 5. E2E smoke (Python)
# Gateway health: ✅ 0.02s
# Models: ✅ hukuk-ai-poc
# Legal Q&A (RAG→DGX): ✅ 6.64s, citations=[TBK m.72]
# SSE Streaming: ✅ 5.23s, 13 chunk

# 6. Open WebUI container → Gateway bağlantı
docker exec hukuk-ai-open-webui curl -s \
  http://host.docker.internal:8000/v1/chat/completions \
  -d '{"model":"hukuk-ai-poc","messages":[...]}' 
# → 657 entity Milvus + DGX RAG yanıtı ✅

# 7. DGX startup script testi
bash scripts/dgx-vllm-ensure-running.sh
# → ✅ vLLM zaten çalışıyor (port 30000)
```

---

## Yapılan Değişiklikler

| Dosya | Değişiklik |
|-------|-----------|
| `api-gateway/src/data_pipeline/fixtures/tbk_detail.html` | YENİ — /tmp'den kopyalanan kalıcı TBK HTML cache (792K) |
| `api-gateway/src/data_pipeline/loaders/tbk_loader.py` | `DEFAULT_HTML_CACHE_PATH` sabit + `html_cache_path` param + load() docstring |
| `api-gateway/src/data_pipeline/indexing/pipeline.py` | `html_cache_path` pipeline.run() parametresi eklendi |
| `scripts/run_ingest.py` | HTML cache öncelikli yükleme; `--online` olmadan network çıkışı yok |
| `scripts/dgx-vllm-ensure-running.sh` | YENİ — M4 Max'ten DGX vLLM health+start scripti |
| `docs/DGX_VLLM_STARTUP.md` | YENİ — DGX vLLM başlatma/sorun giderme dokümantasyonu |
| `api-gateway/docker-compose.yml` | Port 3000→3001, restart=unless-stopped, Ollama=boş, DEFAULT_MODELS |
| `coordination/openwebui-live-smoke.md` | Güncellendi — PASS sonuçları ile yeniden yazıldı |
| `coordination/status.md` | Güncellendi — subagent tamamlandı, teknik borçlar kapatıldı |

---

## Smoke Testi Sonuçları

### API Seviyesi (Host)
| Test | Sonuç | Süre |
|------|-------|------|
| Gateway health → retriever=milvus | ✅ | 0.02s |
| /v1/models → hukuk-ai-poc | ✅ | 0.00s |
| Legal Q&A: "haksız fiil zamanaşımı" | ✅ | 6.64s |
| SSE Streaming (13 chunk) | ✅ | 5.23s |

### Container → Gateway Zinciri
| Test | Sonuç | Süre |
|------|-------|------|
| Container curl → /v1/models | ✅ | <1s |
| Container curl → /v1/chat (kira sorusu) | ✅ | ~25s |
| Open WebUI HTTP 200 (port 3001) | ✅ | - |

**Kira sorusu yanıtından örnek citations:**  
`TBK m.362` (fesih hakkı), `TBK m.325` (borç devamı), `TBK m.346` (ceza koşulu geçersizliği)

---

## DGX vLLM Durumu (Öğrenilen)

Container architecture:
- `vllm_head` container: Ray head node başlatır (`ray start --head ...`)
- vLLM prosesi: `docker exec -d` ile ayrıca başlatılmış (PID 3393579 host'ta)
- Restart policy: `no` → container restart = vLLM prosesi kaybolur
- Model yolu: `/root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/0b2752837483aa34b3db6e83e151b150c0e00e49`
- Log: container içi `/tmp/vllm_serve.log`

Faz 2 öncesi yapılması gereken: container CMD'si vLLM'i de başlatacak şekilde düzenlenmeli veya systemd servisi oluşturulmalı.

---

## Kalan Riskler

| Risk | Önem | Açıklama |
|------|------|---------|
| DGX vLLM idle shutdown | Orta | Plan doc: ~4-5dk istek gelmezse kapanabilir. Şimdilik `dgx-vllm-ensure-running.sh` ile kontrol. |
| Container restart policy=no | Orta | DGX reboot veya vllm_head restart → vLLM yeniden başlatma gerekir. Faz 2'de systemd/CMD fix. |
| Open WebUI UI testi (manuel) | Düşük | API zinciri doğrulandı. Tarayıcıdan port 3001'e manuel girip streaming chat görsel kontrolü yapılmadı. |
| tbk_detail.html güncelliği | Düşük | HTML cache 2026-03-08 snapshot'ı. Mevzuat değişikliğinde `--online` ile yenilenmeli. |
| Model snapshot hash sabitlenmiş | Düşük | dgx-vllm-ensure-running.sh içinde hardcoded; yeni model versiyonunda güncellenmeli. |

---

## Faz 1 Final Durumu

Tüm Faz 1 kalite gate'leri geçildi (**2026-03-08 06:22**).  
Teknik borçların tümü kapatıldı (**2026-03-08 08:10**).  
**Faz 1 PoC: TAMAMLANDI ✅**
