# Hukuk-AI — Phase 24J Targeted Shadow Backfill for Confirmed Residual Sources Brief

## Karar

Phase 24I update kabul edilmiştir.

Repo doğrulamasına göre:

- `KANUN-12`: confirmed + parser_ready + SHA verified
- `KKY-03`: confirmed + parser_ready + SHA verified; source family `YONETMELIK`, not `KKY`
- `TUZUK-04`: confirmed + parser_ready + SHA verified; only historical/repealed-source handling
- `YON-04`: confirmed + parser_ready + SHA verified
- `TUZUK-05`: still `not_found / needs_more_review`

Bu nedenle sıradaki faz:

```text
Phase 24J — Targeted Shadow Backfill for Confirmed Residual Sources
```

Bu faz yalnız shadow-only çalışacak.  
Live `8000` değişmeyecek.  
Productization kapalı.  
Fine-tuning kapalı.  
Internal eval kapalı.

---

## 1. Amaç

Dört confirmed residual source için shadow-only backfill/materialization yapmak:

```text
KANUN-12
KKY-03
TUZUK-04
YON-04
```

Amaç:

1. Raw source bundle doğrulamak.
2. Deterministic text/span materialization yapmak.
3. Shadow collection oluşturmak veya mevcut p0_backfill shadow üzerine yeni shadow delta üretmek.
4. Targeted residual smoke çalıştırmak.
5. Guard smoke çalıştırmak.
6. Uygunsa full shadow benchmark çalıştırmak.
7. Internal-eval readiness’i yeniden değerlendirmek.

---

## 2. Kesin Kurallar

Phase 24J boyunca:

- live `8000` değişmeyecek
- live/base collection overwrite edilmeyecek
- productization açılmayacak
- fine-tuning açılmayacak
- public serving açılmayacak
- broad retrieval/top-k değiştirilmeyecek
- prompt/model değiştirilmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- TUZUK-05 için işlem yapılmayacak
- TUZUK-04 current-law authority gibi kullanılmayacak; yalnız historical/repealed handling

---

## 3. Source Inputs

Confirmed raw files:

```text
reports/benchmark/source_acquisition/phase_24I/raw/kanun_12_5651_official_source.txt
reports/benchmark/source_acquisition/phase_24I/raw/kky_03_bddk_bilgi_sistemleri_official_source.txt
reports/benchmark/source_acquisition/phase_24I/raw/tuzuk_04_radyasyon_guvenligi_official_source.txt
reports/benchmark/source_acquisition/phase_24I/raw/yon_04_kvkk_silme_yok_etme_anonim_official_source.txt
```

Confirmed SHA values are in:

```text
reports/benchmark/phase_24I_official_source_acquisition_return_validation.md
reports/benchmark/phase_24I_official_source_acquisition_return_validation.csv
```

---

## 4. Phase 24J-A — Source Bundle Verification

## Output

```text
reports/benchmark/phase_24J_source_bundle_verification.md
reports/benchmark/phase_24J_source_bundle_verification.csv
```

## Checks

For each of the four sources:

```text
qid
raw_file_path_exists
sha256_matches
parser_ready
legal_confirmation
source_family_confirmed
article_boundaries_detectable
phase24J_use_allowed
blocking_reason
```

## Acceptance

- 4/4 source bundle verified.
- `TUZUK-04` marked historical/repealed-only.
- `TUZUK-05` explicitly excluded.

## Commit

```text
Verify Phase 24J confirmed source bundle
```

Push required.

---

## 5. Phase 24J-B — Text Extraction and Span Materialization

## Output dirs

```text
reports/benchmark/source_acquisition/phase_24J/normalized/
reports/benchmark/source_acquisition/phase_24J/spans/
reports/benchmark/source_acquisition/phase_24J/catalog_delta/
```

## Reports

```text
reports/benchmark/phase_24J_text_extraction_report.md
reports/benchmark/phase_24J_span_materialization_report.md
reports/benchmark/phase_24J_catalog_delta_report.md
```

## Required materialization

### KANUN-12

```text
5651 sayılı Kanun as primary source
supporting internet cafe / public internet provider regulation only as support
relevant article spans from raw source
primary/supporting relation preserved
```

### KKY-03

```text
Source family must be YONETMELIK, not KKY
confirmed spans: m.13, m.29, m.34, m.37, m.46
BDDK regulation identity preserved
```

### TUZUK-04

```text
Radyasyon Güvenliği Tüzüğü as historical/repealed source
2023 repeal relation preserved if available
must not be standalone current-law authority
historical/repealed effective_state required
```

### YON-04

```text
KVKK deletion/destruction/anonymization regulation
article spans m.7-m.12
6698 m.7 as supporting legal basis
YONETMELIK primary source preserved
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
relation metadata if applicable
```

## Commit

```text
Materialize Phase 24J confirmed residual source spans
```

Push required.

---

## 6. Phase 24J-C — Build Phase 24J Shadow Collection

