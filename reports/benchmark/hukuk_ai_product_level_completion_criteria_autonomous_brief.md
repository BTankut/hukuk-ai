# Hukuk-AI — Product-Level Completion Criteria and Autonomous Execution Targets

## Amaç

Bu belge, Hukuk-AI uygulamasının **benchmark-only teknik başarıdan product seviyesine** geçebilmesi için gereken şartları tanımlar.

Kod asistanı bu belgeyi şu amaçla kullanmalıdır:

1. Product seviyesine çıkış için hangi teknik, hukuki ve operasyonel gate’lerin gerektiğini bilmek.
2. Hangi işlerin otonom yapılabileceğini, hangi işlerde durup raporlaması gerektiğini ayırmak.
3. Productization, internal eval, serving candidate ve public serving kavramlarını karıştırmamak.
4. Fine-tuning’i yanlış zamanda açmamak.
5. Canlı sistemi riske atmadan güvenli ilerlemek.

---

# 1. Mevcut Durum

Şu anki sistem durumu:

```text
Live 8000 = benchmark-only runtime
lane = phase22f_s7_full_shadow
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
guardrails = disabled
verification = disabled
presidio/privacy = disabled
audit logging = disabled
productization = closed
internal eval = closed
fine-tuning = closed
```

Bilinen benchmark-only başarı:

```text
raw_score_proxy = 816.86
pass_proxy = 91/100
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

Bu başarı **product-ready anlamına gelmez**.

---

# 2. Product-Level Completion Tanımı

Product seviyede tamamlanmış sayılmak için sistem şu seviyeye gelmelidir:

```text
Kısıtlı ve izlenebilir internal eval yapılabilir.
Serving-candidate ortamı güvenli şekilde açılabilir.
Public/productization için ayrı risk onayı alınabilir.
Hukuki kaynak doğruluğu, veri gizliliği, loglama, rollback ve insan incelemesi mekanizmaları tanımlıdır.
```

Product-level completion, yalnızca benchmark skorunun yüksek olması değildir.

Aşağıdakilerin tamamı sağlanmalıdır:

```text
benchmark stability
residual risk closure
legal/source/scorer review closure
guardrails policy
verification policy
privacy/PII policy
audit logging
trace exposure control
manual review workflow
confidence/abstention policy
rollback runbook
internal-eval readiness
serving-candidate readiness
final productization decision
```

---

# 3. Kesin Ayrımlar

## 3.1 Benchmark-only

Şu anki kapsam budur.

Özellikleri:

```text
benchmark koşulabilir
private/internal teknik değerlendirme yapılabilir
guardrails disabled olabilir
verification disabled olabilir
public/user traffic yoktur
productization değildir
```

## 3.2 Internal Eval

Kapalıdır. Açılması için ayrıca gate gerekir.

Özellikleri:

```text
kısıtlı erişim
belirli test kullanıcıları
kontrollü query seti
trace erişimi sınırlı
manual review aktif
rollback planı hazır
```

## 3.3 Serving Candidate

Kapalıdır.

Özellikleri:

```text
gerçek kullanıcıya benzer kullanım olabilir
guardrails/verification/privacy/logging politikaları gerektirir
hala public product değildir
```

## 3.4 Productization / Public Serving

Kapalıdır.

Özellikleri:

```text
public veya production-benzeri trafik
yüksek hukuki ve operasyonel risk
residual acceptance ve legal sign-off gerekir
privacy/audit/guardrails zorunludur
```

## 3.5 Fine-Tuning

Kapalıdır.

Açılması için ayrı model-training gate gerekir.

Fine-tuning, source/corpus/retrieval/scorer sorunları çözülmeden açılmamalıdır.

---

# 4. Productization İçin Ana Gate’ler

## Gate A — Benchmark Stability Gate

Minimum şart:

```text
raw_score_proxy >= 816
pass_proxy >= 91/100
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

Stability şartı:

```text
iki ardışık full benchmark run
raw_score_delta >= -5
pass_delta >= -1
wrong_family artışı <= 1
wrong_document artışı <= 1
hallucinated_identifier artışı <= 1
safety counters = 0
```

Kural:

