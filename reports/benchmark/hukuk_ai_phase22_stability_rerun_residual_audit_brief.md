# Hukuk-AI — Phase 22 Stability Rerun + Residual Backlog Audit Brief

## Karar

Phase 21 **kabul edilmiştir**.

Phase 21F full benchmark güçlü geçti:

- `raw_score_proxy = 800.55`
- `pass_proxy = 89/100`
- `wrong_family = 6`
- `wrong_document = 5`
- `hallucinated_identifier = 5`
- `unsupported_confident_answer_count = 0`
- `unsupported_confident_claim = 0`
- `answer_contract_invalid_count = 0`
- `contract_valid = 100/100`
- `green_lane = PASS`
- `source_key_v2_collision_detected_count = 0`
- `binding_source_key_collision_detected_count = 0`

Phase 20F’ye göre:

- raw score yaklaşık `+44.95`
- pass count `+10`
- source/document/hallucinated identifier metrikleri belirgin iyileşti
- hard safety gates tamamen temiz kaldı

Bu, Phase 21’in güçlü kabulüdür.

Ancak:

- productization hâlâ kapalı
- fine-tuning hâlâ kapalı
- sıradaki iş yeni patch değil
- sıradaki iş **Phase 22 Stability Rerun + Residual Backlog Audit**

---

## 1. Neden Phase 22?

Phase 21F tek full run olarak çok iyi. Fakat productization veya fine-tuning konuşmadan önce aynı runtime ve aynı collection ile ikinci tam koşunun benzer sonucu verdiği görülmeli.

Ayrıca residual blocker backlog hâlâ var:

- total source/span blockers: `11`
- bazıları PASS satır olsa da source/span veya canonical evidence riski taşıyor
- bazıları FAIL ve Phase 22 residual audit gerektiriyor

Bu yüzden Phase 22’nin amacı kaliteyi artırmak değil; **stabiliteyi doğrulamak ve kalan riskleri sınıflamak**.

---

# 2. Phase 22A — Stability Full Rerun

## Amaç

Phase 21F sonucunun tekrarlanabilir olup olmadığını görmek.

## Koşulacak runtime

Aynı runtime kullanılmalı:

```text
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024
MILVUS_ENTITY_COUNT = 349191
VECTOR_DIMENSION = 1024
EMBEDDING_BACKEND = remote
EMBEDDING_MODEL = intfloat/multilingual-e5-large-instruct
GUARDRAILS_ENABLED = false
PRESIDIO_ENABLED = false
```

## Komutlar

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8000/v1 \
  --model hukuk-ai-poc \
  --out-dir reports/benchmark/runs/<timestamp>_phase22A_stability_full \
  --timeout 420 \
  --retries 0 \
  --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/<timestamp>_phase22A_stability_full/candidate_answers.csv \
  --out-dir reports/benchmark/runs/<timestamp>_phase22A_stability_full

GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/<timestamp>_phase22A_stability_full \
  bash scripts/benchmark/run_green_lane.sh \
  --run-dir reports/benchmark/runs/<timestamp>_phase22A_stability_full
