# Hukuk-AI — Phase 19 R3F/R3G Execution Brief After R3E

## Karar

R3D ve R3E **kabul edilebilir**.

Phase 19 refactor hattı hâlâ davranış koruyucu ilerliyor:

- R1: runtime trace extraction tamamlandı.
- R2: source supplement extraction tamamlandı.
- T1: test expectation triage tamamlandı.
- R3A: source-family identity primitive extraction tamamlandı.
- R3B: chunk source-family profile extraction tamamlandı.
- R3C: source identity match primitive extraction tamamlandı.
- R3D: metadata-first catalog lookup extraction tamamlandı.
- R3E: source-key v2 binding helper extraction tamamlandı.

Özellikle R3D ve R3E sonrası 20-QID smoke’un önceki R3 adımlarıyla aynı kalması kritik:

- `raw_score_proxy = 140.23 / 200`
- `pass_proxy = 15/20`
- `contract_valid = 20/20`
- `unsupported_confident_answer = 0`
- `source_key_v2_collision_detected_count = 0`
- `binding_source_key_collision_detected_count = 0`
- `canonical_key_binding_applied_count = 20`
- `binding_source_key_version = canonical_source_key_v2` for all 20

Bu, source-key v2 extraction’ın davranış koruyucu olduğunu gösteriyor.

Ancak R3 artık en riskli aşamaya giriyor:

1. `identity rerank body`
2. `family gate helpers`
3. `source lock`
4. `selected-source retention`

Bu parçalar doğrudan selected document / selected family davranışını değiştirebilir. Bu nedenle R3F ve R3G fixture-backed ve stop-rule kontrollü yürütülmeli.

---

## 1. R3E Sonrası Önemli Uyarı

R3E sırasında bir invalid run yaşanmış:

- gateway remote embedding yerine `hashing` backend ile kalkmış
- selected evidence boşalmış
- düşük skorlar oluşmuş
- run discard edilmiş

Bu iyi yakalanmış. Bundan sonra her refactor smoke öncesi runtime provenance zorunlu kontrol edilmeli:

```text
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
MILVUS_ENTITY_COUNT=349191
VECTOR_DIMENSION=1024
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
DGX_MODEL=/models/merged_model_fabric_stage_20260321
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

Provenance bu değerlerden saparsa smoke sonucu invalid kabul edilsin.

---

# 2. R3F — Identity Rerank Body Extraction

## Amaç

`_rerank_chunks_by_source_identity(...)` body ve ona bağlı scoring/helper logic’i `api-gateway/src/rag/source_identity.py` içine taşımak.

Bu R3’ün en riskli adımıdır.

## Neden riskli?

Çünkü bu fonksiyon ve bağlı helper’lar:

- selected document
- selected source family
- title/identifier/issuer/year match
- document identity score
- lock strength
- metadata-first preference
- selected source cluster scoring

davranışını doğrudan etkileyebilir.

## Ön Koşul

`phase_19_R3F_identity_rerank_fixture.md` fixture oluşturulmuş. Bu iyi.

R3F extraction sonrası aynı fixture ile before/after karşılaştırması yapılmalı.

Fixture QID’leri:

- `CBG-01`
- `CBKAR-01`
- `CBKAR-08`
- `MULGA-02`
- `YON-01`
- `TEB-01`
- `KANUN-01`
- `UY-07`

## R3F Hard Stop Rule

Aşağıdakilerden biri olursa R3F durdurulmalı ve rollback/repair yapılmalı:

- fixture’da selected source family değişirse
- fixture’da selected document değişirse
- top post-rerank citation değişirse
- document identity score anlamlı değişirse
- lock strength değişirse
- reason prefix değişirse ve format-only olduğu kanıtlanamazsa
- 20-QID smoke’da wrong_family veya wrong_document artarsa
- source-key v2 / binding collision > 0 olursa

## Taşınacak Sorumluluklar

`source_identity.py` içine taşınacaklar:

- `_rerank_chunks_by_source_identity(...)` body
- document identity scoring helpers
- title match classification
- identifier match classification
- issuer match classification
- year match classification
- identity lock strength helpers
- metadata-selected source preference logic
- selected source cluster scoring helpers
- rerank reason construction helpers

## Taşınmayacaklar

Şimdilik yerinde kalsın:

- final family gate arbitration
- source lock finalization
- selected-source retention final step
- prompt construction
- answer synthesis
- answer contract repair
- confidence policy

## Kurallar

- rerank weights değişmeyecek
- candidate ordering değişmeyecek
- tie-break değişmeyecek
- score thresholds değişmeyecek
- no new heuristic
- no cleanup refactor beyond extraction
- no QID-specific behavior
- function signature mümkün olduğunca korunmalı
- router-level compatibility wrapper geçici olarak kalabilir

---

## R3F Test Plan

### Compile

```bash
api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/routers/chat.py \
  api-gateway/src/rag/source_identity.py
