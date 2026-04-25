# Hukuk-AI Hardening Plan — Phase 18 Execution Brief After Phase 17F

## Karar

Phase 17F **conditional acceptance** aldı.

Bunun anlamı:

- Phase 17 sistemik olarak başarılı kabul edilebilir.
- Phase 18 açılmalı.
- Productization gate hâlâ kapalı.
- Fine-tuning gate hâlâ kapalı.

Phase 17F sonucu artık corpus / source-key / family-routing tarafının ana blokaj olmaktan çıktığını gösteriyor. Yeni ana darboğaz:

1. **rubric-aligned evidence-to-answer slot completion**
2. **claim-level confidence / unsupported-claim calibration**
3. **private-rubric completeness**
4. kalan küçük corpus/materialization backlog’un açık yan backlog olarak yürütülmesi

---

## Phase 17F’den Çıkan Net Sonuçlar

### Güçlü sonuçlar

- `raw_score_proxy = 767.91`
- `pass_proxy = 77/100`
- `wrong_family = 12`
- `wrong_document = 10`
- `hallucinated_identifier = 18`
- `corpus_materialization_required_count = 2`
- `canonical_span_materialized_count = 98`
- `runtime rubric_sufficient = 88/100`
- `MULGA pass = 3/5`
- `CB_GENELGE pass = 2/4`
- `contract_valid = 100/100`
- `green_lane = pass`
- source-key v2 runtime binding active on `100/100`
- v2 collision and binding collision both `0`

### Kapanmayan kritik noktalar

- `unsupported_confident_claim = 8`, target `<=3`
- `missing_required_content_signal = 98`, target `<=92`
- `partial_grounding_only = 98`, target `<=92`

### Yan backlog

Aşağıdaki işler Phase 18 ana akışını bloklamadan ayrı backlog olarak takip edilmeli:

- CB_GENELGE `2024/7` Tasarruf Tedbirleri official source acquisition/materialization
- CB_GENELGE `2019/12` Bilgi ve İletişim Güvenliği official source acquisition/materialization
- `CBKAR-08` materialization backlog
- `KANUN-06` materialization backlog

---

# Phase 18 — Rubric-Aligned Evidence-to-Answer Slot Completion

## Amaç

Cevaplar artık çoğunlukla doğru kaynak ve doğru belge bandında. Bundan sonra hedef, bu kaynaklardan **private rubric’in beklediği hukuki fact slotlarını eksiksiz ve doğrulanabilir biçimde cevaba taşımak**.

Yani Phase 18’in amacı daha çok retrieval yapmak değil; mevcut evidence’ı daha iyi yapılandırmak ve cevaba aktarmak.

---

# Phase 18A — Required Slot Matrix Cleanup

## Amaç

Her task type ve source family için zorunlu answer slotlarını netleştirmek.

## Yapılacaklar

Task type bazlı required slot matrix oluştur:

```yaml
task_types:
  precise_retrieval:
    required_slots:
      - governing_source
      - exact_source_identity
      - article_or_span
      - direct_rule
      - temporal_validity

  temporal_validity:
    required_slots:
      - governing_source
      - effective_state
      - effective_period
      - current_applicability
      - transition_or_replacement_rule
      - direct_conclusion

  scenario_applicability:
    required_slots:
      - governing_source
      - article_or_span
      - rule
      - facts_applied
      - exception_or_limitation
      - direct_conclusion

  document_selection:
    required_slots:
      - selected_primary_source
      - source_family
      - identifier
      - why_this_source
      - why_not_neighbor_source
      - temporal_validity

  hierarchy_conflict:
    required_slots:
      - upper_norm
      - lower_norm
      - conflict_rule
      - applicable_priority
      - direct_conclusion

  compliance_checklist:
    required_slots:
      - governing_source
      - obligations
      - procedure
      - consequence
      - exception_or_limitation

  exception_analysis:
    required_slots:
      - governing_source
      - general_rule
      - exception_rule
      - exception_conditions
      - conclusion

  current_update:
    required_slots:
      - current_source
      - previous_source_if_relevant
      - change_or_update
      - effective_date
      - current_conclusion
```

Family-specific additions:

```yaml
MULGA:
  required_slots:
    - source_is_repealed_or_historical
    - applicable_period
    - current_applicability
    - replacement_or_current_law_relation
    - transition_rule
    - no_active_law_overclaim

CB_GENELGE:
  required_slots:
    - issuer
    - circular_number_or_date
    - subject
    - scope_or_addressee
    - operative_instruction
    - temporal_validity
    - administrative_effect

CB_KARAR:
  required_slots:
    - decision_number
    - operative_clause
    - annex_or_attachment_if_relevant
    - effective_date
    - related_regulation_or_teblig_if_supporting

TEBLIGLER:
  required_slots:
    - teblig_identifier
    - issuer
    - scope
    - operative_rule
    - procedure_or_formula
    - temporal_validity
```

## Acceptance Criteria

