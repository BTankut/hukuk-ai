# Hukuk-AI — Phase 24Q CBY-06 Regression Diff, TEB-04 Raw Acquisition, and Trace Policy Brief

## Karar

Phase 24P-R tamamlandı.

Net sonuç:

```text
CBY-06 targeted smoke = PASS
CBY-06 score = 8.58
Full shadow = FAIL
raw_score_proxy = 806.87 < 816
pass_proxy = 90 < 91
wrong_family = 8
hallucinated_identifier = 7
live_8000_modified = false
productization = closed
internal_eval = closed
fine_tuning = closed
```

TEB-04 için:

```text
official GİB URL known
download attempts = HTTP 400 application/json
safe_for_section_materialization = false
```

GitHub warning:

```text
trace.jsonl > 50 MB warning observed
push succeeded
trace size policy needed
```

Bu nedenle sıradaki faz:

```text
Phase 24Q — CBY-06 Regression Diff + TEB-04 Raw Acquisition Alternatives + Trace Artifact Policy
```

Bu faz implementation/merge fazı değildir.  
Önce neden CBY-only shadow full benchmark’ın baseline altına düştüğü netleştirilecek.

---

## 1. Kesin Kurallar

Phase 24Q boyunca:

- live `8000` değişmeyecek
- CBY-only collection live’a alınmayacak
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- TEB-04 raw source hash’lenmeden materialization yok
- large trace files repo’ya tekrar eklenmeyecek; önce policy yazılacak

---

## 2. Phase 24Q-A — CBY-Only Full Shadow Regression Audit

## Amaç

CBY-06 targeted PASS olmasına rağmen full shadow skorunun neden Phase23R-E baseline altına düştüğünü satır bazında açıklamak.

## Inputs

```text
Phase23R-E baseline full:
reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full

Phase24P-R full:
reports/benchmark/runs/phase_24P_R_full_shadow_20260504T1340Z
```

## Output

```text
reports/benchmark/phase_24Q_A_cby06_full_regression_audit.md
reports/benchmark/phase_24Q_A_cby06_full_regression_audit.csv
```

## Fields

```text
qid
phase23RE_score
phase24PR_score
score_delta
phase23RE_pass
phase24PR_pass
pass_to_fail
fail_to_pass
phase23RE_failure_classes
phase24PR_failure_classes
phase23RE_selected_source
phase24PR_selected_source
phase23RE_claimed_family
phase24PR_claimed_family
phase23RE_claimed_identifier
phase24PR_claimed_identifier
phase24PR_cby_new_span_in_evidence
root_cause
safe_action
```

## Root cause enum

```text
cby_span_interference
runtime_provenance_mismatch
selector_nondeterminism
existing_residual_shift
trace_or_scoring_artifact
no_meaningful_regression
unknown
```

## Acceptance

- Full 100-row delta table produced.
- Identify pass->fail and fail->pass rows.
- Determine whether CBY new spans caused any unrelated regression.
- No runtime behavior change.

## Commit

```text
Audit Phase 24Q-A CBY-only full regression
```

Push required.

---

## 3. Phase 24Q-B — CBY-06 Merge / No-Merge Decision

## Amaç

CBY-06 materialization tek başına korunmalı mı, diagnostic-only mi kalmalı kararını vermek.

## Output

```text
reports/benchmark/phase_24Q_B_cby06_merge_decision.md
```

## Decision options

### Option A — Keep diagnostic-only

```text
Do not merge CBY collection.
Reason: full benchmark regression outweighs targeted gain.
```

### Option B — Keep CBY span but require selector scoping

```text
CBY span is valid, but needs scope filter before full benchmark.
Open scoped selector diagnostic.
```

### Option C — Merge candidate if regression is artifact

```text
Only if Phase24P-R full regression is proven artifact and re-run passes minimum gate.
```

## Commit

```text
Record Phase 24Q-B CBY-06 merge decision
```

Push required.

---

## 4. Phase 24Q-C — TEB-04 Raw Acquisition Alternative Plan

## Amaç

GİB KDV Genel Uygulama Tebliği raw source capture için alternatif, reproducible ve hash’lenebilir yol belirlemek.

## Known blocker

```text
https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf
returns HTTP 400 application/json under tested methods.
```

## Output

```text
reports/benchmark/phase_24Q_C_teb04_raw_acquisition_alternative_plan.md
```

## Required investigation

Try/record:

```text
GİB page source canonical download link
browser-exported PDF save path if manual capture is needed
Resmî Gazete / mevzuat.gov.tr alternative if available
GİB HTML text endpoint if official
content-disposition headers
required cookies / anti-hotlink requirements if any
manual acquisition instruction for human operator
```

## Decision options

### Option A — Automated reproducible capture possible

```text
Produce raw PDF/text + SHA.
Open TEB-04 section materialization.
```

### Option B — Manual browser capture required

```text
Prepare human acquisition instruction.
No materialization until raw file + SHA is committed.
```

### Option C — Official raw capture impossible

```text
Keep TEB-04 scorer/materialization blocker.
Do not patch runtime.
```

## Commit

```text
Plan Phase 24Q-C TEB-04 raw acquisition alternatives
```

Push required.

---

## 5. Phase 24Q-D — Large Trace Artifact Policy

## Amaç

GitHub trace.jsonl >50 MB warning tekrarını önlemek.

## Output

```text
reports/benchmark/phase_24Q_D_trace_artifact_policy.md
```

## Policy must define

```text
max trace size committed to git
which trace files are gitignored
when to compress trace artifacts
when to keep summary only
whether Git LFS is required
how to store full traces locally
how to reference run dirs without committing large trace.jsonl
```

## Proposed defaults

```text
Do not commit trace.jsonl over 25 MB.
Commit summary CSV/MD/JSON only.
Compress large traces as .jsonl.zst or .jsonl.gz only if explicitly needed.
Add or update .gitignore for large run artifacts if safe.
Do not remove already committed history in this phase.
```

## Commit

```text
Define Phase 24Q trace artifact policy
```

Push required.

---

## 6. Phase 24Q-E — Final Decision Report

## Output

```text
reports/benchmark/phase_24Q_regression_and_acquisition_decision_report.md
```

## Must include

1. commit SHA list
2. CBY-only full regression audit
3. CBY merge/no-merge decision
4. TEB raw acquisition alternative plan
5. trace artifact policy
6. productization decision
7. internal eval decision
8. fine-tuning decision
9. final live 8000 state
10. next recommended phase

## Commit

```text
Report Phase 24Q regression and acquisition decision
```

Push required.

---

## 7. Stop Rules

Stop or avoid implementation if:

```text
live 8000 would be modified
base collection would be modified
QID-specific runtime branch is required
TEB raw source cannot be hashed
CBY full regression root cause is unknown
large trace policy cannot be applied safely
```

---

## Final Note

CBY-06 materialization is locally valid but not yet merge-safe.

TEB-04 is still blocked by reproducible official raw capture.

Do not run another remediation until:
1. CBY full regression cause is understood,
2. TEB raw acquisition path is decided,
3. trace artifact policy is in place.