```text
Trace-off full runs productization evidence değildir.
include_trace=true veya scorer’ın ihtiyaç duyduğu tüm selected-source evidence alanları dolu olmalıdır.
```

---

## Gate B — Residual Risk Closure Gate

Şu residual rows kapanmalı veya resmen kabul edilmelidir:

```text
CBY-04
CBY-06
KANUN-12
KKY-01
KKY-03
TEB-04
TUZUK-04
TUZUK-05
YON-04
```

Her residual için şu karar alanları dolu olmalıdır:

```text
qid
current_status
root_cause
legal_review_status
source_acquisition_status
scorer_rubric_status
runtime_fix_status
accepted_for_internal_eval
accepted_for_serving_candidate
accepted_for_productization
owner
next_action
```

Productization için güvenli varsayılan:

```text
accepted_for_productization = no
```

Manuel kabul ancak açık gerekçe ve owner ile yapılabilir.

---

## Gate C — Legal / Scorer Review Gate

Aşağıdaki kararlar tamamlanmalıdır:

```text
CBY taxonomy/scorer expectations
KKY vs YONETMELIK taxonomy compatibility
TEB-04 KDV GUT scorer/materialization expectation
TUZUK-04 historical/current-law framing
TUZUK-05 source ambiguity decision
```

Required artifacts:

```text
reports/benchmark/legal_review_returns/filled_phase_24H_legal_scorer_review_return.csv
reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_checklist.csv
normalized legal/scorer decision report
```

Karar enumları:

```text
runtime_fix_allowed
runtime_fix_not_allowed
scorer_rubric_mismatch
legal_taxonomy_confirmed
manual_residual_accepted
needs_more_review
```

`needs_more_review` kalan satır productization blocker’dır.

---

## Gate D — Source / Corpus / Materialization Gate

Her product-critical kaynak için:

```text
official_url present
raw_file_path present
raw_file_sha256 present
parser_ready = yes
article/section boundary detectable
legal_reviewer_confirmation = confirmed
effective_state known
```

Source/corpus durumları:

```text
active
amended
repealed
historical
partially_repealed
unknown
```

`unknown`, `not_found`, `not_downloaded`, `missing`, `needs_more_review` productization blocker’dır.

Özel blocker:

```text
TEB-04: KDV GUT official raw PDF/text hashable şekilde yakalanmadan section materialization yapılamaz.
TUZUK-05: exact source identity bulunmadan runtime patch yapılamaz.
```

---

## Gate E — Source Identity / Selector Gate

Source identity pipeline product için şu garantileri vermelidir:

```text
primary source doğru seçiliyor
supporting source primary source’u overwrite etmiyor
family/domain compatibility korunuyor
canonical_source_key_v2 stable
binding_source_key stable
wrong document regression yok
hallucinated identifier düşük ve kontrollü
```

Minimum hedef:

```text
wrong_family <= 5 preferred, <= 6 maximum
wrong_document <= 4
hallucinated_identifier <= 4
runtime_source_key_collision = 0
binding_collision = 0
```

Source selection drift görüldüğünde:

```text
QID-specific patch yasak
family/domain compatibility systemic olmalı
supporting/primary source ayrımı korunmalı
```

---

## Gate F — Temporal / Current-Law Validity Gate

Hukuki cevaplarda tarihsel/yürürlük ayrımı güvenli olmalıdır.

Zorunlu kurallar:

```text
repealed/historical source active current law gibi sunulamaz
current-law question eski tüzükle tek başına cevaplanamaz
repeal/current-law basis varsa evidence bundle’da rol ayrımı yapılmalı
historical source, repeal instrument ve current-law basis ayrı claim role ile sunulmalı
```

Stop condition:

```text
repealed_as_active_count > 0
```

---

## Gate G — Guardrails Policy Gate

Product seviyede guardrails politikası tanımlanmalıdır.

Minimum policy:

```text
legal advice disclaimer
insufficient evidence mode
unsupported confident answer block
dangerous hallucinated citation block
confidence threshold
manual review trigger
source unavailable response
current-law uncertainty response
```

Artifact:

```text
reports/benchmark/productization/guardrails_policy.md
```

Guardrails kapalıysa productization açılamaz veya resmi waiver gerekir.

---

## Gate H — Verification Policy Gate

