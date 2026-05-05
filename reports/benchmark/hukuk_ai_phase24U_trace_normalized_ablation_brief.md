# Hukuk-AI — Phase 24U Trace-Normalized Matched A/B and Source Supplement Drift Isolation Brief

## Karar

Phase 24T tamamlandı ve ana kök neden ayrıştırıldı.

Büyük çöküş:

```text
Phase23R-E = 816.86 / 91
Phase24R BASE trace-off = 725.40 / 72
```

Birincil neden:

```text
Phase24R/S full runs include_trace=false çalıştırılmış.
Trace-derived selected source/document fields yok.
Bu yüzden Phase24R/S full runs Phase23R-E ile score-equivalent değil.
```

Trace-on current reproduction:

```text
Phase24T-D current trace-on = 805.09 / 89
```

Yani trace normalization çoğu kaybı geri aldı:

```text
+79.69 raw
+17 pass
```

Ancak Phase23R-E hâlâ tam üretilmedi:

```text
remaining_gap_vs_Phase23R-E = -11.77 raw / -2 pass
```

Dar şüpheli alan:

```text
api-gateway/src/rag/source_supplements.py
source_supplement_hash changed
commit: ddcadd2 Execute Phase 24O shadow residual remediation
new default behavior: ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=true dynamic supplements
```

Sıradaki faz:

```text
Phase24U — Trace-Normalized Matched A/B and Source Supplement Drift Isolation
```

Bu faz diagnostic/ablation fazıdır.  
Live `8000` değişmeyecek.  
Productization/internal eval/fine-tuning kapalı kalacak.

---

# 1. Kesin Kurallar

Phase 24U boyunca:

- live `8000` değiştirilmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- prompt/model/top-k değişmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- trace-off full runs productization evidence olarak kullanılmayacak
- large trace files git’e commitlenmeyecek
- summary artifacts commitlenecek

---

# 2. Phase 24U-A — Trace-Normalized Matched BASE/CBY A/B Plan

## Amaç

Phase24R/S full runlarını yeniden üretirken `include_trace=True` ile gerçek score-equivalent A/B oluşturmak.

## Collections

```text
BASE_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
CBY_COLLECTION  = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
```

## Runtime requirements

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
include_trace = true
only MILVUS_COLLECTION differs
```

## Output

```text
reports/benchmark/phase_24U_A_trace_normalized_ab_plan.md
reports/benchmark/phase_24U_A_trace_normalized_ab_plan.json
```

## Commit

```text
Plan Phase 24U trace-normalized matched A/B
```

Push required.

---

# 3. Phase 24U-B — Run Trace-Normalized BASE Full Benchmark

## Amaç

Current code + BASE collection + include_trace=true ile baseline’ı ölçmek.

## Runtime

Use non-live candidate if possible:

```text
BASE_API = http://127.0.0.1:8037/v1
COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
include_trace = true
```

## Output

```text
reports/benchmark/phase_24U_B_base_trace_on_full_summary.md
reports/benchmark/phase_24U_B_base_trace_on_green_lane_summary.md
```

## Expected comparison

```text
Phase23R-E = 816.86 / 91
Phase24T-D current trace-on = 805.09 / 89
```

## Commit

```text
Run Phase 24U BASE trace-on full benchmark
```

Push required.

---

# 4. Phase 24U-C — Run Trace-Normalized CBY Full Benchmark

Only run if Phase 24U-B completes cleanly.

## Runtime

```text
CBY_API = http://127.0.0.1:8038/v1
COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
include_trace = true
```

## Output

```text
reports/benchmark/phase_24U_C_cby_trace_on_full_summary.md
reports/benchmark/phase_24U_C_cby_vs_base_trace_on_delta.md
reports/benchmark/phase_24U_C_cby_trace_on_green_lane_summary.md
```

## Acceptance for CBY consideration

```text
CBY raw_score_proxy >= BASE raw_score_proxy
CBY pass_proxy >= BASE pass_proxy
CBY wrong_family <= BASE wrong_family
CBY wrong_document <= BASE wrong_document
CBY hallucinated_identifier <= BASE hallucinated_identifier
CBY safety counters all zero
green_lane = PASS
```

## Commit

```text
Run Phase 24U CBY trace-on full benchmark
```

Push required.

---

# 5. Phase 24U-D — Source Supplement Ablation

## Amaç

Kalan 805.09/89 vs 816.86/91 farkının Phase24N dynamic supplements kaynaklı olup olmadığını izole etmek.

## Ablation

Run BASE collection with:

```text
ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=false
include_trace=true
```

Do not change live 8000.

Use non-live candidate:

```text
ABLATION_API = http://127.0.0.1:8039/v1
COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## Output

