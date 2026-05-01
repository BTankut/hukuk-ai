# Hukuk-AI — Phase 22F P0 Shadow Backfill Implementation Brief

## Karar

Phase 22S **kabul edilmiştir**.

Resmî kaynak edinimi tamamlandı:

- required source package: `7/7`
- downloaded successfully: `7/7`
- SHA-256 populated: `7/7`
- raw_file_path populated: `7/7`
- parser_ready: `7/7`
- article_boundaries_detectable: `7/7`
- OCR required: `false`
- guard script: `EXIT_CODE=0`

Phase 22S kararı:

```text
Option A — Phase 22F ready
```

Bu nedenle sıradaki faz:

```text
Phase 22F — P0 Shadow Backfill Implementation
```

Phase 22F live collection’a yazmayacak.  
Phase 22F shadow-only çalışacak.  
Productization kapalı.  
Fine-tuning kapalı.

---

## 1. Phase 22F Ana Hedef

P0 blocker’lar için resmî kaynak bundle’ı kullanarak shadow collection üzerinde corpus/source materialization backfill yapmak.

P0 rows:

```text
MULGA-01
TEB-06
```

Hedef:

- `MULGA-01` için historical/repealed source + repeal/current-law bridge + current basis materialize etmek
- `TEB-06` için 23093 tebliğ body spans ve supporting source chain materialize etmek
- Bunları live collection’a değil, shadow collection’a yazmak
- Targeted smoke ve full benchmark ile doğrulamak
- Başarılıysa ayrı cutover decision üretmek

---

## 2. Kesin Kurallar

Phase 22F boyunca:

- live Milvus collection overwrite yok
- live source catalog overwrite yok
- benchmark answer key kullanılmayacak
- runtime prompt / model / fine-tuning değişikliği yok
- source identity heuristic patch yok, unless shadow backfill validation açıkça gerektirirse ayrı mini-commit ve smoke gate ile
- answer synthesis patch yok
- answer slot patch yok
- QID-specific runtime rule yok
- productization yok
- fine-tuning yok

Bu faz corpus materialization + shadow validation fazıdır.

---

## 3. Shadow Collection

## Target collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## Source baseline

```text
mevzuat_faz1_shadow_20260418_compat1024
```

## Kurallar

- Mevcut production/benchmark shadow collection değiştirilmeyecek.
- Backfill yeni shadow collection üzerinde yapılacak.
- Yeni source catalog / supplement / provenance hash üretilecek.
- Runtime sadece candidate endpoint veya explicit env ile bu shadow collection’a bağlanacak.
- Live `8000` cutover yapılmayacak.

---

## 4. Phase 22F-A — Backfill Source Bundle Verification

## Amaç

Phase 22S’de edinilen raw source bundle’ın Phase 22F tarafından kullanılabilir olduğunu tekrar doğrulamak.

## Input artifacts

```text
reports/benchmark/phase_22S_official_source_acquisition_manifest.csv
reports/benchmark/phase_22S_raw_source_provenance.csv
reports/benchmark/phase_22S_parser_readiness_audit.csv
reports/benchmark/legal_review_returns/filled_phase_22M_official_source_acquisition_checklist.csv
reports/benchmark/source_acquisition/phase_22S/raw/
reports/benchmark/source_acquisition/phase_22S/provenance/
```

## Output

```text
reports/benchmark/phase_22F_source_bundle_verification.md
reports/benchmark/phase_22F_source_bundle_verification.csv
```

## Kontroller

Her source için:

```text
source_title
official_url
raw_file_path_exists
sha256_matches
parser_ready
article_boundaries_detectable
required_article_scope_present
phase22F_use_allowed
blocking_reason
```

## Acceptance

- Required 7 source için hash match olmalı.
- Phase22F use allowed true olmalı.
- Eksik varsa shadow backfill başlamamalı.

## Commit

```text
Verify Phase 22F source bundle
```

Push zorunlu.

---

## 5. Phase 22F-B — Deterministic Text Extraction and Span Materialization

## Amaç

Raw source files’dan deterministic text extraction yapıp canonical article/span materialization üretmek.

## Output directories

