# hukuk-ai-data-eval — Gemini Sonucu

Durum: tamamlandı
Tarih: 2026-03-07 13:05 Europe/Istanbul
Kaynak session: `agent:gemini:subagent:d3be04b0-eb17-47b6-b73e-1deb2e4c278b`

## Özet
Veri edinim sırası güvenilirlik odaklı önerildi:
1. Temel mevzuat
2. Resmi Gazete güncellik katmanı
3. YİM en son

Ana ilke: belirsizlikte refusal; %100'e yakın güvenilirlik için scope daraltma gerekirse mevzuat-only baseline.

## Ana Bulgular
- Öncelik sırası:
  - Önce temel 7 kanun (TBK, TCK, TMK, HMK, CMK, TTK, İK)
  - Sonra son 1 yıl Resmi Gazete değişiklikleri / AYM iptal kararları
  - En son YİM, başlangıçta emsal kararlarla sınırlı
- En güvenli scope daraltma:
  - Faz 1'de YİM ve gerekirse Resmi Gazete'yi dışarıda bırakıp statik mevzuat asistanı olarak başlamak
- Kritik veri kalite kontrolleri:
  - Hiyerarşik bütünlük
  - Overlap doğruluğu
  - Metadata doğruluğu (`kanun_no`, `madde_no`, `hukuk_dali`)
  - Mülga madde etiketleme/filtresi
  - HTML çöp veri temizliği
  - Kaynak toplamı ile indexed chunk sayısı eşleşmesi
- Evaluation set önerisi (50 soru):
  - 15 doğrudan mevzuat
  - 10 kompleks/çapraz mevzuat
  - 10 güncellik/mülga tuzaklı soru
  - 15 out-of-domain / refusal testi
- Sert beta go/no-go önerileri:
  - Hallucination oranı pratikte 0 hedefi
  - Refusal başarısı >= %95
  - Kaynak referans oranı >= %95
  - Yanlış kaynak, tahmini hukuk yorumu, mülga madde hatası = no-go

## Riskler
- Scraping rate limit / ban / captcha / e-Devlet oturum zorlukları
- Güncelliğin kaçırılması
- Hukuki tavsiye üretimi riski
- KVKK / PII sızıntısı riski

## Koordinatör Notu
Sentez backlog’da şu maddeler zorunlu yer almalı:
- mevzuat-only fallback planı
- mülga/güncellik kontrol hattı
- refusal-heavy evaluation set
- PII masking gereksinimi
- YİM’i geç faza iten risk temelli plan
