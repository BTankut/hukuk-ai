# Hukuk-AI — Revised Engineering Task Brief After External Expert Review + Phase 17E

## Amaç

Bu doküman kod asistanına verilecek güncel görev brifidir.

Dış uzman değerlendirmesi ve Phase 17E CB_GENELGE recovery raporu birlikte değerlendirildi. Mevcut rota genel olarak doğru; fakat sonraki işler artık daha net sıralanmalı:

1. **Phase 17F full benchmark rerun**
2. **v2 source-key runtime binding’in tam doğrulanması**
3. **remaining corpus/body-span blockers**
4. **evidence-to-answer required slot synthesis**
5. **MULGA historical/current/transition slot completion**
6. **CB_GENELGE kalan iki kaynak için official source acquisition/materialization**
7. ancak bunlardan sonra fine-tuning değerlendirmesi

Fine-tuning hâlâ kapalıdır.

---

## 1. Şu Anki Durum

### Genel ilerleme

Başlangıçta sistem yaklaşık şu seviyedeydi:

- Raw score: `415 / 1000`
- PASS: `35 / 100`
- ciddi wrong source / hallucination
- answer contract eksikleri
- temporal validity ve mülga/current ayrımı zayıf
- CB_GENELGE, CB_KARAR, KANUN, YONETMELIK, TEBLIGLER, MULGA en sorunlu ailelerdi

Phase 16 itibarıyla:

- Raw score: yaklaşık `709 / 1000`
- PASS: `69 / 100`
- contract validity: `100/100`
- API errors: `0`
- unsupported confident: `0`
- wrong family: `12`
- canonical span materialized: `93`
- corpus materialization required: `6`

Bu büyük bir sistemik ilerlemedir. Ancak productization ve fine-tuning gate hâlâ kapalıdır.

### Ana kalan blokajlar

Phase 16 sonrası ana sorunlar:

- `missing_required_content_signal = 99`
- `partial_grounding_only = 99`
- `MULGA pass = 0/5`
- `CB_GENELGE pass = 0/4` idi
- kalan corpus/materialization satırları vardı
- v2 source-key trace’te çalışıyor ama tüm runtime binding path içinde primary identity olduğundan emin olmak gerekiyordu

---

## 2. Dış Uzman Değerlendirmesinden Alınan Ana Kararlar

Dış uzman görüşü genel rotanın doğru olduğunu teyit etti:

- Fine-tuning hâlâ erken.
- Sorun artık genel RAG kırığı değil.
- Ana problem:
  - canonical source identity runtime binding
  - corpus/body-span materialization
  - evidence-to-answer slot completeness
  - non-article instruments için uygun span modeli
  - MULGA ve CB_GENELGE gibi ailelere özel answer slotları

### Uzmanın önerdiği ana mimari

Aşağıdaki pipeline benimsenmeli:

```text
User Query
  ↓
Query Legal Parser
  ↓
Source Resolver
  ↓
Candidate Source Set
  ↓
Scoped Hybrid Retrieval
  ↓
Document Identity Selector
  ↓
Article / Body / Annex / Instruction Span Selector
  ↓
Evidence Bundle Builder
  ↓
Required Slot Extractor
  ↓
Slot Verifier
  ↓
Answer Synthesizer
  ↓
Claim-Level Verifier + Confidence Policy
  ↓
Final Answer
```

Ana prensip:

> Retrieval’dan sonra doğrudan cevap üretme. Önce zorunlu hukuki answer slotlarını evidence span’lerden doldur, doğrula, eksikleri işaretle; synthesis en son yapılsın.

---

## 3. Phase 17E Sonucu

Phase 17E, dar kapsamlı **CB_GENELGE recovery slice** olarak başarılı kabul edildi.

### Phase 17E kazanımları

- CB_GENELGE smoke pass: `1/4 -> 2/4`
- `corpus_materialization_required_count`: `1 -> 0`
- `canonical_span_materialized_count`: `3/4 -> 4/4`
- `evidence_slot_synthesis_count`: `1/4 -> 3/4`
- `unsupported_confident_answer_count = 0`
- `repealed_as_active_count = 0`
- `source_key_v2_collision_detected_count = 0`

### Düzeltilen satırlar

- `CBG-03`: 2025/3 Mobbing Genelgesi official source supplement ile düzeldi
- `CBG-04`: 2025/3 active source ve 2011/2 repeal clause ayrımı doğru kuruldu