```text
reports/benchmark/source_acquisition/phase_22F/normalized/
reports/benchmark/source_acquisition/phase_22F/spans/
reports/benchmark/source_acquisition/phase_22F/catalog_delta/
```

## Output reports

```text
reports/benchmark/phase_22F_text_extraction_report.md
reports/benchmark/phase_22F_span_materialization_report.md
reports/benchmark/phase_22F_catalog_delta_report.md
```

## Required materialization

### MULGA-01

Materialize / update:

```text
2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği
2023 repeal instrument
2547 sayılı Kanun m.54
historical/repealed state relation
current-law bridge relation
```

Required state:

```text
16532 must not be treated as directly active for 2026 reference date
historical regulation text must be retrievable as historical source
2547 m.54 must be retrievable as current-law basis
repeal instrument must be linked
```

### TEB-06

Materialize:

```text
23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ
m.4-m.8
m.6
m.8
6102 TTK m.210
Ticaret Sicili Yönetmeliği relevant provisions
2021 amendment instrument for current text control
```

Required state:

```text
23093 title-only/body=0 spans must be replaced or supplemented by body-bearing article spans
source chain must distinguish primary tebliğ and supporting law/regulation
```

## Canonical requirements

Every new/updated span must include:

```text
canonical_source_key_v2
binding_source_key
source_family
source_identifier
official_url
raw_sha256
span_type
article_no
paragraph_no
char_start
char_end
span_hash
effective_state
effective_start
effective_end if available
relation metadata if applicable
```

## Commit

```text
Materialize Phase 22F P0 official source spans
```

Push zorunlu.

---

## 6. Phase 22F-C — Build P0 Shadow Collection

## Amaç

Backfilled corpus delta ile yeni shadow collection oluşturmak.

## Target

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## Output

```text
reports/benchmark/phase_22F_shadow_collection_build_report.md
reports/benchmark/phase_22F_shadow_runtime_provenance.json
```

## Report fields

```text
base_collection
target_collection
base_entity_count
target_entity_count
delta_entity_count
vector_dimension
embedding_backend
embedding_model
source_catalog_hash
source_supplement_hash
backfill_source_count
backfill_span_count
canonical_key_collision_count
binding_key_collision_count
build_status
```

## Acceptance

- Build successful
- `canonical_key_collision_count = 0`
- `binding_key_collision_count = 0`
- Target entity count >= base entity count
- Runtime provenance complete

## Commit

```text
Build Phase 22F P0 shadow collection
```

Push zorunlu.

---

## 7. Phase 22F-D — Candidate Runtime Binding and Targeted Smoke

## Amaç

Live `8000` değiştirilmeden candidate runtime’ı P0 shadow collection’a bağlamak ve targeted smoke koşmak.

## Candidate runtime

Use a candidate port, for example:

```text
http://127.0.0.1:8018/v1
```

Do not cut over live `8000`.

## Required provenance

```text
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
DGX_MODEL=/models/merged_model_fabric_stage_20260321
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
guardrails=false for benchmark runtime
presidio=false for benchmark runtime
```

## Targeted smoke QIDs

```text
MULGA-01
MULGA-02
MULGA-03
MULGA-04
MULGA-05
TEB-01
TEB-02
TEB-03
TEB-04
TEB-05
TEB-06
TEB-07
TEB-08
```

## Targeted smoke acceptance

```text
MULGA >= 4/5
TEBLIGLER >= 7/8 preferred, >=6/8 minimum
MULGA-01 improves or is correctly classified as legal/corpus residual
TEB-06 improves or is correctly classified as legal/corpus residual
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
repealed_as_active_count = 0
```

## Output

```text
reports/benchmark/phase_22F_targeted_smoke_report.md
```

## Commit

```text
Run Phase 22F targeted P0 shadow smoke
```

Push zorunlu.

---

## 8. Phase 22F-E — Regression Guard Smoke

## Amaç

P0 backfill’in önceki kazanımları bozmadığını doğrulamak.

## Regression QIDs

```text
CBG-01 CBG-02 CBG-03 CBG-04
CBKAR-01 CBKAR-02 CBKAR-03 CBKAR-04 CBKAR-05 CBKAR-06 CBKAR-07 CBKAR-08
YON-01 YON-02 YON-03 YON-04 YON-05 YON-06 YON-07 YON-08 YON-09 YON-10
UY-07 UY-08
KANUN-03 KANUN-04 KANUN-19
```

