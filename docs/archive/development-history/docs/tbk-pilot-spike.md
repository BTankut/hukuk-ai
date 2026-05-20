# TBK Pilot Spike — Canlı Source + Milvus Smoke (Follow-up)

Bu doküman Faz 1 frozen scope'a (mevzuat-only baseline) sadık TBK zincirinin follow-up doğrulamasını özetler.

## Scope
- ✅ TBK loader: canlı kaynak deneme + offline fixture fallback
- ✅ Canlı kaynak parser iyileştirmesi (`mevzuatDetayIframe` akışı)
- ✅ Madde/fıkra bazlı chunking + metadata extraction
- ✅ Ingest pipeline interface (`VectorStore`) + smoke store (`InMemoryVectorStore`)
- ✅ Milvus adapter + gerçek Milvus smoke komutu
- ❌ YİM / Resmi Gazete (Faz 1 dışı)

---

## 1) Canlı TBK Source — Ne Kırılmıştı, Ne Düzeldi?

### Kırılma nedeni (net)
`https://mevzuat.gov.tr/mevzuat?...` URL'i doğrudan kanun metnini değil, bir **shell HTML** döndürüyor.
Asıl metin `id="mevzuatDetayIframe"` içindeki iframe kaynağında geliyor.

Eski parser shell HTML'i parse ettiği için `MADDE` blokları 0 dönüyor ve fixture fallback'e düşüyordu.

### Yapılan düzeltmeler
- Loader, shell sayfadan `mevzuatDetayIframe` `src` URL'ini çıkarıp asıl içeriği fetch ediyor.
- Retry + alternatif host (`mevzuat.gov.tr` / `www.mevzuat.gov.tr`) denemesi eklendi.
- Metin normalize aşaması güçlendirildi (`&nbsp;`, whitespace, appendix kırpma).
- `Kanun Numarası` parse önceliği artırıldı; TBK dışı yanlış parse olursa 6098'e sabitleme uyarısı bırakılıyor.
- `GEÇİCİ MADDE` blokları normal maddelerle çakışmayacak şekilde etiketleniyor (`G1`, `G2`).

### Canlı doğrulama komutu
`api-gateway/` altında:

```bash
PYTHONPATH=src .venv/bin/python -m data_pipeline.cli \
  --online \
  --fixture src/data_pipeline/fixtures/tbk_fixture.txt
```

Örnek canlı çıktı:

```json
{
  "source_kind": "online",
  "law_no": "6098",
  "article_count": 651,
  "chunk_count": 656,
  "indexed_count": 656,
  "warnings": [
    "Mevzuat shell sayfası iframe döndürdüğü için mevzuatDetayIframe kaynağı kullanıldı."
  ]
}
```

> Not: `article_count=651` içinde `MADDE 1..649` + `GEÇİCİ MADDE 1-2` vardır.

---

## 2) Milvus Canlı Bağlantı Smoke Yolu

### Kod tarafı
Yeni smoke komutu eklendi:

```bash
tbk-milvus-smoke
# veya
python -m data_pipeline.milvus_smoke
```

Komut akışı:
1. Milvus'a bağlanır
2. TBK pipeline şemasına uygun collection oluşturur (gerekirse recreate)
3. TBK ingest pipeline'ı çalıştırır (online veya fixture)
4. `flush` + `search` ile yazım/arama smoke doğrular
5. İstenirse collection'ı temizler (`--drop-after`)

### Lokal Milvus çalıştırma (Docker Compose)
`api-gateway/` altında:

```bash
docker compose -f docker-compose.milvus.yml up -d
```

### pymilvus kurulumu
`api-gateway/` altında:

```bash
uv pip install --python .venv/bin/python -e '.[milvus]'
```

### Canlı smoke komutu
```bash
PYTHONPATH=src .venv/bin/python -m data_pipeline.milvus_smoke \
  --online \
  --recreate-collection \
  --drop-after
```

Örnek canlı çıktı:

```json
{
  "milvus_uri": "http://localhost:19530",
  "collection": "mevzuat_tbk_smoke",
  "collection_created": true,
  "source_kind": "online",
  "article_count": 651,
  "chunk_count": 656,
  "indexed_count": 656,
  "count_after_upsert": 656,
  "search_hit_count": 3,
  "top_hit_id": "TBK_m18_f1",
  "warnings": [
    "Mevzuat shell sayfası iframe döndürdüğü için mevzuatDetayIframe kaynağı kullanıldı."
  ]
}
```

Stack kapatma:

```bash
docker compose -f docker-compose.milvus.yml down
```

---

## Testler
`api-gateway/` altında:

```bash
PYTHONPATH=src .venv/bin/pytest -q tests/test_tbk_data_pipeline.py tests/test_milvus_smoke.py
```

Bu paket aşağıdakileri doğrular:
- TBK loader fixture/parse zinciri
- chunk metadata/id formatı
- ingest zincirinde `chunk_count == indexed_count`
- Milvus smoke helper'larının schema/index/top-hit davranışı (fake client ile)

---

## Açık Notlar / Riskler
- Canlı kaynak erişimi internet/sandbox politikasına bağlı; erişim yoksa fallback fixture çalışır.
- Milvus `row_count` metriği flush öncesi 0 görünebilir; smoke akışında flush zorlandı.
- Bu spike production throughput/latency benchmark'ı değildir; bağlantı + parser + ingest smoke seviyesidir.