Legal RAG için claim-level verification gerekir.

Minimum verification:

```text
claim-to-evidence map
citation/source consistency check
effective_state check
source_family/source_identifier consistency check
unsupported claim detector
contract validity check
```

Artifact:

```text
reports/benchmark/productization/verification_policy.md
```

Verification kapalıysa public/product serving açılmamalıdır.

---

## Gate I — Privacy / Presidio / PII Gate

Product seviyede veri gizliliği politikası gerekir.

Minimum policy:

```text
PII detection
query logging minimization
trace redaction
raw user query retention policy
manual reviewer data access rules
data deletion process
```

Artifact:

```text
reports/benchmark/productization/privacy_pii_policy.md
```

Presidio veya eşdeğer privacy kontrolü kapalıysa productization açılamaz veya resmi waiver gerekir.

---

## Gate J — Audit Logging Gate

Product seviyede audit logging gerekir.

Minimum audit log:

```text
request_id
timestamp
model id
collection id
retrieved source keys
selected source keys
answer confidence
manual review flag
guardrail/verification result
error state
```

Trace dosyaları public log değildir.

Artifact:

```text
reports/benchmark/productization/audit_logging_policy.md
```

---

## Gate K — Trace Exposure / Artifact Policy Gate

Trace dosyaları kontrollü olmalıdır.

Kurallar:

```text
large trace.jsonl git’e commitlenmez
summary artifacts commitlenir
full trace local-only veya controlled storage
trace redaction yapılmadan external paylaşım yok
trace retention süresi tanımlı
```

Mevcut policy korunmalıdır:

```text
max_trace_size_committed_to_git <= 25 MB
large traces ignored/local-only
```

Artifact:

```text
reports/benchmark/productization/trace_exposure_policy.md
```

---

## Gate L — Manual Review Workflow Gate

Manual review gerektiren durumlar:

```text
low confidence
insufficient current-law evidence
repealed/current law ambiguity
source not found
scorer/legal taxonomy mismatch
high-impact legal answer
```

Artifact:

```text
reports/benchmark/productization/manual_review_workflow.md
```

Workflow şunları içermelidir:

```text
reviewer role
review queue
review SLA
decision enums
accept/reject/escalate rules
audit trail
```

---

## Gate M — Confidence / UX / Refusal Policy Gate

Cevap davranışı ürün seviyesinde tanımlanmalıdır.

Minimum policy:

```text
high confidence answer
qualified answer
insufficient evidence answer
manual review required answer
source unavailable answer
current-law uncertainty answer
```

Artifact:

```text
reports/benchmark/productization/confidence_ux_policy.md
```

---

## Gate N — Rollback / Incident Runbook Gate

Product seviyede rollback prosedürü gerekir.

Minimum runbook:

```text
current live config backup
candidate config
rollback command
health checks
post-rollback smoke
owner
incident severity
communication process
```

Artifact:

```text
reports/benchmark/productization/rollback_incident_runbook.md
```

Rollback doğrulanmadan serving candidate açılamaz.

---

# 5. Otonom Çalışma Programı

Kod asistanı aşağıdaki sırayla ilerlemelidir.

## Phase P1 — Product Readiness Inventory

Output:

```text
reports/benchmark/productization/product_readiness_inventory.md
reports/benchmark/productization/product_readiness_inventory.csv
```

Amaç:

```text
tüm gate’leri PASS/FAIL/PARTIAL olarak işaretle
eksik artifactleri listele
owner ve next_action belirt
```

Commit:

```text
Inventory product readiness gates
```

---

## Phase P2 — Residual Closure Matrix

Output:

```text
reports/benchmark/productization/residual_closure_matrix.md
reports/benchmark/productization/residual_closure_matrix.csv
```

Amaç:

```text
9 residual row için legal/source/scorer/runtime/productization durumunu tek matriste topla
```

Commit:

```text
Create residual closure matrix
```

---

## Phase P3 — Product Policy Artifacts

Hazırlanacak dosyalar:

