# Hukuk-AI — Phase 24R Matched Base-vs-CBY Evidence Run + TEB-04 Manual Raw Intake Brief

## Karar

Phase 24Q kararına göre sıradaki faz:

```text
Phase 24R — controlled evidence phase
```

Bu faz remediation merge değildir. Önce temiz A/B kanıt üretilecek.

Phase 24Q bulguları:

```text
CBY-06 span faydalı: 6.80 -> 8.58
Phase24P-R full shadow düştü: 816.86 -> 806.87
5 pass-to-fail row yeni CBY span içermiyor
CBY span interference doğrudan kanıtlanmadı
Phase23R-E vs Phase24P-R temiz aynı-runtime A/B değil
```

TEB-04 durumu:

```text
GİB KDV GUT PDF browser’da açılıyor
scripted local capture HTTP 400 JSON dönüyor
TEB-04 materialization raw PDF + SHA olmadan kapalı
```

Productization kapalı.  
Internal eval kapalı.  
Fine-tuning kapalı.  
Live `8000` değişmeyecek.

---

## 1. Kesin Kurallar

Phase 24R boyunca:

- live `8000` değişmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- gateway code farkı olmadan A/B koşulacak
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- large trace files git’e eklenmeyecek
- only summary artifacts committed
- TEB-04 raw PDF + SHA yoksa materialization yok

---

## 2. Phase 24R-A — Matched Runtime A/B Plan

## Amaç

BASE vs CBY koleksiyonlarını aynı runtime provenance ile karşılaştırmak.

## Collections

```text
BASE_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
CBY_COLLECTION  = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
```

## Required identical fields

```text
same git_sha
same gateway code
same scorer
same model
same DGX_MODEL
same prompt behavior
same retrieval/top-k
same embedding backend/model
same guardrails/verification state
same source catalog/supplement config
only MILVUS_COLLECTION differs
```

## Output

```text
reports/benchmark/phase_24R_A_matched_ab_plan.md
reports/benchmark/phase_24R_A_matched_ab_plan.json
```

## Commit

```text
Plan Phase 24R matched base-vs-CBY A/B run
```

Push required.

---

## 3. Phase 24R-B — Collection Load and Runtime Pair Verification

## Amaç

Aynı runtime config ile iki candidate çalıştırmak.

## Suggested ports

```text
BASE_API = http://127.0.0.1:8035/v1
CBY_API  = http://127.0.0.1:8036/v1
```

## Expected counts

```text
BASE entity_count = 349403
CBY entity_count = 349405
vector_dimension = 1024
```

## Output

```text
reports/benchmark/phase_24R_B_runtime_pair_verification.md
reports/benchmark/phase_24R_B_runtime_pair_provenance.json
```

## Acceptance

```text
both runtimes healthy
both /v1/models OK
only collection/entity_count/port differ
collections loaded
```

## Commit

```text
Verify Phase 24R matched runtime pair
```

Push required.

---

## 4. Phase 24R-C — Matched Targeted A/B Smoke

## QIDs

```text
CBY-06
CBY-05
MULGA-01
MULGA-05
TEB-06
KANUN-12
YON-04
TUZUK-04
CBG-01
CBKAR-08
UY-01
```

## Output

```text
reports/benchmark/phase_24R_C_matched_targeted_ab_smoke.md
reports/benchmark/phase_24R_C_matched_targeted_ab_smoke.csv
```

## Acceptance

```text
CBY-06 improves or stays improved on CBY collection
critical guards no regression
contract_valid all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
TUZUK-04 not active-current-law claim
```

## Commit

```text
Run Phase 24R matched targeted A/B smoke
```

Push required.

---

## 5. Phase 24R-D — Matched Full A/B Benchmark

Only run if Phase 24R-C passes.

Run full 100 benchmark on both BASE and CBY matched runtimes.

## Output

```text
reports/benchmark/phase_24R_D_base_full_summary.md
reports/benchmark/phase_24R_D_cby_full_summary.md
reports/benchmark/phase_24R_D_matched_ab_delta.md
reports/benchmark/phase_24R_D_matched_ab_delta.csv
reports/benchmark/phase_24R_D_green_lane_summary.md
```