### Açık kalan satırlar

- `CBG-01`: expected `2024/7` Tasarruf Tedbirleri source seçilemiyor
- `CBG-02`: expected `2019/12` Bilgi ve İletişim Güvenliği source seçilemiyor

Bu iki satır artık güvenli şekilde suppressed/backlog olarak kalıyor; yanlış-confident cevap üretilmiyor.

### Önemli karar

Phase 17E narrow slice accepted.
Ancak productization / fine-tuning gate hâlâ kapalı.
Şimdi Phase 17F full benchmark rerun yapılmalı.

---

# 4. Hemen Yapılacak İş: Phase 17F Full Benchmark Rerun

## Amaç

Phase 17E’deki CB_GENELGE kazanımlarının full 100 soruluk benchmark’a etkisini görmek ve Phase 17’nin genel durumunu netleştirmek.

## Koşulacak işler

Aşağıdaki full pipeline koşulmalı:

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py   --out-dir reports/benchmark/runs/<timestamp>_phase17_full   --api-url http://127.0.0.1:8000/v1   --model hukuk-ai-poc   --timeout 420   --retries 0   --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py   --answers reports/benchmark/runs/<timestamp>_phase17_full/candidate_answers.csv   --out-dir reports/benchmark/runs/<timestamp>_phase17_full

GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/<timestamp>_phase17_full   bash scripts/benchmark/run_green_lane.sh   --run-dir reports/benchmark/runs/<timestamp>_phase17_full
```

## Zorunlu audit/artifact seti

Full rerun sonrası şu raporlar üretilmeli:

- `phase_17_final_summary.md`
- `phase_17_score_summary.md`
- `phase_17_scored.csv`
- `phase_17_family_level_summary.md`
- `phase_17_cbgenelge_audit.md`
- `phase_17_mulga_audit.md`
- `phase_17_source_key_v2_binding_audit.md`
- `phase_17_corpus_materialization_audit.md`
- `phase_17_evidence_slot_coverage_audit.md`
- `phase_17_unsupported_confident_audit.md`
- `phase_17_phase_comparison.md`
- `phase_17_green_lane_summary.md`

## Full Phase 17 hedefleri

Aşağıdaki hedefler kontrol edilmeli:

| Metric | Target |
|---|---:|
| raw_score_proxy | `>= 735` |
| pass_proxy | `>= 73` |
| wrong_family | `<= 12` |
| wrong_document | `<= 15` |
| hallucinated_identifier | `<= 23` |
| unsupported_confident_claim | `<= 3` |
| corpus_materialization_required_count | `<= 3` |
| canonical_span_materialized_count | `>= 95` |
| missing_required_content_signal | `<= 92` |
| partial_grounding_only | `<= 92` |
| runtime rubric_sufficient | `>= 35/100` |
| MULGA pass | `>= 2/5` |
| CB_GENELGE pass | `>= 2/4` |

En az **9/13** hedef tutmalı.

## Commit / push

### Commit 1
- Phase 17E changes already implemented and verified
- Ensure report artifacts are committed

### Commit 2
- Phase 17F full run artifacts
- Phase 17 final summary
- Green lane output

Her commit sonrası push.

---

# 5. Phase 17F Sonrası Karar Ağacı

## Durum A — Phase 17F hedeflerin çoğunu tutturursa

Eğer en az 9/13 hedef geçerse:

- Phase 17 kısmi/koşullu kabul edilebilir.
- Sonraki faz **Phase 18 — Rubric-Aligned Completeness and Slot Recall** olmalı.
- Fine-tuning yine hemen açılmamalı; önce bir stabil rerun daha alınmalı.

## Durum B — CB_GENELGE hâlâ 2/4 altında kalırsa

Önce şu işler yapılmalı:

- `CBG-01` için `2024/7 Tasarruf Tedbirleri` official source acquisition/materialization
- `CBG-02` için `2019/12 Bilgi ve İletişim Güvenliği` official source acquisition/materialization
- CB_GENELGE circular body model genişletme
- slash-numbered identifiers ve topic scoring regresyon testi

## Durum C — MULGA hâlâ 0/5 kalırsa

Phase 18’den önce küçük bir **MULGA-only remediation slice** açılmalı:

- historical/repealed answer slots
- current applicability
- replacement/current-law relation
- transition rule
- 5-row MULGA smoke

## Durum D — missing_required_content_signal / partial_grounding_only hâlâ 95+ ise

Bu durumda retrieval eklemek yerine:

- required slot matrix yeniden tasarlanmalı
- task-type slot mapping genişletilmeli
- evidence-to-answer slot verifier güçlendirilmeli
- private rubric must-include sinyalleriyle human/judge calibration yapılmalı

---

# 6. Phase 18 İçin Şartlı Plan

Phase 17F sonrası yeterli zemin oluşursa Phase 18 açılabilir.

## Phase 18 adı

**Rubric-Aligned Evidence-to-Answer Slot Completion**

## Amaç

Cevapların sadece grounded değil, benchmark/private rubric’in beklediği zorunlu hukuki fact slotlarını da doldurması.

## Ana kavram

Her cevap şu slotlardan oluşmalı:

```yaml
answer_slots:
  - governing_source
  - exact_source_identity
  - article_or_span
  - temporal_validity
  - scenario_application
  - exception_or_limitation
  - transition_or_replacement_rule
  - procedure_or_consequence
  - document_selection_rationale
  - direct_legal_conclusion