```

### Focused tests

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "source_identity_reranker or selected_source_cluster or metadata_selected_source or title_match or identifier_match" -q
```

Known stale T1 expectation gerekirse hariç tutulabilir; ancak R3F ile ilgili yeni failure çıkarsa ciddiye alınmalı.

### Fixture comparison

Yeni script veya rapor üret:

```text
reports/benchmark/phase_19_R3F_identity_rerank_after_extraction_fixture_diff.md
reports/benchmark/phase_19_R3F_identity_rerank_after_extraction_fixture_diff.csv
```

Karşılaştırılacak alanlar:

```text
qid
pre_count
pre_top
first_changed
identity_rerank_input_source
post_top
document_identity_score
title_match_type
identifier_match_type
lock_strength
reason_prefix
selected_family
selected_document
selected_article
```

### Smoke

20-QID recovery smoke:

```text
CBG-01 CBG-02 CBG-03 CBG-04
MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05
CBKAR-01 CBKAR-02 CBKAR-08
YON-01 YON-02 YON-03
KANUN-01 KANUN-06 KANUN-15
TEB-01 TEB-02
```

Additional focused smokes:

- CB_GENELGE 4-QID
- MULGA 5-QID
- YONETMELIK boundary mini:
  - `YON-01`
  - `YON-02`
  - `YON-03`
  - `YON-05`
- strong family guard:
  - `UY-07`
  - `UY-08`
  - `KKY-10`

## Acceptance Criteria

R3F kabul için:

- Fixture diff behavior-preserving olmalı.
- 20-QID smoke:
  - `raw_score_proxy >= 130/200`
  - `pass_proxy >= 12/20`
  - `wrong_family <= 3`
  - `wrong_document <= 5`
  - `contract_valid = 20/20`
  - `unsupported_confident_answer = 0`
- `source_key_v2_collision_detected_count = 0`
- `binding_source_key_collision_detected_count = 0`
- `canonical_key_binding_applied_count = 20`
- CB_GENELGE 4/4 korunmalı
- UY guard korunmalı
- MULGA smoke `>= 3/5` hedeflenmeli

## Commit

### Commit R3F

- identity rerank body extraction
- fixture diff report
- focused tests
- smoke reports

Push zorunlu.

---

# 3. R3G — Family Gate / Source Lock / Selected-Source Retention Extraction

## Amaç

Family gate helpers, source lock ve selected-source retention logic’i `api-gateway/src/rag/source_identity.py` içine taşımak.

Bu da yüksek risklidir çünkü final selected source davranışına çok yakındır.

## R3G Ön Koşul

R3F başarıyla tamamlanmadan R3G’ye geçilmemeli.

## Taşınacak Sorumluluklar

- family gate status helpers
- preferred family pool helpers
- selected-source retention helpers
- source lock key matching helpers
- primary vs supporting source retention utilities
- selected source claim normalization helpers, sadece source identity ile ilgili olanlar
- source retention reason helpers