```text
reports/benchmark/phase_24U_D_source_supplement_ablation_summary.md
reports/benchmark/phase_24U_D_ablation_vs_current_trace_on_delta.md
reports/benchmark/phase_24U_D_ablation_green_lane_summary.md
```

## Decision

### If ablation restores Phase23R-E level

```text
source supplement drift confirmed.
Open Phase24V source supplement gating redesign.
```

### If ablation does not restore

```text
source supplement drift not sufficient.
Open commit-level code regression audit.
```

## Commit

```text
Run Phase 24U source supplement ablation
```

Push required.

---

# 6. Phase 24U-E — Drift Row Attribution

## Amaç

Phase23R-E, current trace-on BASE, and source-supplement ablation arasındaki farkları row bazında sınıflamak.

## Output

```text
reports/benchmark/phase_24U_E_drift_row_attribution.md
reports/benchmark/phase_24U_E_drift_row_attribution.csv
```

## Rows to focus

At least:

```text
MULGA-04
KANUN-08
KANUN-02
YON-05
YON-08
```

Plus any pass/fail changes.

## Fields

```text
qid
phase23RE_score
current_trace_on_score
ablation_score
score_delta_current_vs_phase23
score_delta_ablation_vs_phase23
phase23RE_selected_source
current_selected_source
ablation_selected_source
phase23RE_failure_classes
current_failure_classes
ablation_failure_classes
source_supplement_effect
suspected_root_cause
safe_next_action
```

## source_supplement_effect enum

```text
fixed_by_ablation
worsened_by_ablation
unchanged
mixed
unknown
```

## Commit

```text
Attribute Phase 24U source supplement drift rows
```

Push required.

---

# 7. Phase 24U-F — Decision Report

## Output

```text
reports/benchmark/phase_24U_trace_normalized_ablation_decision.md
```

## Decision options

### Option A — Source supplement drift confirmed

```text
Open Phase24V source supplement gating redesign.
Do not cut over CBY yet.
```

### Option B — Current code reproduces Phase23R-E

```text
Open Phase24S2 controlled CBY cutover with trace-on verified evidence.
```

### Option C — CBY trace-on is clean but BASE still drifted

```text
First fix BASE drift before CBY merge.
```

### Option D — Code regression not supplement-related

```text
Open commit-level regression audit between Phase23R-E and current HEAD.
```

## Commit

```text
Record Phase 24U trace-normalized ablation decision
```

Push required.

---

# 8. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24U_trace_normalized_ablation_report.md
```

Must include:

1. commit SHA list
2. trace-normalized A/B plan
3. BASE trace-on full result
4. CBY trace-on full result
5. source supplement ablation result
6. drift row attribution
7. decision
8. productization decision
9. internal eval decision
10. fine-tuning decision
11. final live 8000 state
12. next recommended phase

## Commit

```text
Report Phase 24U trace-normalized ablation outcome
```

Push required.

---

# 9. Stop Rules

Stop if:

```text
live 8000 would be modified
include_trace cannot be enabled
runtime provenance differs beyond intended collection/env flag
contract invalid appears
unsupported confident appears
source_key_v2 collision appears
binding collision appears
large trace files are staged
```

---

## Final Note

Do not patch logic in Phase24U.

First establish:
1. trace-on BASE current score,
2. trace-on CBY matched score,
3. whether source_supplements.py dynamic supplements explain the remaining Phase23R-E gap.