```

Her slot şu metadata ile dönmeli:

```yaml
slot_name: string
required: bool
value: string | null
evidence_span_keys: string[]
extraction_method: deterministic | llm_schema | hybrid
fill_status: filled | missing | contradicted | unsupported | not_applicable
verifier_status: verified | failed | needs_review
confidence_0_100: int
slot_missing_reason: string | null
```

## Phase 18A — Required Slot Matrix

Task type bazında zorunlu slot haritası çıkar:

- precise_retrieval
- temporal_validity
- scenario_applicability
- hierarchy_conflict
- document_selection
- compliance_checklist
- exception_analysis
- current_update

## Phase 18B — Evidence-to-Slot Extraction

Hybrid extraction:

- deterministic:
  - source identity
  - article number
  - temporal metadata
  - repeal status
- LLM schema extraction:
  - scope
  - consequence
  - scenario application
  - exception
  - transition relation

## Phase 18C — Slot Verifier

Her slot evidence span ile doğrulanmalı:

- slot value retrieved span içinde destekleniyor mu?
- temporal validity doğru mu?
- supporting source ile primary source karışmış mı?
- transition/current relation açık mı?

## Phase 18D — Answer Synthesis from Verified Slots Only

Cevap serbest metinden önce slotlarla kurulmalı.

Eğer required slot eksikse:

- answer qualified olmalı
- confidence düşmeli
- missing slot açıkça final_reason’da görünmeli

---

# 7. Source-Key v2 için Zorunlu Teknik Not

Dış uzman görüşü source-key için hiyerarşik key ailesi önerdi.

Runtime’da şu key ailesi hedeflenmeli:

```yaml
instrument_key:
  jurisdiction: TR
  corpus_namespace: MEVZUAT
  source_family: string
  instrument_type: string
  issuing_authority_norm: string
  identifier_type: string
  identifier_norm: string
  title_norm_hash: string
  disambiguator_hash: string

version_key:
  instrument_key: string
  official_gazette_date: date | null
  official_gazette_no: string | null
  effective_start: date | null
  effective_end: date | null
  version_status: active | repealed | partially_repealed | amended | historical | unknown
  amendment_sequence: int | null
  raw_content_sha256: string
  doc_uuid: string

span_key:
  version_key: string
  span_type: article | temporary_article | additional_article | paragraph | clause | free_body | instruction_block | annex | table_row | preamble | repeal_clause | transition_clause
  article_no: string | null
  paragraph_no: string | null
  clause_no: string | null
  annex_no: string | null
  section_ordinal: int | null
  char_start: int
  char_end: int
  span_hash: string
```

Current proposed source key:

```text
{source_family}:{canonical_identifier}:{normalized_title_hash_or_doc_uuid}
```

Bu iyi başlangıçtır ama production için şu alanlar da düşünülmeli:

- issuing authority
- official gazette date/no
- effective interval
- version status
- content hash
- span type
- char offsets

Numeric `belge_no` yalnız alias olabilir. Cross-family identity key olarak tek başına kullanılmamalı.

---

# 8. Non-Article Document Families İçin Span Modeli

Article-first model her family için uygun değil.

## CB_GENELGE span türleri

```yaml
cb_genelge_spans:
  - title_span
  - subject_span
  - addressee_span
  - legal_basis_span
  - scope_span
  - instruction_block
  - implementation_procedure_span
  - effective_date_span
  - supersession_or_repeal_span
  - signature_span