- Slot matrix config/dataset üretildi.
- Her QID için expected required slot set trace’e yazılıyor.
- Missing slot sınıfları daha açıklanabilir hale geliyor.
- Eski answer contract kırılmıyor.

## Commit / Push

### Commit 1
- required slot matrix config
- task/family slot resolver
- trace/report fields

Push zorunlu.

---

# Phase 18B — Evidence-to-Slot Extraction

## Amaç

Seçilen evidence span’lerden required slot değerlerini çıkarmak.

## Yapılacaklar

Her slot için şu schema kullanılmalı:

```yaml
answer_slot:
  slot_name: string
  required: bool
  value: string | null
  evidence_span_keys: string[]
  evidence_article_or_span: string | null
  extraction_method: deterministic | llm_schema | hybrid
  fill_status: filled | missing | contradicted | unsupported | not_applicable
  verifier_status: verified | failed | needs_review
  confidence_0_100: int
  slot_missing_reason: string | null
```

Extraction stratejisi:

- deterministic:
  - source identity
  - source family
  - identifier
  - article/span
  - temporal metadata
  - effective state
- hybrid / LLM schema:
  - rule
  - scenario application
  - scope
  - exception
  - consequence
  - transition/replacement relation
  - document-selection rationale

## Critical Slot

Phase 16–17 raporlarında en önemli eksik sınıf `transition_or_replacement_rule` idi. Bu slot özellikle şu ailelerde aktif olmalı:

- `MULGA`
- `KANUN`
- `KHK`
- `TUZUK`
- `CB_KARAR`
- `YONETMELIK`

## Acceptance Criteria

- `minimum_answer_facts_present_count` artmalı.
- `runtime rubric_sufficient` korunmalı veya artmalı.
- Slot extraction hallucination üretmemeli.
- Her filled slot en az bir evidence span’e bağlı olmalı.

## Commit / Push

### Commit 2
- evidence-to-slot extraction
- deterministic metadata slot extractor
- LLM schema extractor wrapper
- slot verifier tests

Push zorunlu.

---

# Phase 18C — Claim-Level Confidence Calibration

## Amaç

Runtime `unsupported_confident_answer=0` olsa bile scorer `unsupported_confident_claim=8` diyor. Bu fark kapatılmalı.

## Yapılacaklar

8 scorer-flagged row için audit çıkar:

```yaml
unsupported_confident_audit_row:
  qid: string
  answer_mode: string
  confidence_0_100: int
  grounding_status: string
  unsupported_claim_reason: string
  missing_required_slots: string[]
  filled_slots: string[]
  evidence_span_keys: string[]
  should_degrade_confidence: bool
  proposed_confidence_ceiling: int
```

Claim-level confidence rule:

```text
final confidence = min(
  source_identity_confidence,
  document_identity_confidence,
  slot_coverage_confidence,
  temporal_confidence,
  evidence_support_confidence,
  missing_required_slot_penalty
)
```

Confidence ceilings:

| Condition | Max confidence |
|---|---:|
| all required slots verified | 90 |
| one required slot missing but non-critical | 75 |
| critical required slot missing | 60 |
| transition/current relation missing when required | 55 |
| title-only or insufficient canonical evidence | 45 |
| source identity uncertain | 40 |
| temporal state uncertain | 40 |

## Acceptance Criteria

- `unsupported_confident_claim <= 3`
- contract_valid remains `100/100`
- pass count should not collapse
- no increase in hallucinated source

## Commit / Push

### Commit 3
- scorer-flagged unsupported audit
- confidence ceiling policy
- claim-level verifier calibration

Push zorunlu.

---

# Phase 18D — Answer Synthesis From Verified Slots

## Amaç

Final cevap artık serbest context summary değil, verified answer slots üzerinden üretilmeli.

## Yapılacaklar

Synthesis input:

```yaml
verified_answer_plan:
  direct_answer_slot:
  legal_basis_slots:
  temporal_validity_slot:
  scenario_application_slot:
  exception_or_limitation_slot:
  transition_or_replacement_slot:
  missing_slots:
  confidence_policy:
```

Cevap üretim kuralları:

- Required slot doluysa açıkça cevapta yer almalı.
- Required slot eksikse:
  - cevap qualified olmalı
  - eksik bilgi final_reason’da görünmeli
  - confidence ceiling uygulanmalı
- Supporting source ile primary source karışmamalı.
- MULGA’da current-law overclaim yapılmamalı.
- CB_GENELGE’de article/fıkra yoksa instruction/scope üzerinden cevap verilmeli.

## Acceptance Criteria

- `missing_required_content_signal <= 90`
- `partial_grounding_only <= 90`
- `runtime rubric_sufficient >= 90/100`
- `pass_proxy >= 78`
- `raw_score_proxy >= 775`

## Commit / Push

### Commit 4
- answer synthesis from verified slots
- final_reason missing-slot explanation
- task/family answer templates

Push zorunlu.

---