```text
reports/benchmark/productization/guardrails_policy.md
reports/benchmark/productization/verification_policy.md
reports/benchmark/productization/privacy_pii_policy.md
reports/benchmark/productization/audit_logging_policy.md
reports/benchmark/productization/trace_exposure_policy.md
reports/benchmark/productization/manual_review_workflow.md
reports/benchmark/productization/confidence_ux_policy.md
reports/benchmark/productization/rollback_incident_runbook.md
```

Commit:

```text
Draft productization policy artifacts
```

Bu faz dokümantasyon/policy fazıdır. Runtime değiştirmez.

---

## Phase P4 — Internal Eval Readiness Recheck

Output:

```text
reports/benchmark/productization/internal_eval_readiness_recheck.md
```

Decision options:

```text
internal_eval_ready
limited_legal_review_eval_only
not_ready_residuals_open
not_ready_policy_controls_missing
```

Commit:

```text
Recheck internal eval readiness for product path
```

Internal eval yalnız explicit PASS ile açılabilir.

---

## Phase P5 — Serving Candidate Readiness Recheck

Output:

```text
reports/benchmark/productization/serving_candidate_readiness_recheck.md
```

Decision options:

```text
serving_candidate_ready_with_restrictions
not_ready_guardrails_missing
not_ready_verification_missing
not_ready_privacy_missing
not_ready_residuals_open
```

Commit:

```text
Recheck serving candidate readiness
```

Serving candidate explicit PASS olmadan açılmaz.

---

## Phase P6 — Final Productization Gate

Output:

```text
reports/benchmark/productization/final_productization_gate.md
```

Decision options:

```text
not_productization_ready
productization_ready_with_restrictions
requires_legal_signoff
requires_security_privacy_review
requires_residual_remediation
```

Commit:

```text
Record final productization gate decision
```

---

# 6. Otonom İzinler

Kod asistanı şu işleri otonom yapabilir:

```text
audit
matrix generation
policy drafting
readiness checklist
risk register
documentation
non-live diagnostic
non-live smoke if explicitly safe
```

Kod asistanı şu işleri onaysız yapamaz:

```text
live 8000 değiştirmek
internal eval açmak
serving candidate açmak
productization açmak
fine-tuning başlatmak
model değiştirmek
prompt/top-k değiştirmek
public endpoint açmak
```

---

# 7. Stop Rules

Derhal dur ve raporla:

```text
live 8000 değişikliği gerektiriyorsa
product/public/internal_eval scope açılacaksa
fine-tuning öneriliyorsa
legal/source residual needs_more_review kalıyorsa
privacy/audit/guardrails policy eksikse
rollback planı yoksa
source_key_v2_collision > 0
binding_collision > 0
unsupported_confident_answer > 0
answer_contract_invalid > 0
```

---

# 8. Product-Level “Done” Definition

Uygulama product seviyede tamamlandı denebilmesi için:

```text
Benchmark stability PASS
Residual closure matrix accepted
Internal eval gate PASS
Serving candidate gate PASS or explicitly waived
Guardrails policy PASS
Verification policy PASS
Privacy/PII policy PASS
Audit logging policy PASS
Trace exposure policy PASS
Manual review workflow PASS
Confidence/UX policy PASS
Rollback runbook PASS
Legal/scorer review closure PASS
Source/corpus materialization closure PASS
Final productization gate PASS or restricted PASS
Fine-tuning decision explicitly CLOSED or separately approved
```

Bunlardan biri eksikse:

```text
productization = not_ready
```

---

# 9. Mandatory Final Report

Kod asistanı sonunda mutlaka şu dosyayı üretmelidir:

```text
reports/benchmark/productization/product_level_completion_report.md
```

İçerik:

1. gate-by-gate status
2. benchmark status
3. residual closure status
4. policy artifact status
5. internal eval decision
6. serving candidate decision
7. productization decision
8. fine-tuning decision
9. remaining blockers
10. next required human decision
11. final live state

Commit:

```text
Report product-level completion readiness
```

Push required.

---

## Final Note

Product seviyeye geçiş, skor iyileştirme işi değildir.

Product seviyeye geçiş; hukuki güven, kaynak doğruluğu, denetlenebilirlik, gizlilik, rollback, insan incelemesi ve operasyonel güvenlik işidir.

Benchmark-only başarı korunmalı, fakat productization ancak tüm gate’ler kapandığında açılmalıdır.
