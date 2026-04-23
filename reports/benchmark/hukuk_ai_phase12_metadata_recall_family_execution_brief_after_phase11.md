# Hukuk-AI Hardening Plan — Phase 12 Execution Brief (After Phase 11)

## Karar

Phase 11 **kabul edilmemeli**. Fine-tuning kapısı **kapalı** kalmalı.

Ama Phase 11’in çok değerli bir çıktısı var: artık “kaynak yok” ile “kaynak var ama retrieval/family katmanında kaybediliyor” sorunları birbirinden ayrıştı.

Bu nedenle sıradaki fazın odağı artık genel corpus acquisition olmamalı. Öncelik şuna kaymalı:

1. **Pre-generation metadata/source lookup**
2. **Visible-but-not-retrieved recall repair**
3. **Family prior coverage and no-gate reduction**
4. **Sonra document identity / rubric grounding re-entry**

Bu sırayı bozma. Fine-tuning’e geçme.

---

## Phase 11’den Çıkan Net Sonuçlar

### Güçlü taraflar
- Run bütünlüğü temiz: 100/100 answered, 0 error, green lane pass, metric registry valid.
- `unsupported_confident_claim = 6`
- `hallucinated_identifier = 32`
- `selector_exact_article_hit_rate = 0.84`

### Açık kalan ana blokajlar
- `raw_score_proxy = 690.87`
- `pass_proxy = 55`
- `wrong_family = 35`
- `wrong_document = 15`
- `selected_article_equals_claimed_article = 63`
- `right_document_wrong_article_or_span = 51`
- `missing_required_content_signal = 97`
- `partial_grounding_only = 97`
- `needs_corpus_acquisition = 21`

### En kritik teknik okuma
Phase 11 summary’ye göre:

- `needs_corpus_acquisition = 21`
- ama bunun **18/21** satırı aslında katalog/index içinde görünür; yalnızca retrieval’da gelmiyor veya family yanlış sınıflanıyor.
- yalnız **3** satır “truly missing/unchecked” bandında görünüyor.

Bu çok önemli. Çünkü sonraki fazın ana işi yeni veri toplamak değil; **var olan doğru kaynağı generation öncesi havuza sokmak** olmalı.

---

## Neden Phase 12’nin Çekirdeği Metadata Lookup Olmalı?

Phase 11’de family tarafı neredeyse yerinde saymış:
- `wrong_family = 35`
- `selector_preferred_family_hit_rate = 0.90`
- `no_gate = 58`

Ayrıca summary açıkça söylüyor:
- birçok wrong-family satırı “locked gate” yüzünden değil,
- **weak/no family prior** yüzünden oluyor.

Bu da şu anki retrieval girişinin fazla serbest olduğunu gösteriyor.
Dense retrieval başlamadan önce, soru içinden source-title / identifier / issuer / family sinyali çıkaran ayrı bir lookup katmanı gerekiyor.

---

# Phase 12A — Pre-Generation Metadata / Source Lookup Layer

## Amaç
Soruya bakarak olası kaynak ailesini, olası belge başlığını ve varsa identifier sinyalini generation’dan önce candidate havuzuna enjekte etmek.

## Yapılacaklar
- Soru parser’ına şu lookup sinyallerini ekle:
  - mevzuat tipi kelimeleri (`kanun`, `yönetmelik`, `tebliğ`, `karar`, `genelge`, `kararname`, `tüzük`)
  - kurum/issuer adları
  - sayı/yıl/desen ifadeleri
  - “hakkında”, “ilişkin”, “usul ve esaslar”, “uygulanmasına dair” gibi title kalıpları
  - yürürlükten kaldırılan / geçici / ek madde / eski-yeni rejim sinyalleri
- Bu parser’dan şu structured alanlar üretilsin:
  - `parsed_family_candidates`
  - `parsed_identifier_candidates`
  - `parsed_issuer_candidates`
  - `parsed_title_ngrams`
  - `parsed_temporal_cues`
- Dense retrieval’dan önce **metadata lookup path** çalıştır:
  1. exact/near identifier lookup
  2. normalized title lookup
  3. issuer + family lookup
  4. title n-gram + family lookup
- Metadata lookup ile gelen candidate’lar trace’de ayrı işaretlensin:
  - `metadata_lookup_hit`
  - `metadata_lookup_source`
  - `metadata_lookup_rank`
  - `metadata_lookup_confidence`

