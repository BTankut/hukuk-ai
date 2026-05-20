# DGX Spark — vLLM Startup Prosedürü

**Son güncelleme:** 2026-03-08  
**Model:** `Qwen/Qwen3.5-35B-A3B-FP8`  
**DGX node:** `dgxnode1` — `192.168.12.243`  
**Port:** `30000`

---

## Mimari Özet

```
M4 Max (orkestrasyon)
  └── API Gateway (localhost:8000)
        └── DGX Spark — vllm_head container (192.168.12.243:30000)
                └── vLLM serve process (OpenAI-compat API)
```

**Önemli:** vLLM, `vllm_head` container içinde `docker exec -d` ile başlatılır.  
Container yalnızca Ray head node'u başlatır; vLLM prosesi **container restart'ta otomatik başlamaz**.

---

## Container Bilgileri

| Parametre | Değer |
|-----------|-------|
| Legacy wrapper container | `vllm_head` |
| Güncel direct-serve container (tercih) | `vllm_qwen35_lowmem` |
| Alternatif direct-serve container | `vllm_qwen35moe` |
| Son gözlenen eval drift'i | `qwen35-base-eval` (`30001`) |
| Image | `vllm-node*` |
| Restart policy | `no` (otomatik yeniden başlama YOK) |
| Network mode | `host` |
| Model yolu (container içi) | `/root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/0b2752837483aa34b3db6e83e151b150c0e00e49` |
| Direct-serve log | `docker logs <container>` |
| Wrapper log | `/tmp/vllm_serve.log` (container içi `/tmp`) |

**Not:** `scripts/dgx-vllm-ensure-running.sh` artık sırasıyla `vllm_qwen35_lowmem`, `vllm_head`, `vllm_qwen35moe`, `qwen35-base-eval` adaylarını dener. Güncel DGX düzeninde direct-serve container'lar için `docker start` yeterlidir; `docker exec` gerekmez. `qwen35-base-eval` gibi `30000` dışı runtime'lar için `DGX_PORT=30001` override verilmelidir.

---

## Hızlı Başlat (M4 Max'ten)

```bash
# Çalışıyor mu kontrol et + gerekirse başlat (beklemez)
bash scripts/dgx-vllm-ensure-running.sh

# Başlat ve sağlıklı olana kadar bekle (~4 dakika)
bash scripts/dgx-vllm-ensure-running.sh --wait

# Eğer eval runtime `qwen35-base-eval` / `30001` üstündeyse:
DGX_PORT=30001 DGX_CONTAINER=qwen35-base-eval bash scripts/dgx-vllm-ensure-running.sh --wait
```

---

## Manuel Prosedür (Adım Adım)

### 1. Container'ın Ayakta Olup Olmadığını Kontrol Et

```bash
ssh btankut@192.168.12.243 "docker ps | egrep 'vllm_qwen35_lowmem|vllm_head|vllm_qwen35moe'"
```

Beklenen çıktı:
```
NAMES               STATUS
vllm_qwen35_lowmem  Up XX minutes
```

**Container yoksa:**
```bash
ssh btankut@192.168.12.243 "docker start vllm_qwen35_lowmem"
```

### 2. vLLM Servisinin Çalışıp Çalışmadığını Kontrol Et

```bash
curl -s http://192.168.12.243:30000/v1/models | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('OK:', d['data'][0]['id'])"
```

Beklenen: `OK: qwen35moe` veya `OK: Qwen/Qwen3.5-35B-A3B-FP8`

### 3. vLLM'i Başlat (Çalışmıyorsa)

```bash
ssh btankut@192.168.12.243 "docker start vllm_qwen35_lowmem"
```

Legacy `vllm_head` wrapper kullanılıyorsa:

```bash
ssh btankut@192.168.12.243 "docker exec -d vllm_head bash -c '
  python3 -m vllm.entrypoints.openai.api_server \
    --model /root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/0b2752837483aa34b3db6e83e151b150c0e00e49 \
    --served-model-name Qwen/Qwen3.5-35B-A3B-FP8 \
    --host 0.0.0.0 \
    --port 30000 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.85 \
    --dtype auto \
    > /tmp/vllm_serve.log 2>&1
'"
```

### 4. Başlangıç Tamamlanana Kadar Bekle (~4 Dakika)

```bash
# Log takibi
ssh btankut@192.168.12.243 "docker logs -f vllm_qwen35_lowmem"

# Hazır olduğunda şu satırı göreceksin:
# INFO:     Application startup complete.
```

### 5. Sağlık Doğrulama

```bash
curl -s http://192.168.12.243:30000/v1/models
# Test isteği:
curl -s http://192.168.12.243:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3.5-35B-A3B-FP8","messages":[{"role":"user","content":"Merhaba"}],"max_tokens":20}'
```

---

## RAG için Uzun Context Profili

Standart başlatma: `--max-model-len 8192` (RAG için yeterli, ~5-10 chunk × 512-1024 token)

Uzun doküman analizi testi için:
```bash
ssh btankut@192.168.12.243 "docker exec -d vllm_head bash -c '
  python3 -m vllm.entrypoints.openai.api_server \
    --model /root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/0b2752837483aa34b3db6e83e151b150c0e00e49 \
    --served-model-name Qwen/Qwen3.5-35B-A3B-FP8 \
    --host 0.0.0.0 \
    --port 30000 \
    --max-model-len 131072 \
    --gpu-memory-utilization 0.90 \
    --kv-cache-dtype fp8 \
    --enable-prefix-caching \
    --dtype auto \
    > /tmp/vllm_serve_longctx.log 2>&1
'"
```

---

## Sorun Giderme

### "Connection refused" veya timeout

```bash
# Container durumu
ssh btankut@192.168.12.243 "docker inspect vllm_qwen35_lowmem --format '{{.State.Status}}'"

# Direct-serve container logu
ssh btankut@192.168.12.243 "docker logs --tail 30 vllm_qwen35_lowmem"

# Legacy wrapper logu
ssh btankut@192.168.12.243 "docker exec vllm_head cat /tmp/vllm_serve.log | tail -30"
```

### "CUDA out of memory"

1. vLLM'i durdur: `ssh btankut@192.168.12.243 "docker stop vllm_qwen35_lowmem"`
2. GPU'yu kontrol et: `ssh btankut@192.168.12.243 "nvidia-smi"`
3. `--gpu-memory-utilization` değerini düşür (0.85 → 0.80)
4. Yeniden başlat.

### Container başlamıyor

```bash
ssh btankut@192.168.12.243 "docker logs vllm_qwen35_lowmem --tail=20"
```

---

## Bakım Notları

- **vLLM idle shutdown:** Plan doc (bölüm 10) uyarısı: ~4-5 dakika istek gelmezse vLLM kapanabilir.
  Faz 1 PoC'da bunu izlemek için `scripts/dgx-vllm-ensure-running.sh` kullanılır.
  Üretim öncesi container CMD'ye otomatik başlatma eklenmelidir.
- **Snapshot hash:** Model snapshot hash (`0b2752837...`) güncellenirse `dgx-vllm-ensure-running.sh` içindeki `MODEL_SNAPSHOT` değişkenini güncelle.
- **Container restart policy:** Üretim için `--restart=unless-stopped` eklenmeli VE container CMD'si vLLM'i doğrudan çalıştırmalı (Ray ile birlikte `&` arka planda).
