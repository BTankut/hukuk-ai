# Hukuk-AI Hardening Plan — Phase 17 Execution Brief (After Phase 16)

## Karar

Phase 16 **kabul edilmemeli**. Productization gate ve fine-tuning gate **kapalı** kalmalı.

Phase 16 sistemik olarak değerli ilerleme sağladı:
- corpus materialization backlog `13 -> 6`
- canonical span materialization `86 -> 93`
- title-only degradation `13 -> 6`
- unsupported-confident answer `6 -> 0`
- canonical source key v2 collision `0/100`

Ancak kalite hedefleri kapanmadı:
- `raw_score_proxy = 709.00`, hedef `>=735`
- `pass_proxy = 69`, hedef `>=72`
- `wrong_document = 18`, hedef `<=15`
- `missing_required_content_signal = 99`
- `partial_grounding_only = 99`
- `MULGA pass = 0/5`
- `CB_GENELGE pass = 0/4`

Bu yüzden Phase 17’nin ana hedefi model tuning değil; **v2 source-key’i gerçek selection/materialization path’e geçirmek, kalan corpus satırlarını kapatmak ve answer completeness’i evidence-slot düzeyinde zorlamak** olmalı.

---

## Phase 16’dan Çıkan Net Sonuçlar

### Güçlü taraflar
- `unsupported_confident_claim = 0`
- `wrong_family = 12`
- `canonical_span_materialized_count = 93`
- `corpus_materialization_required_count = 6`
- `canonical_source_key_v2 collision = 0/100`
- `green_lane = pass`
- `contract_valid = 100/100`

### Açık kalan blokajlar
- `missing_required_content_signal = 99`
- `partial_grounding_only = 99`
- runtime `rubric_sufficient = 20/100`
- `transition_or_replacement_rule` en büyük missing-slot sınıfı
- `CB_GENELGE = 0/4`
- `MULGA = 0/5`
- 6 corpus materialization row hâlâ açık

### Kalan 6 corpus/materialization satırı
- `CBG-04`: family source-key collision / v2 binding path eksik
- `CBKAR-08`: family source-key collision / v2 binding path eksik
- `KANUN-06`: corpus ingestion / text extraction repair
- `KHK-05`: article-zero materialization
- `TUZUK-05`: article-zero materialization
- `YON-04`: article-zero materialization

---

# Phase 17A — Move Source-Key v2 Into Binding Path

## Amaç
`canonical_source_key_v2` sadece trace alanı olarak kalmamalı; materialization, retrieval, selection ve source-lock binding içinde gerçek kimlik anahtarı olarak kullanılmalı.

## Neden Öncelik?
Phase 16’da v2 collision `0/100`, fakat bazı satırlar hâlâ legacy alias/collision nedeniyle açık kaldı. Bu, v2’nin ölçümde doğru ama runtime binding’de eksik kullanıldığını gösteriyor.

## Yapılacaklar
- Materialization binding path içinde primary key sırası:
  1. `canonical_source_key_v2`
  2. `doc_uuid`
  3. family-qualified source id
  4. legacy source key yalnız alias
- Source-lock, selected-source, candidate merge ve evidence bundle aynı v2 key ile çalışmalı.
- Trace alanları:
  - `binding_source_key`
  - `binding_source_key_version`
  - `legacy_source_key_used_as_alias`
  - `canonical_key_binding_applied`
  - `canonical_key_binding_reason`
- `CBG-04` ve `CBKAR-08` için özel before/after audit üret.

## Acceptance Criteria
- `CBG-04` ve `CBKAR-08` artık legacy source-key collision blocker olarak kalmamalı.
- `source_key_collision_detected_count` legacy alias tarafında kalsa bile v2 binding collision `0` kalmalı.
- `corpus_materialization_required_count <= 4`
- `wrong_document` artmamalı.

## Commit / Push
### Commit 1
- v2 source-key binding integration
- trace field expansion
- CBG-04 / CBKAR-08 regression tests