## Acceptance Criteria
- visible-but-not-retrieved satırların önemli kısmı metadata lookup ile initial candidate havuzuna girmeli
- `no_gate` düşmeye başlamalı
- `expected family present in initial candidates` oranı artmalı

## Commit / Push
### Commit 1
- parser + metadata lookup schema
- trace columns
- lookup unit tests

### Commit 2
- lookup path integration
- candidate merge policy
- benchmark smoke rerun

Her commit sonrası push.

---

# Phase 12B — Visibility-Aware Recall Repair

## Amaç
“Kaynak indeks içinde var ama retrieval ilk havuza sokmuyor” problemini sistematik çözmek.

## Yapılacaklar
- Phase 11 visibility truth table’daki `18/21 visible` satırları ayrı backlog olarak ele al:
  - `present_but_not_retrieved`
  - `present_but_family_misclassified`
- Her satır için şunları kaydet:
  - first seen rank
  - initial top-k içinde görünme durumu
  - metadata lookup ile görünme durumu
  - dense-only ile görünme durumu
  - final selected candidate
- Initial retrieval policy’yi iki kanallı yap:
  1. metadata-informed recall lane
  2. dense recall lane
- Sonra bu iki lane birleşsin ve family/document rerank’e girsin.
- `gold_document_not_retrieved` satırlarını ayrıca takip et; bunlar dense recall tuning veya indexing sorunu olabilir.
- Aşağıdaki problemli aileler için özel recall regression paketi çıkar:
  - `CB_KARAR`
  - `CB_YONETMELIK`
  - `YONETMELIK`
  - `KANUN`
  - `UY`
  - `TUZUK`

## Acceptance Criteria
- `needs_corpus_acquisition <= 8`
- visible-but-not-retrieved alt kümesi keskin düşmeli
- `gold_document_not_retrieved` sayısı azalmalı
- retrieval initial candidate recall raporu üretilmeli

## Commit / Push
### Commit 3
- visibility-aware recall lane
- recall diagnostics
- family-specific recall fixtures

Push zorunlu.

---

# Phase 12C — Family Prior Coverage and No-Gate Reduction

## Amaç
`no_gate = 58` seviyesini ciddi biçimde düşürmek ve yanlış aile seçimlerini generation öncesinde azaltmak.

## Yapılacaklar
- `expected_family_prior` üretimini şu açılardan genişlet:
  - parsed family candidates
  - parsed issuer candidates
  - title lookup sonuçları
  - metadata lookup rank
- `no_gate` için açık neden kodları ekle:
  - `no_family_signal`
  - `conflicting_family_signals`
  - `low_lookup_confidence`
  - `family_lookup_miss`
- Aşağıdaki aile geçişleri için explicit negative rules yaz:
  - `CB_KARAR -> TEBLIGLER`
  - `CB_KARAR -> CB_GENELGE`
  - `CB_YONETMELIK -> CB_KARARNAME`
  - `YONETMELIK -> KKY`
  - `YONETMELIK -> UY`
  - `KANUN -> KKY`
  - `KANUN -> MULGA`
  - `UY -> KANUN`
- `YONETMELIK` ailesi için özel hardening şart; bu aile current report’ta en problemli ailelerden biri.

## Acceptance Criteria
- `wrong_family <= 32`
- `no_gate <= 35`
- `selector_preferred_family_hit_rate >= 0.92`
- `YONETMELIK` ve `KANUN` ailesinde wrong-family count belirgin düşmeli

## Commit / Push
### Commit 4
- family prior expansion
- no-gate reason codes
- negative family transition rules

Push zorunlu.

---

# Phase 12D — Document Identity Re-Stabilization

## Amaç
Phase 10–11’de düşen article/document hizasını geri toplamak.

## Yapılacaklar
- Metadata lookup sonucu gelen candidate’ları document identity rerank’e bağla.
- `title_match_type` için exact/strong bias artır:
  - exact phrase
  - strong overlap
  - medium overlap
  - weak overlap
  - none
- `none` ve `weak_overlap` ile seçilen candidate’lara cezayı artır.
- `selected_article_equals_claimed_article` metriği özellikle yeniden izlenmeli.
- Problemli satırlarda `replaced_by_selected_evidence` akışını kontrol et:
  - gerçekten düzeltme mi yapıyor
  - yoksa yanlış seçimi meşrulaştırıyor mu
