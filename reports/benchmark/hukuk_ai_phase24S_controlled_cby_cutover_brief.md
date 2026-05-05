# Hukuk-AI — Phase 24S Controlled CBY Collection Merge / Cutover Readiness Brief

## Karar

Phase 24R tamamlandı ve temiz matched A/B kanıt üretildi.

Repo kararına göre:

```text
selected_option = Option A — CBY collection is merge-safe
auto_cutover = false
live_8000_modified = false
```

Matched A/B sonucu:

```text
BASE_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
CBY_COLLECTION  = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06

BASE raw_score_proxy = 725.40
CBY raw_score_proxy  = 727.18
raw_score_delta = +1.78

BASE pass_proxy = 72
CBY pass_proxy  = 73
pass_delta = +1

changed_rows = CBY-06 only
CBY-06 = 6.80 FAIL -> 8.58 PASS
critical_guard_regression = false
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
```

Bu fazın amacı:

```text
CBY collection için kontrollü benchmark-only merge/cutover readiness hazırlamak ve gerekiyorsa uygulamak.
```

Bu productization değildir.  
Bu internal eval değildir.  
Bu public serving değildir.  
Fine-tuning kapalıdır.

TEB-04 bu fazın dışında kalır.

---

# 1. Kesin Kurallar

Phase 24S boyunca:

- productization açılmayacak
- internal eval açılmayacak
- public serving açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- TEB-04 materialization yok
- TEB-04 raw intake bu fazda yalnız not olarak kalacak
- trace policy korunacak; large trace commit yok

Live `8000` yalnız controlled benchmark-only scope ile ve rollback planı hazırsa değişebilir.

---

# 2. Phase 24S-A — CBY Cutover Candidate Manifest

## Amaç

CBY collection’ın live benchmark-only adayı olarak manifestini oluşturmak.

## Candidate

```text
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
entity_count = 349405
delta_vs_current_live = +2
expected improvement = CBY-06 only
```

## Current live baseline

```text
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
lane = phase22f_s7_full_shadow
scope = benchmark_only
```

## Output

```text
reports/benchmark/phase_24S_A_cby_cutover_candidate_manifest.md
reports/benchmark/phase_24S_A_cby_cutover_candidate_manifest.json
```

## Must include

```text
candidate_collection
candidate_entity_count
base_collection
base_entity_count
git_sha
model
DGX_MODEL
embedding_model
source_catalog_hash
source_supplement_hash
matched_ab_evidence
expected_changed_row
rollback_target
```

## Commit

```text
Create Phase 24S CBY cutover candidate manifest
```

Push required.

---

# 3. Phase 24S-B — Pre-Cutover Live Backup and Rollback Plan

## Amaç

Live `8000` değişmeden önce mevcut durumu backup almak.

## Output

```text
reports/benchmark/phase_24S_B_pre_cutover_live_backup.md
reports/benchmark/phase_24S_B_pre_cutover_live_backup.json
reports/benchmark/phase_24S_B_rollback_plan.md
```

## Required fields

```text
live_api_url
live_pid
live_lane
live_collection
live_entity_count
live_model
live_dgx_model
live_api_version
live_health
live_models_response
rollback_command
rollback_collection
rollback_entity_count
rollback_expected_health
```

## Commit

```text
Backup live 8000 before Phase 24S CBY cutover
```

Push required.

---

# 4. Phase 24S-C — Controlled Benchmark-Only CBY Cutover

## Amaç

Live `8000` benchmark-only runtime’ı CBY collection’a kontrollü geçirmek.

## Target

```text
MILVUS_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
entity_count = 349405
lane = phase22f_s7_full_shadow or phase24s_cby_benchmark_only
model = /models/merged_model_fabric_stage_20260321
scope = benchmark_only
```

## Output

```text
reports/benchmark/phase_24S_C_cutover_execution_log.md
reports/benchmark/phase_24S_C_post_cutover_runtime_provenance.json
```

## Acceptance

```text
8000 healthy
/v1/models OK
collection = candidate collection
entity_count = 349405
model correct
guardrails/verification state unchanged from benchmark-only scope
```

## Commit