Push zorunlu.

---

# Phase 17B — Repair Remaining Corpus / Article-Zero Materialization Rows

## Amaç
Kalan body-span / article-zero / extraction borçlarını kapatmak.

## Öncelik sırası
1. `KANUN-06`: corpus ingestion / text extraction
2. `KHK-05`: article-zero materialization
3. `TUZUK-05`: article-zero materialization
4. `YON-04`: article-zero materialization

## Yapılacaklar
- Her satır için:
  - source text var mı?
  - body var ama article parser mı kaçırıyor?
  - m.0 içinde body mi gömülü?
  - official source acquisition gerekiyor mu?
  - reindex gerekir mi?
- Article-zero materialization için:
  - title + body ayrımı
  - m.0 body extraction
  - body span candidate üretimi
  - title-only fallback’in son seçenek olması
- Yeni alanlar:
  - `article_zero_body_extracted`
  - `article_zero_materialization_reason`
  - `body_extraction_source`
  - `materialized_from_m0`

## Acceptance Criteria
- `corpus_materialization_required_count <= 3`
- `canonical_span_materialized_count >= 95`
- `title_only_answer_degraded_count <= 4`
- Kalan açık satırlar explicit corpus backlog olarak kalmalı.

## Commit / Push
### Commit 2
- article-zero materialization
- KANUN-06 extraction repair
- family smoke reports

Push zorunlu.

---

# Phase 17C — Evidence-to-Answer Required Slot Synthesizer

## Amaç
`missing_required_content_signal = 99` ve `partial_grounding_only = 99` sorununu doğrudan hedeflemek.

## Ana fikir
Model sadece genel cevap üretmemeli; seçilen evidence span’lerden zorunlu hukuki fact slotlarını doldurmalı.

## Yapılacaklar
- Her task type için required slots:
  - governing source
  - exact source identity
  - article/span
  - temporal validity
  - scenario application
  - exception / limitation
  - transition / replacement rule
  - procedure / consequence
  - document-selection rationale
- Evidence bundle’dan slot doldurma:
  - `slot_name`
  - `slot_value`
  - `evidence_span_id`
  - `evidence_quote_hash`
  - `slot_confidence`
  - `slot_missing_reason`
- Final answer bu slotlardan üretilmeli.
- `transition_or_replacement_rule` özel slotu eklenmeli; çünkü Phase 16’da en büyük missing-slot sınıfı bu.

## Acceptance Criteria
- `minimum_answer_facts_present_count` artmalı
- runtime `rubric_sufficient >= 35/100`
- `missing_required_content_signal <= 92`
- `partial_grounding_only <= 92`
- `unsupported_confident_claim <= 3` korunmalı

## Commit / Push
### Commit 3
- required-slot schema
- evidence-to-slot extraction
- task-type templates

### Commit 4
- final answer synthesis from slots
- scorer/report fields
- regression tests

Her commit sonrası push.

---

# Phase 17D — MULGA Rubric Completion Slice

## Amaç
`MULGA` ailesinde state/family safety düzelmişken pass sayısını artırmak.

## Neden ayrı?
Phase 16’da:
- `wrong_family_claims` çok azaldı
- `active_state_claims = 0`
- ama `MULGA pass = 0/5`

Bu, artık routing/state değil; missing historical/current/transition facts sorunu.

## Yapılacaklar
MULGA için zorunlu slotlar:
- source is repealed / historical
- applicable period
- current applicability
- replacement/current-law relation
- transition rule
- direct legal conclusion
- no active-law overclaim

Answer mode:
- `historical_repealed_answer`
- `repealed_transition_answer`
- `not_currently_applicable_answer`

Mini smoke:
- 5 MULGA row
- önce full benchmark yok

## Acceptance Criteria
- `MULGA pass >= 2/5`
- `repealed_as_active_count = 0` veya artmamalı
- `unsupported_confident_claim` artmamalı
- `transition_or_replacement_rule` slot coverage artmalı