```

## Stability Gate

Phase 22A, Phase 21F’ye göre şu toleransları sağlamalı:

| Metric | Phase 21F | Phase 22A Accept |
|---|---:|---:|
| raw_score_proxy | `800.55` | `>= 790` |
| pass_proxy | `89/100` | `>= 87/100` |
| wrong_family | `6` | `<= 8` |
| wrong_document | `5` | `<= 7` |
| hallucinated_identifier | `5` | `<= 7` |
| unsupported_confident_claim | `0` | `<= 2` |
| contract_valid | `100/100` | `100/100` |
| green_lane | `PASS` | `PASS` |
| source_key_v2_collision | `0` | `0` |
| binding_source_key_collision | `0` | `0` |

## Family Stability Gate

| Family | Phase 21F expected floor |
|---|---:|
| CB_GENELGE | `4/4` |
| CB_KARAR | `>= 7/8` |
| CB_KARARNAME | `6/6` |
| KANUN | `>= 19/21` |
| KHK | `6/6` |
| KKY | `>= 9/11` |
| MULGA | `>= 4/5` |
| TEBLIGLER | `>= 6/8` |
| UY | `>= 9/10` |
| YONETMELIK | `>= 7/10` |

## Commit

### Commit 1

```text
Run Phase 22A stability full benchmark
```

İçerik:

- full benchmark artifacts
- green lane artifacts
- stability comparison vs Phase 21F
- no runtime code changes

Push zorunlu.

---

# 3. Phase 22B — Residual Source/Span Blocker Audit

## Amaç

Phase 21F backlog’daki 11 residual blocker satırı root cause ve aksiyon türüne göre sınıflamak.

## Girdi

```text
reports/benchmark/phase_21F_source_span_blocker_backlog.md
```

## Backlog rows

```text
CBG-02
CBKAR-05
CBY-01
CBY-04
KANUN-12
KKY-01
KKY-03
MULGA-01
TEB-06
TUZUK-05
YON-04
```

## Üretilecek raporlar

```text
reports/benchmark/phase_22B_residual_backlog_audit.md
reports/benchmark/phase_22B_residual_backlog_audit.csv
```

## Her satır için alanlar

```text
qid
family
score
pass_fail
blocker_type
failure_classes
selected_document
selected_span
selected_article
expected_document_if_available
expected_family
claimed_family
wrong_family
wrong_document
wrong_article
hallucinated_identifier
insufficient_canonical_span_evidence
missing_gold_document_signal
metadata_lookup_hit
source_key_v2
binding_source_key
candidate_completeness_score
body_text_available
root_cause
safe_action
priority
```

## Root cause enum

```text
source_identity
document_identity
article_span_selection
span_materialization
corpus_materialization
family_boundary
private_rubric_auto_fail
scorer_proxy_mismatch
acceptable_residual_risk
unknown
```

## Safe action enum

```text
fix_now_generalizable
defer_needs_corpus
defer_needs_manual_legal_review
defer_private_rubric_mismatch
watch_only_pass_row
do_not_fix_qid_specific
```

## Priority enum

```text
P0_blocks_productization
P1_high_value_next_iteration
P2_watchlist
P3_acceptable_residual
```

## Special handling

### PASS but flagged rows

Some backlog rows may be PASS but flagged. These should not automatically trigger fixes:

- `CBG-02`
- `CBKAR-05`
- `CBY-01`

Classify whether they are:

```text
watch_only_pass_row
acceptable_residual_risk
or real productization blocker
```

### FAIL rows

Falling residuals require stricter analysis:

- `CBY-04`
- `KANUN-12`
- `KKY-01`
- `KKY-03`
- `MULGA-01`
- `TEB-06`
- `TUZUK-05`
- `YON-04`

Do not patch them yet unless the audit shows a clear, generalizable, low-risk fix.

## Commit

### Commit 2

```text
Audit Phase 22 residual source/span backlog
```

İçerik:

- residual backlog audit report
- CSV
- recommended next action
- no runtime code changes unless separately authorized

Push zorunlu.

---

# 4. Phase 22C — Decision Gate

## Amaç

Phase 22A stability rerun ve Phase 22B residual audit sonrası bir sonraki fazı belirlemek.

## Karar seçenekleri

### Seçenek A — Stability passed, residuals manageable

Şartlar:

- Phase 22A full run stable
- residual blockers sınıflandı
- P0 blocker yok veya çok sınırlı
- hard safety gates temiz

Karar:

```text
Phase 22 accepted
Open Phase 23 Productization Readiness Audit
Fine-tuning still closed
```

### Seçenek B — Stability passed, but residual source/span blockers remain meaningful

Karar:

```text
Open Phase 22D residual targeted remediation
No productization
No fine-tuning
```

### Seçenek C — Stability failed

Karar:

```text
Open Phase 22R stability regression investigation
No new feature work
No productization
No fine-tuning
```

---

# 5. Productization Readiness Criteria

Productization ancak Phase 22 sonrası tartışılabilir.

Minimum koşullar:

```text
two stable full benchmark runs
raw_score_proxy >= 790
pass_proxy >= 87
unsupported_confident_claim <= 2
contract_valid = 100/100
green_lane = PASS
source_key_v2_collision = 0
binding_collision = 0
CB_GENELGE = 4/4
UY >= 9/10
MULGA >= 4/5
TEBLIGLER >= 6/8
YONETMELIK >= 7/10
CB_KARAR >= 7/8
residual P0 blockers = 0
```

Even if all pass, productization should start as limited pilot / internal evaluation, not public release.

---

# 6. Fine-Tuning Gate

Fine-tuning remains closed.

Do not open until:

```text
productization-readiness audit completed
residual source/span blockers understood
two or more stable full runs
training data source separated from private benchmark
no benchmark answer key contamination
hard-negative source/document sets prepared
```

If any training is considered later, prefer this order:

1. source/document reranker training
2. span selector training
3. slot extractor calibration
4. answer-style fine-tuning last

---

# 7. Required Final Report

Produce:

```text
reports/benchmark/phase_22_stability_and_residual_audit_report.md
```

Report content:

1. Phase 22A full benchmark metrics
2. delta vs Phase 21F
3. green lane status
4. family-level stability table
5. residual backlog audit table
6. P0/P1/P2/P3 counts
7. recommendation:
   - Phase 23 productization readiness audit
   - Phase 22D residual remediation
   - Phase 22R stability regression investigation
8. productization gate decision
9. fine-tuning gate decision

---

## Final Note

Phase 21F is the strongest result so far.  
Do not immediately start more patching.

First prove stability with a second full run, then classify residual blockers.  
Only after that decide whether to move toward productization readiness or a narrow residual remediation phase.
