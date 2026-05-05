# Hukuk-AI — Phase 24T Systemic Full-Run Recovery Diagnostic Brief

## Karar

Phase 24S controlled CBY cutover başarısız oldu ve rollback doğru şekilde yapıldı.

Repo kanıtı:

```text
Phase24S-E full_gate = FAIL
raw_score_proxy = 727.18
pass_proxy = 73/100
wrong_family = 8
wrong_document = 21
hallucinated_identifier = 25
green_lane = FAIL
rollback_verified = PASS
live 8000 = phase22f_s7_full_shadow
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

Önemli bulgu:

```text
CBY-06 targeted PASS.
CBY collection matched A/B’de CBY-06 için faydalı.
Ama full-run score Phase23R-E baseline’dan çok uzak.
```

Bu, sadece CBY span interference gibi görünmüyor. Phase24R/24S full runs ile Phase23R-E full run arasında sistemik source/document identity veya canonical span recall farkı var.

Sıradaki faz:

```text
Phase 24T — Systemic Full-Run Recovery Diagnostic
```

Bu faz implementation fazı değildir.
Önce Phase23R-E baseline ile Phase24R/S full run farkı kök neden seviyesinde açıklanacak.

Productization kapalı.
Internal eval kapalı.
Fine-tuning kapalı.
Live `8000` değişmeyecek.

---

# 1. Kesin Kurallar

Phase 24T boyunca:

- live `8000` değiştirilmeyecek
- CBY collection tekrar live’a alınmayacak
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- prompt/model/top-k değiştirilmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- base/live collection overwrite yok
- full remediation yok
- yalnız diagnostic / matched evidence / design

---

# 2. Source of Truth Runs

## Good baseline

```text
Phase23R-E live full:
reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full
raw_score_proxy = 816.86
pass_proxy = 91
wrong_document = 4
hallucinated_identifier = 4
```

## Bad runs

```text
Phase24R matched BASE full:
raw_score_proxy = 725.40
pass_proxy = 72

Phase24R matched CBY full:
raw_score_proxy = 727.18
pass_proxy = 73

