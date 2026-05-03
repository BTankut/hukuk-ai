# Hukuk-AI — Phase 24J-R2 Normalized Provenance Rerun Brief

## Karar

Phase 24J-R diagnostic tamamlandı ve karar:

```text
RERUN_WITH_NORMALIZED_PROVENANCE
```

Ana bulgu:

- BASE ve TARGET direct Milvus top24 sonuçları `MULGA-01`, `MULGA-05`, `TEB-06` için stabil.
- 17 yeni Phase24J span’ın hiçbiri bu üç guard QID için TARGET direct top100’e girmiyor.
- Regresyon span interference değil.
- Phase 24J-D smoke temiz collection-only karşılaştırma değil.
- TARGET runtime trace’lerinde:
  - `rerank_list` boş
  - `assembled_evidence` boş
  - selected span yok
- Provenance farklı:
  - `api_url`
  - `git_sha`
  - `lane`
  - `api_version`
  - collection
- Catalog/config/source supplement hash’leri eşit.

Bu nedenle sıradaki faz:

```text
Phase 24J-R2 — Normalized Provenance Rerun
```

Bu faz implementation fazı değildir.  
Amaç, aynı runtime provenance ile yalnız collection farkını test etmektir.

Productization kapalı.  
Fine-tuning kapalı.  
Internal eval kapalı.  
Live `8000` değişmeyecek.

---

## 1. Kesin Kurallar

Phase 24J-R2 boyunca:

- live `8000` değişmeyecek
- live/base collection değişmeyecek
- new backfill yapılmayacak
- prompt/model/top-k değişmeyecek
- source identity patch yok
- answer synthesis patch yok
- QID-specific rule yok
- benchmark answer key kullanılmayacak
- full benchmark yok, gate açılmadan yok
- internal eval yok
- productization yok
- fine-tuning yok

Bu faz sadece normalized provenance ile rerun fazıdır.

---

## 2. Phase 24J-R2-A — Runtime Provenance Normalization Plan

## Amaç

BASE ve TARGET karşılaştırmasını aynı kod, aynı lane config, aynı API version davranışı ve yalnız collection farkı ile koşulacak hale getirmek.

## Output

```text
reports/benchmark/phase_24J_R2_provenance_normalization_plan.md
reports/benchmark/phase_24J_R2_provenance_normalization_plan.json
```

## Plan must specify

```text
same git_sha
same code checkout
same env except MILVUS_COLLECTION
same DGX_MODEL
same embedding model
same vector dimension
same guardrails/verification state
same source catalog hash
same source supplement hash
same API command template
BASE port
TARGET port
BASE collection
TARGET collection
collection load verification command
health check command
trace completeness check
```

## Collections

```text
BASE_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
TARGET_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j
```

## Commit

```text
Plan Phase 24J-R2 normalized provenance rerun
```

Push required.

---

## 3. Phase 24J-R2-B — Collection Load / Availability Verification

## Amaç

Her iki collection’ın Milvus tarafında load/available olduğunu ve entity count’larının beklendiğini doğrulamak.

## Output

```text
reports/benchmark/phase_24J_R2_collection_load_verification.md
reports/benchmark/phase_24J_R2_collection_load_verification.json
```

## Expected

```text
BASE entity_count = 349403
TARGET entity_count = 349420
vector_dimension = 1024
index available
collection loaded before runtime smoke
```

## Acceptance

- BASE loaded.
- TARGET loaded.
- Entity counts match.
- If TARGET is NotLoad, explicitly load it before smoke.
- If load fails, stop and report; do not run smoke.

## Commit

```text
Verify Phase 24J-R2 collection load state
```

Push required.

---

## 4. Phase 24J-R2-C — Start Matched BASE and TARGET Candidate Runtimes

## Amaç

Aynı runtime provenance ile iki candidate çalıştırmak.

## Recommended ports

```text
BASE_API=http://127.0.0.1:8032/v1
TARGET_API=http://127.0.0.1:8033/v1
```

## Required identical fields

```text
git_sha
api_version if controllable
lane template
model
DGX_MODEL
embedding model
guardrails state
verification state
presidio state
source catalog hash
source supplement hash
```

## Only allowed difference

```text
MILVUS_COLLECTION
```

## Output

```text
reports/benchmark/phase_24J_R2_runtime_pair_provenance.md
reports/benchmark/phase_24J_R2_runtime_pair_provenance.json
```

## Acceptance

- BASE health OK.
- TARGET health OK.
- Both `/v1/models` OK.
- Provenance diff shows only collection/entity count/port differences.
- If any non-collection provenance differs, stop and fix runtime setup before smoke.

