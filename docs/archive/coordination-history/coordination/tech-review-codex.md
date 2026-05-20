# hukuk-ai-tech-review — Codex Sonucu

Durum: tamamlandı
Tarih: 2026-03-07 13:05 Europe/Istanbul
Kaynak session: `agent:codex:subagent:ad0d6e52-a99c-4c8d-9903-74a1fda26d2b`

## Özet
Plan uygulanabilir; ancak production-benzeri güvenilirlik için üç kritik sertleştirme gerekli:
1. Contract-first servis sınırları
2. Claim-level source verification
3. Gating’li test/eval disiplini

## Ana Bulgular
- Güçlü yanlar:
  - DGX inference ile M4 orchestration ayrımı doğru
  - Kalite hedefleri net
  - Test odaklı taslak güçlü
  - Hukuki chunking yaklaşımı doğru
- Kritik eksikler:
  - API/schema versioning yok
  - Source verification yeterince sert tanımlı değil
  - Auth/audit/PII sınırı belirsiz
  - Observability eksik
  - Reranker seçimi belirsiz
  - Data governance eksik
- Tutarsızlıklar:
  - Diyagramda 3 collection, şemada 2 collection detaylı
  - BM25/hybrid search contract’ı yok
  - Long-context testleri default 8K profile ile karışıyor
  - Idle shutdown notu ile “LLM inference dokunma” kuralı arasında operasyonel karar ihtiyacı var

## Önerilen Öncelikli Teknik Kararlar
1. `POST /v1/chat`, `/v1/chat/stream`, `/v1/search`, `/v1/health`, `/v1/readiness` contract’larını dondur
2. Embedding service için `task_type=query|document` ayrımını zorunlu yap
3. Pipeline veri modellerinde `content_hash`, `version`, idempotent upsert zorunlu olsun
4. Evaluation service ayrı bir run/report contract’ı kullansın
5. Verification mode `strict` default olsun

## Uygulama Sırası Önerisi
1. Contract-first temel
2. Infra connector’ları
3. Minimal RAG (mevzuat-only)
4. Source verification engine (strict MVP)
5. Evaluation runner + baseline
6. Data pipeline genişleme
7. UI + beta hardening

## Yüksek Öncelikli Riskler
- YİM erişim/scraping blokları
- Yanlış/uydurma kaynakla güven kaybı
- BM25/hybrid belirsizliği nedeniyle düşük recall
- Mevzuat güncelliğinin kaçırılması
- Beta öncesi auth/audit eksikliği

## Koordinatör Notu
Sentez backlog’da şu maddeler zorunlu yer almalı:
- claim-level grounding / verification engine
- API & schema versioning
- retrieval debug endpoint
- strict evaluation gates
- mevzuat-only baseline before YİM