Phase24S live CBY full:
raw_score_proxy = 727.18
pass_proxy = 73
```

Key suspicion:

```text
Phase24R/S matched full runs may not be equivalent to Phase23R-E runtime/scorer/provenance despite apparent safety counters.
```

---

# 3. Phase 24T-A — Phase23R-E vs Phase24R/S Provenance Diff

## Amaç

Phase23R-E ile Phase24R/S full benchmark koşuları arasında runtime/scorer/config farkı var mı bulmak.

## Output

```text
reports/benchmark/phase_24T_A_full_run_provenance_diff.md
reports/benchmark/phase_24T_A_full_run_provenance_diff.json
```

## Compare fields

```text
api_url
lane
api_version
git_sha
model
DGX_MODEL
MILVUS_COLLECTION
entity_count
vector_dimension
embedding_backend
embedding_base_url
embedding_model
source_catalog_hash
source_supplement_hash
scorer_version
green_lane_script_version
guardrails
verification
presidio
feature_flags
runtime_env
run_command
timeout/retries/sleep
```

## Acceptance

- Identify all material differences.
- If git_sha/scorer/runtime command differs, mark as possible cause.
- No runtime behavior change.

## Commit

```text
Audit Phase 24T full-run provenance diff
```

Push required.

---

# 4. Phase 24T-B — 100-Row Score Delta Attribution

## Amaç

Phase23R-E ile Phase24R BASE full run arasında 100 satırlık düşüşü sınıflamak.

## Output

```text
reports/benchmark/phase_24T_B_score_delta_attribution.md
reports/benchmark/phase_24T_B_score_delta_attribution.csv
```

## Required fields

```text
qid
phase23RE_score
phase24R_base_score
score_delta
phase23RE_pass
phase24R_base_pass
pass_to_fail
fail_to_pass
phase23RE_selected_source
phase24R_selected_source
phase23RE_claimed_family
phase24R_claimed_family
phase23RE_claimed_identifier
phase24R_claimed_identifier
phase23RE_failure_classes
phase24R_failure_classes
delta_type
suspected_root_cause
```

## delta_type enum

```text
pass_to_fail
fail_to_pass
score_drop_no_pass_change
score_gain_no_pass_change
unchanged
```

## suspected_root_cause enum

```text
runtime_provenance_diff
scorer_or_green_lane_diff
source_identity_regression
document_selection_regression
identifier_surface_regression
evidence_bundle_empty_or_missing
trace_artifact_missing
collection_binding_mismatch
unknown
```

## Acceptance

- 100/100 rows compared.
- Top score-loss rows identified.
- New wrong_document/hallucinated_identifier rows listed.
- No runtime change.

## Commit

```text
Attribute Phase 24T full-run score delta
```

Push required.

---

# 5. Phase 24T-C — Critical Document Identity Regression Audit

## Amaç

Phase24R/S full runs’da wrong_document ve hallucinated_identifier patlamasının kaynağını bulmak.

## Focus

Rows that were good or acceptable in Phase23R-E but bad in Phase24R/S.

## Output

```text
reports/benchmark/phase_24T_C_document_identity_regression_audit.md
reports/benchmark/phase_24T_C_document_identity_regression_audit.csv
```

## Fields

```text
qid
phase23RE_selected_document
phase24R_selected_document
phase23RE_source_key
phase24R_source_key
phase23RE_binding_key
phase24R_binding_key
phase23RE_identifier
phase24R_identifier
phase23RE_evidence_present
phase24R_evidence_present
retrieval_topk_diff_available
selector_diff_available
regression_point
safe_recovery_action
```

## regression_point enum

```text
metadata_lookup
dense_retrieval
rerank
source_identity_selection
article_span_selection
answer_contract_surface
scorer_only
unknown
```

## Commit

```text
Audit Phase 24T document identity regressions
```

Push required.

---

# 6. Phase 24T-D — Reproduce Phase23R-E Baseline on Current Code

## Amaç

Mevcut code checkout ile Phase23R-E base collection tekrar aynı skoru veriyor mu kontrol etmek.

## Rules

- Use current live 8000 only if it is already on base collection and healthy.
- Do not change live 8000.
- If separate candidate needed, run non-live port.
- No prompt/model/top-k changes.

## Output

```text
reports/benchmark/phase_24T_D_phase23RE_baseline_reproduction.md
```

## Decision

### If current code reproduces 816.86 / 91

```text
Phase24R/S low score likely matched-run command/provenance artifact or candidate runtime issue.
```

### If current code reproduces low 725/72

```text
Current code/runtime drifted since Phase23R-E.
Open code regression audit.
```

### If cannot reproduce

```text
Record blocker and required provenance gap.
```

## Commit

```text
Reproduce Phase 23R-E baseline under current code
```

Push required.

---

# 7. Phase 24T-E — Recovery Design, No Implementation

## Amaç

Audit sonuçlarına göre dar recovery planı tasarlamak.

## Output

```text
reports/benchmark/phase_24T_E_recovery_design.md
```

## Design options

### Option A — Runtime/scorer provenance issue

```text
Normalize runner/scorer/runtime and rerun Phase24R/S matched A/B.
No code fix.
```

### Option B — Code regression since Phase23R-E

```text
Identify exact commits causing source/document identity regression.
Prepare revert/cherry-pick plan.
```

### Option C — Collection binding / candidate runtime issue

```text
Fix runtime binding/load/provenance setup.
No logic patch.
```

### Option D — Source identity logic regression

```text
Prepare systemic source/document identity fix.
No QID-specific branch.
```

### Option E — Stop CBY merge line

```text
Keep Phase23R-E baseline live.
Archive CBY span as diagnostic.
```

## Commit

```text
Design Phase 24T systemic recovery plan
```

Push required.

---

# 8. Phase 24T-F — Final Diagnostic Report

## Output

```text
reports/benchmark/phase_24T_systemic_full_run_recovery_report.md
```

Must include:

- commit SHA list
- provenance diff
- score delta attribution
- document identity regression audit
- Phase23R-E baseline reproduction result
- recovery design
- productization decision
- internal eval decision
- fine-tuning decision
- final live 8000 state
- next recommended phase

## Commit

```text
Report Phase 24T systemic recovery diagnostic
```

Push required.

---

# 9. Productization / Internal Eval / Fine-Tuning

All remain closed.

Reason:

```text
Phase24S full gate failed and rollback occurred.
Phase24R/S full scores do not match Phase23R-E stability.
Root cause must be diagnosed before any further merge/cutover.
```

---

## Final Note

Do not attempt another fix until Phase23R-E vs Phase24R/S full-run discrepancy is explained.

This is a systemic recovery diagnostic, not a residual improvement phase.