- Trace’e şu alanları ekle:
  - `identity_rerank_input_source` (`metadata_lookup`, `dense`, `merged`)
  - `identity_lock_strength`
  - `selected_document_rank_after_identity_rerank`

## Acceptance Criteria
- `wrong_document <= 14`
- `selected_article_equals_claimed_article >= 68`
- `right_document_wrong_article_or_span <= 50`
- `title_match_type=none` ve `weak_overlap` oranı düşmeli

## Commit / Push
### Commit 5
- identity re-stabilization changes
- document/article regression tests
- trace/report updates

Push zorunlu.

---

# Phase 12E — Completeness Re-entry (Limited)

## Amaç
Selection katmanı toparlandıktan sonra rubric-aligned completeness’i yeniden denemek; ama yine birincil odak yapmamak.

## Yapılacaklar
- Sadece selection confidence yüksek satırlarda completeness slot zorlaması yap.
- `structurally_full_but_legally_misaligned` sınıfını aile ve document güveniyle birlikte raporla.
- Task-type completeness slot’larını “selection confidence” koşuluna bağla.
- Düşük selection confidence satırlarda uzun cevap yerine kontrollü kısa cevap korunmalı.

## Acceptance Criteria
- `missing_required_content_signal <= 95`
- `partial_grounding_only <= 95`
- `unsupported_confident_claim <= 8` korunmalı

## Commit / Push
### Commit 6
- limited completeness re-entry
- confidence-aware slot filling
- completeness regression tests

Push zorunlu.

---

# Phase 12F — Final Rerun + Gate Recheck

## Amaç
Phase 12 sonunda fine-tuning kapısının tekrar değerlendirilmesi.

## Zorunlu Koşular
- full benchmark rerun
- scorer rerun
- visibility truth audit rerun
- family routing audit rerun
- document identity audit rerun
- score comparison
- green lane

## Promotion Hedefleri
Aşağıdaki hedefler Phase 12 için kullanılmalı:

- `raw_score_proxy >= 695`
- `pass_proxy >= 57`
- `wrong_family <= 32`
- `wrong_document <= 14`
- `hallucinated_identifier <= 30`
- `unsupported_confident_claim <= 8`
- `selector_exact_article_hit_rate >= 0.80` korunmalı
- `selected_article_equals_claimed_article >= 68`
- `right_document_wrong_article_or_span <= 50`
- `missing_required_content_signal <= 95`
- `partial_grounding_only <= 95`
- `needs_corpus_acquisition <= 8`

En az **8/12** hedef tutmalı.

---

## Fine-Tuning Gate

Fine-tuning ancak aşağıdakiler aynı anda sağlanırsa yeniden konuşulsun:

- `raw_score_proxy >= 695`
- `pass_proxy >= 57`
- `wrong_family <= 32`
- `wrong_document <= 14`
- `hallucinated_identifier <= 30`
- `needs_corpus_acquisition <= 8`
- `selector_exact_article_hit_rate >= 0.80`
- `selected_article_equals_claimed_article >= 68`
- iki ardışık rerun’da stabil sonuç

Bu eşikler sağlanmazsa bir sonraki faz da system-level kalmalı.

---

## Öncelikli İzlenecek Aileler

Phase 12 boyunca özel dashboard ile izlenecek aileler:
- `YONETMELIK`
- `KANUN`
- `CB_KARAR`
- `CB_YONETMELIK`
- `UY`
- `MULGA`
- `CB_GENELGE`

Her biri için raporla:
- visibility_probe_status
- metadata_lookup_hit
- family_gate_status
- selected_family_confidence
- title_match_type
- identity_lock_strength
- article_alignment

---

## Faz Sonu Rapor Formatı

1. Commit SHA listesi
2. Değişen dosyalar
3. Çalıştırılan komutlar
4. Test / eval sonuçları
5. Phase 11’e göre delta
6. Visibility truth audit
7. Recall repair audit
8. Family routing audit
9. Document identity audit
10. Limited completeness re-entry audit
11. Riskler / bilinen açıklar
12. Fine-tuning gate kararı

---

## Son Not

Phase 11’den sonra ana problem artık “cevap az şey söylüyor” değil.
Ana problem şu:

- doğru kaynak ilk havuza giriyor mu,
- doğru aileye kilitleniyor mu,
- doğru belgeye kalıyor mu.

Phase 12’nin görevi bu üç soruyu generation’dan önce çözmeye yaklaşmak olmalı.