# Phase 18E — Side Backlog: Corpus / Official Source Acquisition

Bu, Phase 18 ana slot-completion işini bloklamadan ayrı backlog olarak takip edilmeli.

## CB_GENELGE Backlog

- `CBG-01`: `2024/7 Tasarruf Tedbirleri`
- `CBG-02`: `2019/12 Bilgi ve İletişim Güvenliği`

Yapılacaklar:

- official source acquisition
- body materialization
- circular body span extraction
- slash-numbered identifier preservation
- topic scoring regression test

## Remaining Materialization Backlog

- `CBKAR-08`
- `KANUN-06`

Yapılacaklar:

- body/source truth audit
- official source acquisition if required
- materialization path
- reindex/shadow-index if required

## Acceptance Criteria

- corpus_materialization_required_count stays `<=2`, preferably `0`
- CB_GENELGE pass improves beyond `2/4` if sources are acquired
- no regression in source-key v2 collision

## Commit / Push

### Commit 5
- side backlog acquisition/materialization
- family smoke reports
- source-key v2 regression tests

Push zorunlu.

---

# Phase 18F — Full Benchmark Rerun

## Zorunlu koşular

- full 100 benchmark
- scorer
- green lane
- slot coverage audit
- unsupported confident audit
- family-level report
- MULGA report
- CB_GENELGE report
- corpus materialization audit
- source-key v2 binding audit

## Target Metrics

| Metric | Target |
|---|---:|
| raw_score_proxy | `>= 775` |
| pass_proxy | `>= 78` |
| wrong_family | `<= 12` |
| wrong_document | `<= 10` |
| hallucinated_identifier | `<= 18` |
| unsupported_confident_claim | `<= 3` |
| missing_required_content_signal | `<= 90` |
| partial_grounding_only | `<= 90` |
| runtime rubric_sufficient | `>= 90/100` |
| MULGA pass | `>= 3/5` |
| CB_GENELGE pass | `>= 2/4`, preferably `>=3/4` |
| corpus_materialization_required_count | `<= 2` |
| canonical_span_materialized_count | `>= 98` |

En az **10/13** target geçmeli.

---

## Phase 18 Decision

### Eğer hedefler geçerse

- Phase 18 conditional accept.
- Bir stabil rerun daha iste.
- Fine-tuning hâlâ hemen açılmasın; ama artık sınırlı non-benchmark behavior tuning veya reranker training konuşulabilir.

### Eğer unsupported_confident_claim düşmezse

- confidence calibration ayrı mini phase aç.
- Synthesis değil verifier/contract tarafı ele alınmalı.

### Eğer missing_required_content_signal hâlâ 95+ kalırsa

- slot matrix private rubric ile hizalı değil.
- Human/judge-calibrated 20–30 QID slot audit yapılmalı.

### Eğer MULGA hâlâ düşükse

- MULGA-only phase aç.
- Replacement/current-law relation graph gerekebilir.

### Eğer CB_GENELGE hâlâ düşükse

- remaining official source acquisition/materialization blokajı çözülmeli.
- Circular-specific instruction_block model genişletilmeli.

---

## Fine-Tuning Gate

Fine-tuning Phase 18 sonunda ancak tartışılabilir; otomatik açılmayacak.

Minimum ön koşullar:

- `unsupported_confident_claim <= 3`
- `missing_required_content_signal <= 90`
- `partial_grounding_only <= 90`
- `corpus_materialization_required_count <= 2`
- `MULGA pass >= 3/5`
- `CB_GENELGE pass >= 3/4` ideal, `>=2/4` minimum
- two stable full reruns

Bu koşullar sağlanmadan LLM fine-tuning açılmamalı.

---

# Rapor Formatı

Kod asistanı `phase_18_rubric_slot_completion_report.md` üretmeli:

1. Commit SHA listesi
2. Değişen dosyalar
3. Test komutları
4. Benchmark komutları
5. Phase 17F’ye göre delta
6. Required slot matrix summary
7. Evidence-to-slot extraction audit
8. Claim-level confidence calibration audit
9. Verified-slot answer synthesis audit
10. CB_GENELGE side backlog result
11. MULGA result
12. Family-level score table
13. Productization/fine-tuning gate kararı
14. Kalan riskler

---

## Stop Doing

Bu fazda şunlara zaman harcanmasın:

- genel prompt tightening
- dense top-k büyütme
- QID-specific rules
- benchmark answer key ile training
- raw score’u tek hedef yapmak
- title-only fallback’i başarı saymak
- LLM fine-tuning

---

## Nihai Not

Phase 17F sonrası sistem artık ciddi bir performans seviyesine ulaştı.
Phase 18’in işi yeni kaynak aramak değil; **kanıtı zorunlu hukuki cevap slotlarına dönüştürmek ve confidence politikasını claim-level olarak kalibre etmek**.

Başarı ölçütü daha uzun cevap değil; daha eksiksiz, kanıta bağlı ve rubric-sufficient cevap.