```

## CB_KARAR / annex kararları

```yaml
decision_core:
  - decision_number
  - decision_date
  - issuer
  - publication
  - operative_clause
  - effective_date
  - annex_reference

decision_annex:
  - annex_no
  - annex_title
  - annex_article
  - annex_table
  - annex_row
  - annex_legal_effect
```

## TEBLIGLER

```yaml
teblig_required_slots:
  - source_identity
  - issuer
  - teblig_identifier
  - scope
  - operative_rule
  - procedure_or_formula
  - table_or_annex_reference
  - temporal_validity
  - exception
  - conclusion
```

## MULGA

```yaml
mulga_required_slots:
  - source_is_repealed_or_historical
  - applicable_period
  - current_applicability
  - replacement_or_current_law_relation
  - transition_rule
  - direct_legal_conclusion
  - no_active_law_overclaim
```

---

# 9. Reranking / Retrieval İçin Yeni Karar

Dış uzman önerisiyle sonraki 1-2 faz içinde **shadow eval** olarak eklenebilir:

1. source resolver before dense retrieval
2. BM25 / lexical retrieval
3. dense retrieval
4. hybrid candidate merge
5. cross-encoder reranker
6. family/source compatibility gate
7. span-level selector
8. slot-specific retrieval expansion

Öncelik:

- BM25 + dense hybrid standardization
- cross-encoder reranker shadow evaluation

Ancak bu Phase 17F’yi bloklamamalı. Önce full Phase 17 sonucu alınmalı.

---

# 10. Stop Doing / Dikkat

Şu işlere artık fazla zaman harcama:

- genel prompt tightening
- sadece confidence policy ekleme
- top-k dense retrieval’i büyütme
- article modelini her family’ye zorlama
- title-only fallback’i başarı sayma
- raw score’u tek hedef yapmak
- erken LLM fine-tuning

---

# 11. Kod Asistanı İçin Hemen Yapılacaklar

## Step 1 — Phase 17E Commit/Push Durumu

- Phase 17E commit edilmiş mi kontrol et.
- Değilse commit/push yap.
- Raporu `reports/benchmark/phase_17e_cbgenelge_completion_report.md` altında sakla.

## Step 2 — Phase 17F Full Run

- Full 100 benchmark koş.
- Scorer çalıştır.
- Green lane çalıştır.
- Aşağıdaki raporları üret:
  - `phase_17_final_summary.md`
  - `phase_17_score_summary.md`
  - `phase_17_family_level_summary.md`
  - `phase_17_cbgenelge_audit.md`
  - `phase_17_mulga_audit.md`
  - `phase_17_evidence_slot_coverage_audit.md`
  - `phase_17_source_key_v2_binding_audit.md`
  - `phase_17_phase_comparison.md`

## Step 3 — Phase 17F Decision

Şu sorulara cevap ver:

- CB_GENELGE full sette kaç pass?
- MULGA full sette kaç pass?
- unsupported confident hâlâ düşük mü?
- missing_required_content_signal düştü mü?
- partial_grounding_only düştü mü?
- source-key v2 runtime binding path gerçekten kullanılıyor mu?
- corpus materialization required kaç kaldı?

## Step 4 — Sonraki Faz Kararı

Full sonuçtan sonra:

- eğer source/corpus iyi ama completeness kötü ise Phase 18 slot completion
- eğer CB_GENELGE hâlâ kötü ise official source acquisition/materialization
- eğer MULGA hâlâ 0 ise MULGA-only remediation slice
- eğer materialization hâlâ yüksekse corpus/reindex fazı
- hiçbir koşulda fine-tuning açma

---

## Nihai Not

Phase 17E iyi bir dar slice başarısıdır.
Ama bu başarı full benchmarkta taşınmadan yeni mimari refactor’a veya fine-tuning’e geçilmemeli.

Önce full Phase 17F sonucu alınmalı.
Sonra Phase 18’in gerçekten slot-completeness mi, yoksa hâlâ corpus/source-key mi olacağına karar verilmeli.
