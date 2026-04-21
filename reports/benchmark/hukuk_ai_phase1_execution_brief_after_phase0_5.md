# Hukuk-AI Hardening Plan — Phase 1 Execution Brief (After Phase 0.5)

## Durum Özeti

Phase 0.5 başarılı kabul edilebilir. Benchmark için ayrı bir **green lane** oluşturulmuş, private answer key guard eklenmiş, public question schema doğrulanmış ve run artifact validation netleştirilmiş durumda. Legacy test borcu benchmark hattından ayrıştırılmış; bu doğru karar.

Bu noktada planın ana omurgası korunmalı. Büyük faz revizyonuna gerek yok. Ancak **Phase 1 kapsamı daha dar, ölçülebilir ve calibration odaklı** tanımlanmalı.

## Bu Fazdan Çıkan Net Sonuçlar

1. **CI/benchmark ayrımı doğru kurulmuş.**
   - Benchmark hardening işi artık unrelated legacy suite tarafından bloklanmıyor.
   - Bu, sonraki fazlarda metriğe güvenebilmek için gerekliydi.

2. **Skor değişmedi; bu beklenen ve doğru.**
   - Bu faz tuning yapmadı, yalnızca test lane izolasyonu yaptı.
   - Dolayısıyla kalite artmaması bir problem değil.

3. **Asıl darboğaz artık ölçüm şemasında.**
   - Phase 0 proxy scorer hâlâ insan/judge skoru yerine geçmiyor.
   - Belge ailesi, belge kimliği, temporal validity, yürürlük ve grounding sinyalleri daha granular ölçülmeli.

4. **Answer contract problemi hâlâ kritik.**
   - Bu fazda çözülmemesi normaldi.
   - Ancak bundan sonra ertelenirse her sonraki fazın değerlendirme gücü zayıflar.

## Plan Kararı

- **Phase 0.5 tamamlandı, kabul edilsin.**
- **Yeni faz eklemeye gerek yok.**
- **Sıradaki iş doğrudan Phase 1 + calibration olmalı.**
- **Answer contract fazı bunun hemen arkasından gelmeli.**

## Kod Asistanı İçin Phase 1 Kapsamı

Bu fazın amacı modeli iyileştirmek değil; **ölçüm katmanını doğru hale getirmek**.

### 1. Canonical source normalization

Aşağıdaki belge aileleri için canonical eşleme şeması oluştur:

- KANUN
- CB_KARARNAME
- YONETMELIK
- CB_YONETMELIK
- CB_KARAR
- CB_GENELGE
- KHK
- TUZUK
- KKY
- UY
- TEBLIGLER
- MULGA

Her cevap/run için mümkünse şu alanlar normalize edilsin:

- `source_family_canonical`
- `source_title_canonical`
- `source_identifier_canonical`
- `article_or_section_canonical`
- `effective_state_canonical`  
  (`active`, `amended`, `repealed`, `unknown` gibi)
- `temporal_anchor`  
  (soru "bugün", "halen", "2024 itibarıyla" gibi zaman sinyali içeriyorsa)

### 2. Proxy scorer schema upgrade

Phase 0 scorer’a şu sinyaller eklenmeli:

- **family_match_score**
- **document_match_score**
- **article_match_score**
- **temporal_validity_score**
- **grounding_score**
- **answer_contract_score**
- **hallucinated_source_penalty**
- **auto_fail_triggered**

Toplam skor bunlardan türesin ama ayrıca tüm alt skorlar CSV ve rapora ayrı ayrı yazılsın.

### 3. Failure taxonomy genişletmesi

Mevcut hata sınıfları korunarak aşağıdakiler eklenmeli:

- `wrong_family`
- `wrong_document`
- `wrong_article`
- `repealed_source_used_as_active`
- `missing_temporal_qualification`
- `hallucinated_identifier`
- `unsupported_confident_claim`
- `answer_contract_missing`
- `partial_grounding_only`

### 4. Judge calibration set

Private answer key’den bağımsız kalacak şekilde küçük bir calibration katmanı kur:

- 20 soru seç:
  - 5 güçlü cevap
  - 5 orta kalite cevap
  - 10 zayıf/yanlış cevap
- Bunlar için insan/judge referans etiketi çıkar:
  - `expected_band`: `high`, `medium`, `low`
  - kritik hata flag’leri
- Proxy scorer bu mini set üzerinde kalibre edilsin.

Amaç bire bir insan skorunu kopyalamak değil; **sıralama korelasyonunu** ve fail tespitini artırmak.

### 5. Yeni benchmark rapor alanları

Phase 1 sonrası raporda şunlar zorunlu olsun:

- Overall proxy score
- Family-level averages
- Task-type averages
- Top 10 worst QID
- Failure taxonomy counts
- Hallucinated source count
- Repealed-as-active count
- Temporal validity miss count
- Contract completeness rate
- Calibration summary

## Phase 1 İçin Acceptance Criteria

Aşağıdaki maddeler sağlanmadan faz tamamlanmış sayılmasın:

1. 12 belge ailesi canonical olarak normalize edilebiliyor olmalı.
2. Scored CSV’de yeni alt metrik kolonları bulunmalı.
3. Rapor dosyasında yeni hata sınıfı dökümleri yer almalı.
4. Proxy scorer calibration özeti üretilmeli.
5. Mevcut Phase 0 benchmark run artifact’i Phase 1 scorer ile yeniden puanlanabilmeli.
6. Green lane bozulmamalı.
7. Private answer key yine repo dışı kalmalı.

## Phase 1 Sonunda Beklenen Çıktılar

Kod asistanı bu faz bitince şunları üretmeli:

1. Güncel scored CSV
2. Güncel benchmark summary markdown
3. Calibration markdown raporu
4. Yeni/updated metric schema dokümantasyonu
5. Faz sonu kısa yönetici özeti

## Commit / Push Disiplini

Bu fazı tek commit ile kapatma. En az şu granülaritede ilerle:

### Commit 1 — metric schema groundwork
- canonical family/source schema
- yeni metric alanları

### Commit 2 — scorer and taxonomy
- scorer logic
- yeni penalty/failure class’lar

### Commit 3 — calibration and reporting
- calibration set
- rapor çıktıları
- docs

Her commit sonrası push yapılsın.

## Faz Sonu Rapor Formatı

Kod asistanı raporu şu başlıklarla yazsın:

1. Commit SHA listesi
2. Değişen dosyalar
3. Çalıştırılan komutlar
4. Test/eval sonuçları
5. Phase 0’a göre metrik farkları
6. Calibration sonucu
7. Yeni failure taxonomy dökümü
8. Riskler / bilinen açıklar
9. Sonraki faz önerisi

## Sonraki Faz Kararı

Phase 1 tamamlanınca sıradaki faz doğrudan **Answer Contract Hardening** olmalı.

Bu fazda hedef:
- `confidence_0_100` zorunlu üretim
- `final_reason` zorunlu üretim
- kaynak/dayanak yoksa kontrollü belirsizlik beyanı
- unsupported confident answer’ı düşüren output contract

Bu sırayı bozma. Retrieval tuning’i answer contract’tan önce başlatma; yoksa değerlendirme yine bulanık kalır.