## Taşınmayacaklar

- answer synthesis
- answer contract repair
- confidence policy
- prompt building
- text generation
- final response rendering

## Kurallar

- source lock thresholds değişmeyecek
- preferred family behavior değişmeyecek
- source retention priority değişmeyecek
- supporting/primary separation değişmeyecek
- no new family rule
- no QID-specific logic

---

## R3G Test Plan

### Focused tests

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "family_gate or preferred_family or selected_source_retention or source_lock or primary_source" -q
```

### Smoke

20-QID recovery smoke.

KANUN primary/supporting smoke:

- `KANUN-03`
- `KANUN-04`
- `KANUN-09`
- `KANUN-19`

YONETMELIK boundary smoke.

CB_GENELGE smoke.

## Acceptance Criteria

- 20-QID recovery smoke passes baseline gate
- supporting source does not overwrite primary source
- family gate statuses materially unchanged
- no increase in wrong family
- no increase in wrong document
- CB_GENELGE remains 4/4
- KANUN relation rows do not regress

## Commit

### Commit R3G

- family gate / source lock / retention extraction
- focused tests
- smoke report

Push zorunlu.

---

# 4. R3 Completion Gate

R3D, R3E, R3F, R3G tamamlandıktan sonra full R3 kapanış raporu üret.

## Required Report

```text
reports/benchmark/phase_19_R3_source_identity_extraction_report.md
```

İçerik:

1. R3A–R3G commit list
2. taşınan helper/function listesi
3. hala `chat.py` içinde kalan source-identity logic
4. test sonuçları
5. fixture diff özeti
6. 20-QID smoke delta tablosu
7. CB_GENELGE / MULGA / YON / UY focused smoke sonuçları
8. known stale tests
9. R4’e geçilebilir mi?

## R3 Completion Acceptance

- 20-QID smoke:
  - `raw_score_proxy >= 130/200`
  - `pass_proxy >= 12/20`
  - `wrong_family <= 3`
  - `wrong_document <= 5`
  - `unsupported_confident_claim <= 1`
  - `contract_valid = 20/20`
  - `source_key_v2_collision = 0`
  - `binding_source_key_collision = 0`
- CB_GENELGE 4/4
- MULGA >= 3/5
- UY strong-family smoke preserved
- no provenance issue
- no new broad failure caused by extraction

---

# 5. R4 Prep — Article / Span Selection Extraction

R4 başlamadan önce inventory çıkar:

```text
reports/benchmark/phase_19_R4_article_span_selection_inventory.md
```

Inventory şunları içermeli:

- `chat.py` içinde kalan article/span selector functions
- dependencies:
  - source identity
  - temporal helpers
  - answer slot helpers
  - trace helpers
- risk level
- extraction order

Fixture oluştur:

```text
reports/benchmark/phase_19_R4_article_span_fixture.md
```

Fixture QID’leri:

- `CBKAR-08`
- `KANUN-06`
- `KKY-09`
- `YON-07`
- `TEB-01`
- `MULGA-03`

R4’e sadece R3 completion gate geçerse başla.

---

# 6. Stop Rules

Aşağıdakilerden biri olursa dur:

- fixture selected source değişirse
- fixture selected document değişirse
- 20-QID smoke `wrong_family +2`
- 20-QID smoke `wrong_document +2`
- CB_GENELGE < 4/4
- source-key v2 collision > 0
- binding source-key collision > 0
- contract_valid < 100%
- gateway errors/refusals
- provenance missing or wrong runtime env

---

## Final Note

R3D ve R3E güvenli geçti.  
R3F ve R3G davranışa en yakın extraction adımlarıdır.

Bu aşamada “temizlik” bile risklidir.  
Sadece kodu taşı, fixture ile eşdeğerliği kanıtla, smoke ile güvence altına al.