## Commit / Push
### Commit 5
- MULGA slot template
- MULGA smoke runner/report
- temporal rubric regression tests

Push zorunlu.

---

# Phase 17E — CB_GENELGE Recovery Slice

## Amaç
`CB_GENELGE = 0/4` ve corpus/body blocker durumunu kapatmak.

## Yapılacaklar
- 4 CB_GENELGE row için:
  - body availability
  - source key binding
  - canonical title
  - selected span
  - required slots
  - document-selection rationale
- Genelge yapısı genelde article-based olmayabilir. Bu nedenle:
  - m.0/title-only modelinden farklı bir `circular_body_span` modeli gerekebilir.
  - “ilgili genelge neyi emrediyor / hangi kapsamı düzenliyor” slotu eklenmeli.
- CB_GENELGE answer template:
  - genelge konusu
  - kapsam
  - yükümlülük/emir
  - temporal validity
  - dayanak belge kimliği

## Acceptance Criteria
- `CB_GENELGE pass >= 2/4`
- `CBG-04` blocker kapanmalı veya açık corpus blocker olarak net ayrılmalı
- `corpus_materialization_required` CB_GENELGE tarafında düşmeli

## Commit / Push
### Commit 6
- CB_GENELGE body/span model
- circular answer template
- CB_GENELGE smoke report

Push zorunlu.

---

# Phase 17F — Full Rerun + Gate Check

## Zorunlu koşular
- full benchmark rerun
- scorer rerun
- corpus materialization audit
- source-key v2 binding audit
- evidence-to-slot audit
- MULGA audit
- CB_GENELGE audit
- green lane

## Hedef Metrikler
- `raw_score_proxy >= 735`
- `pass_proxy >= 73`
- `wrong_family <= 12`
- `wrong_document <= 15`
- `hallucinated_identifier <= 23`
- `unsupported_confident_claim <= 3`
- `corpus_materialization_required_count <= 3`
- `canonical_span_materialized_count >= 95`
- `missing_required_content_signal <= 92`
- `partial_grounding_only <= 92`
- `runtime rubric_sufficient >= 35/100`
- `MULGA pass >= 2/5`
- `CB_GENELGE pass >= 2/4`

En az **9/13** hedef tutmalı.

---

## Fine-Tuning Gate

Fine-tuning Phase 17’de de kapalı.

Yalnız şu koşullar sağlanırsa sonraki değerlendirmede konuşulabilir:
- `corpus_materialization_required_count <= 3`
- `unsupported_confident_claim <= 3`
- `missing_required_content_signal <= 92`
- `partial_grounding_only <= 92`
- `MULGA pass >= 2/5`
- `CB_GENELGE pass >= 2/4`
- iki ardışık full rerun stabil

Bunlar sağlanmadan fine-tuning açılmamalı.

---

## Faz Sonu Rapor Formatı

Kod asistanı `phase_17_sourcekey_slots_mulga_cbgenelge_report.md` üretmeli:

1. Commit SHA listesi
2. Değişen dosyalar
3. Çalıştırılan testler
4. Source-key v2 binding audit
5. Remaining corpus/materialization remediation
6. Evidence-to-answer required slot audit
7. MULGA smoke + full result
8. CB_GENELGE smoke + full result
9. Full benchmark delta
10. Productization/fine-tuning gate kararı
11. Kalan backlog

---

## Son Not

Phase 16 bize şunu gösterdi:
- corpus materialization ve source-key tarafında ilerleme mümkün,
- confidence safety artık iyi,
- ama cevaplar özel hukuk benchmark rubric’inin beklediği fact slotlarını doldurmuyor.

Phase 17’nin ana işi:
**v2 key’i runtime binding’e almak, kalan body-span borcunu azaltmak ve cevapları evidence-slot bazlı üretmek.**
