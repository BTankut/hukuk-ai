# Reranker Live Blockers

**Tarih:** 2026-03-20  
**Amaç:** Safe-activation runner hazırlandıktan sonra canlı A/B koşusunu engelleyen servis blocker'larını netleştirmek.

## Yapılan Kontroller

```bash
curl http://localhost:8000/v1/health
curl http://localhost:8081/health
curl http://localhost:19530
curl http://192.168.12.243:30000/v1/models
```

## Sonuç

- `localhost:8000` → **down**
- `localhost:8081` → **down**
- `localhost:19530` → **down**
- `192.168.12.243:30000` → **unreachable**

## Anlamı

Reranker safe-activation runner teknik olarak hazır olsa da canlı A/B koşusu şu an başlatılamaz. Çünkü:

1. API gateway çalışmıyor.
2. Embedding service çalışmıyor.
3. Milvus erişilebilir değil.
4. DGX vLLM endpoint'i erişilemiyor.

Bu durumda canlı eval sonucu almak yerine blocker'ı açıkça kaydetmek daha doğruydu.

## Sonraki Adım

1. API gateway ortamını kur / ayağa kaldır
2. Embedding service'i doğrula
3. Milvus erişimini doğrula
4. DGX vLLM erişimini doğrula
5. Sonra:

```bash
python3 evaluation/run_reranker_safe_activation.py --live
```