## Acceptance for CBY merge consideration

```text
CBY raw_score_proxy >= BASE raw_score_proxy
CBY pass_proxy >= BASE pass_proxy
CBY wrong_family <= BASE wrong_family
CBY wrong_document <= BASE wrong_document
CBY hallucinated_identifier <= BASE hallucinated_identifier
CBY contract_valid = 100/100
CBY unsupported_confident_answer = 0
CBY answer_contract_invalid = 0
CBY source_key_v2_collision = 0
CBY binding_collision = 0
CBY green_lane = PASS
```

## Commit

```text
Run Phase 24R matched full A/B benchmark
```

Push required.

If not run:

```text
reports/benchmark/phase_24R_D_full_ab_not_run.md
```

---

## 6. Phase 24R-E — CBY Merge Decision

## Output

```text
reports/benchmark/phase_24R_E_cby_merge_decision.md
```

## Decision options

### Option A — CBY collection is merge-safe

```text
Open future controlled cutover/merge brief.
Do not auto-cutover.
```

### Option B — CBY collection improves targeted but hurts full

```text
Keep CBY collection diagnostic-only.
Do not merge.
```

### Option C — CBY result neutral

```text
Keep diagnostic-only unless product owner wants the CBY-06 improvement explicitly.
No cutover.
```

### Option D — A/B inconclusive

```text
Rerun once with same provenance.
```

## Commit

```text
Record Phase 24R CBY merge decision
```

Push required.

---

## 7. Phase 24R-F — TEB-04 Manual Raw Intake

## Amaç

Kullanıcı veya insan operatör tarafından browser’dan indirilecek GİB KDV GUT raw PDF’i için intake hazırlamak.

## Required human file

Expected path after manual save:

```text
reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf
```

## If file exists

Compute:

```text
file size
sha256
PDF text extraction status
I/C-2.1.3 visible?
tevkifat/iade visible?
```

## If file missing

Do not block Phase 24R A/B. Produce instruction file.

## Output

```text
reports/benchmark/phase_24R_F_teb04_manual_raw_intake.md
reports/benchmark/phase_24R_F_teb04_manual_raw_intake.csv
```

## If missing, also produce

```text
reports/benchmark/phase_24R_F_teb04_manual_download_instruction.md
```

## Commit

```text
Process Phase 24R TEB-04 manual raw intake
```

Push required.

---

## 8. Phase 24R-G — Trace Artifact Compliance Check

## Amaç

Phase24Q trace policy uygulanıyor mu doğrulamak.

## Output

```text
reports/benchmark/phase_24R_G_trace_artifact_compliance.md
```

## Checks

```text
no trace.jsonl > 25 MB staged
large traces ignored or local-only
summary artifacts committed
no git add -f of trace files
run dirs summarized
```

## Commit

```text
Check Phase 24R trace artifact compliance
```

Push required.

---

## 9. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24R_matched_ab_and_teb_intake_report.md
```

Must include:

1. commit SHA list
2. matched A/B plan
3. runtime pair verification
4. targeted A/B smoke
5. full A/B benchmark or not-run reason
6. CBY merge decision
7. TEB-04 manual raw intake status
8. trace artifact compliance
9. productization decision
10. internal eval decision
11. fine-tuning decision
12. final live 8000 state
13. next recommended phase

## Commit

```text
Report Phase 24R matched A/B and TEB intake outcome
```

Push required.

---

## 10. Stop Rules

Stop / do not proceed if:

```text
runtime provenance differs beyond collection
collection load fails
targeted A/B smoke regresses critical guards
contract invalid appears
unsupported confident appears
source_key_v2 collision appears
binding collision appears
live 8000 modified
large traces staged
```

---

## Final Note

This is not a remediation phase.

It is an evidence phase:
- prove whether CBY-06 span is merge-safe under matched provenance,
- prepare TEB-04 manual raw intake,
- enforce trace artifact policy.