## Commit

```text
Start Phase 24J-R2 matched candidate runtimes
```

Push required.

---

## 5. Phase 24J-R2-D — Critical Guard Paired Smoke

## Amaç

BASE and TARGET matched runtimes üzerinde aynı critical guard QID’leri koşmak.

## QIDs

```text
MULGA-01
MULGA-05
TEB-06
```

## Output

```text
reports/benchmark/phase_24J_R2_critical_guard_paired_smoke.md
reports/benchmark/phase_24J_R2_critical_guard_paired_smoke.csv
```

## Required compare fields

```text
qid
base_score
target_score
base_pass
target_pass
base_selected_source
target_selected_source
base_selected_span
target_selected_span
base_rerank_list_present
target_rerank_list_present
base_assembled_evidence_present
target_assembled_evidence_present
base_contract_valid
target_contract_valid
base_unsupported_confident
target_unsupported_confident
base_source_key_v2_collision
target_source_key_v2_collision
base_binding_collision
target_binding_collision
```

## Acceptance

```text
TARGET rerank_list non-empty
TARGET assembled_evidence non-empty
TARGET contract_valid all
TARGET unsupported_confident_answer = 0
TARGET source_key_v2_collision = 0
TARGET binding_collision = 0
MULGA-01 no regression vs BASE
MULGA-05 no regression vs BASE
TEB-06 no regression vs BASE
```

## If fails

Do not proceed to broader smoke. Produce diagnostic.

## Commit

```text
Run Phase 24J-R2 critical guard paired smoke
```

Push required.

---

## 6. Phase 24J-R2-E — Residual Targeted Paired Smoke

Only run if R2-D passes.

## QIDs

Affected rows:

```text
KANUN-12
KKY-03
TUZUK-04
YON-04
```

Guard rows:

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

## Output

```text
reports/benchmark/phase_24J_R2_residual_targeted_paired_smoke.md
reports/benchmark/phase_24J_R2_residual_targeted_paired_smoke.csv
```

## Acceptance

```text
TARGET no regression on critical guards
TARGET contract_valid all
TARGET unsupported_confident_answer = 0
TARGET source_key_v2_collision = 0
TARGET binding_collision = 0
TUZUK-04 not claimed active current law
At least one affected residual improves OR document why none improved
```

## Commit

```text
Run Phase 24J-R2 residual targeted paired smoke
```

Push required.

---

## 7. Phase 24J-R2-F — Decision Report

## Output

```text
reports/benchmark/phase_24J_R2_normalized_provenance_decision.md
```

## Decision options

### Option A — TARGET is clean and improves/no-regresses

```text
Open Phase 24K-R2 full shadow benchmark on TARGET
```

### Option B — TARGET clean but no improvement

```text
Keep Phase24J collection as diagnostic only
No full benchmark
```

### Option C — TARGET still loses guards

```text
Root cause is not provenance; open selector/evidence assembly audit
No full benchmark
```

### Option D — TARGET trace still empty

```text
Open runtime collection binding / load bug investigation
No full benchmark
```

## Commit

```text
Record Phase 24J-R2 normalized provenance decision
```

Push required.

---

## 8. Optional Phase 24K-R2 — Full Shadow Benchmark

Only if R2-F Option A.

## Runtime

Use TARGET matched runtime.

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

## Output

```text
reports/benchmark/phase_24K_R2_full_shadow_summary.md
reports/benchmark/phase_24K_R2_delta_vs_phase23RE.md
reports/benchmark/phase_24K_R2_green_lane_summary.md
```

## Commit

```text
Run Phase 24K-R2 full shadow benchmark
```

Push required.

---

## 9. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24J_R2_normalized_provenance_rerun_report.md
```

Must include:

1. commit SHA list
2. provenance normalization plan
3. collection load verification
4. runtime pair provenance
5. critical guard paired smoke
6. residual targeted paired smoke if run
7. decision
8. full shadow benchmark if run
9. productization decision
10. fine-tuning decision
11. live 8000 final state
12. next recommended phase

## Commit

```text
Report Phase 24J-R2 normalized provenance rerun outcome
```

Push required.

---

## 10. Productization / Fine-Tuning

Productization remains closed.

Fine-tuning remains closed.

Reason:

```text
Phase24J regression was not yet proven to be a real collection/content regression.
Normalized provenance rerun must resolve this first.
```

---

## Final Note

The diagnostic showed collection content is probably not the problem.

Do not patch logic until BASE/TARGET are compared under identical runtime provenance.