## Acceptance

```text
CB_GENELGE = 4/4
CB_KARAR >= 7/8, preferred 8/8
YONETMELIK >= 7/10, preferred 9/10
UY focused no regression
KANUN relation no regression
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
```

## Output

```text
reports/benchmark/phase_22F_regression_guard_report.md
```

## Commit

```text
Run Phase 22F regression guard smoke
```

Push zorunlu.

---

## 9. Phase 22F-F — Full Benchmark on Shadow

## Amaç

P0 shadow backfill’in full 100 benchmark üzerindeki etkisini ölçmek.

## Run

Use candidate runtime bound to shadow collection:

```text
api_url=http://127.0.0.1:8018/v1
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## Target metrics

Phase 22A baseline:

```text
raw_score_proxy = 800.55
pass_proxy = 89/100
wrong_family = 6
wrong_document = 5
hallucinated_identifier = 5
```

Phase 22F targets:

| Metric | Target |
|---|---:|
| raw_score_proxy | `>= 805` preferred, `>= 800` minimum |
| pass_proxy | `>= 90` preferred, `>= 89` minimum |
| wrong_family | `<= 5` |
| wrong_document | `<= 4` |
| hallucinated_identifier | `<= 4` |
| unsupported_confident_claim | `<= 2` |
| unsupported_confident_answer | `0` |
| answer_contract_invalid | `0` |
| contract_valid | `100/100` |
| green_lane | `PASS` |
| source_key_v2_collision | `0` |
| binding_collision | `0` |

## Output

```text
reports/benchmark/phase_22F_full_shadow_benchmark_summary.md
reports/benchmark/phase_22F_delta_vs_phase22A.md
reports/benchmark/phase_22F_decision.md
```

## Commit

```text
Run Phase 22F full shadow benchmark
```

Push zorunlu.

---

## 10. Phase 22F Decision

## Option A — Shadow backfill improves and safety clean

```text
Prepare controlled cutover brief
No automatic live cutover
Productization still closed until cutover + serving config audit
Fine-tuning closed
```

## Option B — Shadow backfill safety clean but no score improvement

```text
Keep shadow backfill as corpus improvement candidate
Do not cut over yet
Open residual scorer/legal audit
```

## Option C — Shadow backfill regresses

```text
Discard shadow collection
Do not cut over
Return to corpus materialization analysis
```

## Option D — Parser/materialization insufficient

```text
Open Phase 22P parser/materialization preparation
No cutover
```

---

## 11. Stop Rules

Stop immediately if:

- live collection is modified
- live `8000` is cut over without separate brief
- source_key_v2_collision > 0
- binding_collision > 0
- unsupported_confident_answer > 0
- answer_contract_invalid > 0
- CB_GENELGE drops below 4/4
- UY focused regresses
- raw score drops below 790
- pass drops below 87
- provenance missing or wrong collection
- shadow collection entity count unexpectedly below base count

---

## 12. Productization / Fine-Tuning

Productization remains closed.

Fine-tuning remains closed.

Phase 22F is not productization. It is shadow corpus validation.

Productization can be discussed only after:

```text
shadow backfill succeeds
controlled cutover succeeds
post-cutover full benchmark stable
serving config separated from benchmark config
guardrails/verification policy defined
residual risk register updated
```

Fine-tuning remains inappropriate while corpus/source materialization is still changing.

---

## 13. Required Final Report

Produce:

```text
reports/benchmark/phase_22F_p0_shadow_backfill_report.md
```

Report content:

1. commit SHA list
2. source bundle verification
3. text extraction summary
4. span materialization summary
5. catalog delta summary
6. shadow collection build summary
7. targeted P0 smoke result
8. regression guard result
9. full shadow benchmark result
10. delta vs Phase 22A
11. cutover recommendation
12. productization gate decision
13. fine-tuning gate decision
14. remaining risks

---

## Final Note

Phase 22S completed the official source acquisition gate.

Phase 22F may now implement shadow-only P0 backfill.

Do not modify live collection.  
Do not cut over live runtime.  
Do not change model behavior.  
Do not open productization.