## Target collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j
```

## Base collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## Output

```text
reports/benchmark/phase_24J_shadow_collection_build_report.md
reports/benchmark/phase_24J_shadow_runtime_provenance.json
```

## Acceptance

```text
build_status = success
target_entity_count >= 349403
canonical_key_collision_count = 0
binding_key_collision_count = 0
vector_dimension = 1024
embedding_model unchanged
```

## Commit

```text
Build Phase 24J residual shadow collection
```

Push required.

---

## 7. Phase 24J-D — Candidate Runtime and Targeted Smoke

## Candidate runtime

Use a non-live candidate port, for example:

```text
http://127.0.0.1:8031/v1
```

## Runtime target

```text
lane = phase24j_residual_shadow
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j
model = /models/merged_model_fabric_stage_20260321
```

## Targeted QIDs

```text
KANUN-12
KKY-03
TUZUK-04
YON-04
```

## Guard QIDs

```text
MULGA-01
MULGA-05
TEB-04
TEB-06
CBG-01
CBKAR-08
UY-01
YON-05
```

## Acceptance

```text
answered = all
contract_valid = all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
no regression in MULGA-01/MULGA-05/TEB-06
TUZUK-04 not claimed as active current law
```

## Output

```text
reports/benchmark/phase_24J_targeted_shadow_smoke_report.md
```

## Commit

```text
Run Phase 24J targeted residual shadow smoke
```

Push required.

---

## 8. Phase 24K — Full Shadow Benchmark

Only run if Phase 24J targeted smoke passes.

## Runtime

```text
api_url = http://127.0.0.1:8031/v1
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j
```

## Output

```text
reports/benchmark/phase_24K_full_shadow_benchmark_summary.md
reports/benchmark/phase_24K_delta_vs_phase23RE.md
reports/benchmark/phase_24K_green_lane_summary.md
reports/benchmark/phase_24K_decision.md
```

## Minimum gate

```text
raw_score_proxy >= 816
pass_proxy >= 91
wrong_family <= 6
wrong_document <= 4
hallucinated_identifier <= 4
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

## Preferred improvement

```text
pass_proxy > 91
or wrong_document < 4
or at least 2 of 4 targeted residual rows improve
```

## Commit

```text
Run Phase 24K residual full shadow benchmark
```

Push required.

If not run, create:

```text
reports/benchmark/phase_24K_full_shadow_not_run.md
```

---

## 9. Phase 24L — Internal Eval Readiness Recheck

Run after Phase 24J/24K decision.

## Output

```text
reports/benchmark/phase_24L_after_phase24J_internal_eval_readiness_recheck.md
```

## Checks

```text
benchmark-only live stable
Phase24J shadow result
Phase24K full shadow result if run
internal_eval blocker rows status:
  KANUN-12
  KKY-03
  TEB-04
  TUZUK-05
  YON-04
legal/scorer review still pending?
TUZUK-05 still unresolved?
serving policy exists?
trace/manual review policy exists?
```

## Decision options

### Option A — Internal eval ready

```text
Open Phase 25A internal eval lane setup
```

### Option B — Limited legal-review eval only

```text
Open limited reviewer-only eval packet
No general internal eval
```

### Option C — Still not ready

```text
Continue residual closure
No internal eval
```

## Commit

```text
Recheck Phase 24L after Phase 24J residual remediation
```

Push required.

---

## 10. Phase 25A/B/C Handling

## If Phase 24L Option A

Proceed with:

```text
Phase 25A internal eval lane setup
Phase 25B monitoring plan
Phase 25C productization readiness recheck
```

## If Phase 24L Option B or C

Do not open internal eval. Produce not-run reports:

```text
reports/benchmark/phase_25A_not_run_after_phase24J.md
reports/benchmark/phase_25B_not_run_after_phase24J.md
reports/benchmark/phase_25C_productization_readiness_recheck_after_phase24J.md
```

Commit:

```text
Record Phase 25 status after Phase 24J
```

---

## 11. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24J_25C_targeted_shadow_backfill_execution_report.md
```

Must include:

1. commit SHA list
2. source bundle verification
3. text extraction/materialization summary
4. shadow collection build summary
5. targeted smoke result
6. full shadow benchmark result or not-run reason
7. internal eval readiness decision
8. Phase 25 run/not-run status
9. productization decision
10. fine-tuning decision
11. final live 8000 state
12. next required human/source/legal action

Commit:

```text
Report Phase 24J-25C targeted shadow backfill outcome
```

Push required.

---

## 12. Stop Rules

Stop immediately and do not proceed to full benchmark if:

```text
source bundle verification fails
sha mismatch
canonical/binding collision appears
targeted smoke has contract invalid
unsupported confident answer > 0
MULGA-01 or MULGA-05 regresses
TEB-06 regresses
TUZUK-04 is claimed as active current law
live 8000 is modified
base collection is modified
QID-specific runtime rule introduced
```

---

## 13. Final Note

Four source bundles are now confirmed and safe for targeted shadow backfill.

Do not touch TUZUK-05.  
Do not touch live 8000.  
Do not open internal eval unless Phase 24L approves it after evidence.