```text
Execute Phase 24S controlled CBY benchmark cutover
```

Push required.

## Hard stop

Rollback immediately if:

```text
health fails
model mismatch
collection mismatch
entity count mismatch
runtime provenance missing
```

---

# 5. Phase 24S-D — Post-Cutover Targeted Smoke

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
reports/benchmark/phase_24S_D_post_cutover_targeted_smoke.md
```

## Acceptance

```text
CBY-06 PASS or score >= 8.5
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
Run Phase 24S post-cutover targeted smoke
```

Push required.

## Hard stop

Rollback if targeted smoke fails.

---

# 6. Phase 24S-E — Post-Cutover Full Benchmark

Only run if targeted smoke passes.

## Output

```text
reports/benchmark/phase_24S_E_post_cutover_full_summary.md
reports/benchmark/phase_24S_E_delta_vs_phase23RE.md
reports/benchmark/phase_24S_E_green_lane_summary.md
```

## Minimum gate

```text
raw_score_proxy >= 816.86
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

## Expected

```text
CBY-06 improves
No unrelated regression
```

## Commit

```text
Run Phase 24S post-cutover full benchmark
```

Push required.

## Hard stop

Rollback if minimum gate fails.

---

# 7. Phase 24S-F — Stability Rerun

Only run if Phase 24S-E passes.

## Output

```text
reports/benchmark/phase_24S_F_stability_summary.md
reports/benchmark/phase_24S_F_delta_vs_E.md
reports/benchmark/phase_24S_F_green_lane_summary.md
reports/benchmark/phase_24S_F_stability_decision.md
```

## Stability tolerance

```text
raw_score_delta >= -5
pass_delta >= -1
wrong_family <= E_wrong_family + 1
wrong_document <= E_wrong_document + 1
hallucinated_identifier <= E_hallucinated_identifier + 1
safety counters remain zero
contract_valid = 100/100
green_lane = PASS
```

## Commit

```text
Run Phase 24S stability benchmark
```

Push required.

## Hard stop

Rollback or mark unstable if fails.

---

# 8. Phase 24S-G — Residual Register Update

## Output

```text
reports/benchmark/phase_24S_G_residual_register_update.md
reports/benchmark/phase_24S_G_residual_register_update.csv
```

## Must record

```text
CBY-06 status after cutover
remaining residuals
TEB-04 raw blocker
TUZUK-05 stop-loss
productization blockers
internal eval blockers
```

## Commit

```text
Update Phase 24S residual register
```

Push required.

---

# 9. Phase 24S-H — TEB-04 Manual Raw Intake Reminder

Do not materialize TEB-04 in this phase.

But create/update reminder:

```text
reports/benchmark/phase_24S_H_teb04_manual_raw_intake_reminder.md
```

Must include expected file:

```text
reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf
```

and required metadata:

```text
source URL
file size
sha256
browser save method
text extraction status
I/C-2.1.3 visible
```

## Commit

```text
Record Phase 24S TEB-04 raw intake reminder
```

Push required.

---

# 10. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24S_controlled_cby_cutover_report.md
```

Must include:

1. commit SHA list
2. candidate manifest
3. pre-cutover backup
4. cutover execution
5. post-cutover targeted smoke
6. post-cutover full benchmark
7. stability result
8. rollback performed or not
9. residual register update
10. TEB-04 raw intake reminder
11. productization decision
12. internal eval decision
13. fine-tuning decision
14. final live 8000 state
15. next recommended phase

## Commit

```text
Report Phase 24S controlled CBY cutover outcome
```

Push required.

---

# 11. Decision Rules

## If all gates pass

```text
Keep live 8000 on CBY collection under benchmark_only scope.
Productization remains closed.
Internal eval remains closed unless separately approved.
Fine-tuning remains closed.
```

## If any hard gate fails

```text
Rollback live 8000 to p0_backfill base collection.
Productization remains closed.
Internal eval remains closed.
Fine-tuning remains closed.
```

Rollback target:

```text
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
lane = phase22f_s7_full_shadow
```

---

## Final Note

CBY collection is merge-safe by matched evidence, but this still requires controlled benchmark-only cutover validation.

Do not treat this as productization.
