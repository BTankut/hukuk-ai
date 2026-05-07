# Hukuk-AI — Phase 24HT KANUN-08 Same-Family Source Identity Recovery Brief

## Karar

Phase 24HS focused non-live smoke ciddi iyileşme üretti.

Başarılı sonuçlar:

```text
TEB-04 = PASS
TUZUK-05 = PASS
YON-05 = PASS
MULGA-01 = PASS
MULGA-05 = PASS
TEB-06 = PASS
contract_valid = 13/13
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
```

Kalan ana residual:

```text
KANUN-08
```

Durum:

```text
KANUN-08 family düzeldi: YONETMELIK -> KANUN
Ancak aynı-family yanlış doküman seçiliyor:
selected = TÜRK BORÇLAR KANUNU / TBK m.255
score = 3.25 FAIL
```

Bu nedenle sıradaki faz:

```text
Phase 24HT — KANUN-08 Same-Family Source Identity Recovery
```

Amaç:

```text
Aynı legal family içinde generic law’un domain-specific expected source’u bastırmasını sistemik şekilde önlemek.
```

Bu faz live cutover değildir.  
Bu faz productization değildir.  
Bu faz internal eval değildir.  
Fine-tuning kapalıdır.  
Live `8000` değişmeyecek.

---

# 1. Kesin Kurallar

Phase 24HT boyunca:

- live `8000` değişmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- base/live collection overwrite yok
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- large trace commit yok
- sadece non-live candidate ve summary artifact

Allowed:

```text
same-family source identity audit
domain/source-title/issuer compatibility scoring design
feature-flagged non-live prototype
focused smoke
full benchmark only if focused smoke passes and owner/brief allows
```

---

# 2. Current Evidence

## Phase24HS focused result

```text
KANUN-08 = FAIL
selected family = KANUN
selected document = TÜRK BORÇLAR KANUNU
selected article = TBK m.255
failure = same-family wrong-document / domain mismatch
```

## Interpretation

```text
Family/domain gate fixed cross-family drift.
Remaining issue is same-family domain/source identity selection.
A generic or unrelated KANUN wins over a stronger domain-specific KANUN candidate.
```

---

# 3. Phase 24HT-A — KANUN-08 Same-Family Candidate Audit

## Amaç

KANUN-08 için candidate pool’da hangi KANUN kaynaklarının bulunduğunu, neden TBK m.255’in kazandığını, expected/domain-specific kaynağın nerede kaybolduğunu belirlemek.

## Output

```text
reports/benchmark/phase_24HT_A_kanun08_same_family_candidate_audit.md
reports/benchmark/phase_24HT_A_kanun08_same_family_candidate_audit.csv
```

## Required fields

```text
qid
query_text
selected_source_key
selected_source_title
selected_source_identifier
selected_article
candidate_rank
candidate_source_key
candidate_title
candidate_family
candidate_identifier
candidate_article
candidate_domain_terms
candidate_issuer
candidate_score_dense
candidate_score_lexical
candidate_score_metadata
candidate_score_domain
candidate_score_final
candidate_selected
candidate_should_win
why_tbk_won
expected_source_if_inferred
safe_systemic_fix_available
```

## Must answer

```text
TBK m.255 neden seçiliyor?
Expected/domain-specific KANUN candidate pool’da var mı?
Varsa hangi rank’te?
Yoksa metadata/dense retrieval sorunu mu?
Aynı-family domain compatibility scoring problemi mi?
```

## Commit

```text
Audit Phase 24HT KANUN-08 same-family candidates
```

Push required.

---

# 4. Phase 24HT-B — Same-Family Domain Compatibility Design

## Amaç

Aynı legal family içinde yanlış generic source selection’ı QID-specific olmadan azaltacak scoring/gating tasarımı üretmek.

## Output

```text
reports/benchmark/phase_24HT_B_same_family_domain_compatibility_design.md
```

## Design principles

```text
Same-family candidates are not automatically equivalent.
Domain/title/issuer/article signals must be compatible with query.
Generic law cannot win solely because family=KANUN.
Candidate source title/domain should match query legal domain.
Article-level semantic match cannot override document-level domain mismatch unless query explicitly asks that law/article.
Supporting law may appear, but primary law must match domain intent.
```

## Required design elements

```text
same_family_domain_score
document_domain_terms
query_domain_terms
issuer_or_regulator_signal
title_overlap_signal
article_semantic_signal
primary_vs_supporting_law_role
tie_break_rules
trace fields
feature flag name
```

## Suggested feature flag

```text
ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true
```

## Forbidden

```text
No KANUN-08 string.
No expected answer key.
No hardcoded law title unless sourced from query/source metadata generally.
No broad top-k increase.
```

## Commit

```text
Design Phase 24HT same-family domain compatibility
```

Push required.

---

# 5. Phase 24HT-C — Feature-Flagged Non-Live Prototype

Only run if B produces a safe systemic design.

## Implementation surface

Likely:

```text
api-gateway/src/rag/source_identity.py
api-gateway/src/rag/retrieval_orchestration.py
api-gateway/src/rag/runtime_trace.py
```

Avoid unless necessary:

```text
answer_synthesis.py
answer_slots.py
```

## Runtime

Non-live only, for example:

```text
http://127.0.0.1:8042/v1
```

## Output

```text
reports/benchmark/phase_24HT_C_non_live_prototype_report.md
```

## Tests

Add or update tests proving:

```text
same-family domain score does not use QID-specific logic
generic KANUN cannot beat domain-specific KANUN solely by article semantic match
supporting law does not overwrite primary law when domain mismatch exists
family/domain guard does not regress TEB/YON/MULGA critical cases
```

## Commit

```text
Prototype Phase 24HT same-family domain scoring
```

If unsafe:

```text
reports/benchmark/phase_24HT_C_prototype_not_run.md
```

Commit:

```text
Record Phase 24HT prototype not run
```

---

# 6. Phase 24HT-D — Focused Non-Live Smoke

Only run if C prototype exists.

## Target rows

```text
KANUN-08
```

## Regression / guard rows

```text
TEB-04
TUZUK-05
YON-05
MULGA-01
MULGA-05
TEB-06
CBY-06
KANUN-12
YON-04
TUZUK-04
CBG-01
CBKAR-08
```

## Acceptance

```text
contract_valid all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0

KANUN-08 selected document improves or score improves materially
TEB-04 remains PASS
TUZUK-05 remains PASS / no arbitrary concrete tüzük
YON-05 remains PASS
MULGA-01/MULGA-05/TEB-06 no regression
TUZUK-04 not active-current-law claim
```

## Output

```text
reports/benchmark/phase_24HT_D_focused_non_live_smoke_report.md
```

## Commit

```text
Run Phase 24HT focused non-live smoke
```

---

# 7. Optional Full Candidate Benchmark

Only run if focused smoke passes.

## Minimum comparison

Compare against latest safe focused candidate baseline and current trace-on base.

Candidate must satisfy:

```text
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
raw_score_proxy >= current trace-on base
pass_proxy >= current trace-on base
wrong_document <= current trace-on base
hallucinated_identifier <= current trace-on base
```

## Output

```text
reports/benchmark/phase_24HT_E_full_candidate_summary.md
reports/benchmark/phase_24HT_E_delta_vs_phase24U_base.md
reports/benchmark/phase_24HT_E_green_lane_summary.md
```

## Commit

```text
Run Phase 24HT full candidate benchmark
```

If not run:

```text
reports/benchmark/phase_24HT_E_full_candidate_not_run.md
```

---

# 8. Phase 24HT-F — Recovery Decision

## Output

```text
reports/benchmark/phase_24HT_F_recovery_decision.md
```

## Decision options

### Option A — KANUN-08 recovered safely

```text
Open controlled full-candidate validation / integration brief.
No live cutover yet.
```

### Option B — Same-family scoring improves but full insufficient

```text
Keep diagnostic candidate.
Continue component recovery.
```

### Option C — Same-family scoring not sufficient

```text
Open document-level retrieval/candidate recall audit.
No runtime integration.
```

### Option D — Needs scorer/rubric review

```text
No runtime change.
Prepare scorer/legal review packet.
```

## Commit

```text
Record Phase 24HT recovery decision
```

---

# 9. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24HT_same_family_source_identity_report.md
```

Must include:

1. commit SHA list
2. KANUN-08 candidate audit
3. same-family domain compatibility design
4. prototype run/not-run
5. focused smoke result
6. full candidate result if run
7. recovery decision
8. productization decision
9. internal eval decision
10. fine-tuning decision
11. final live 8000 state
12. next recommended phase

## Commit

```text
Report Phase 24HT same-family source identity outcome
```

---

# 10. Stop Rules

Stop/revert prototype if:

```text
live 8000 would be modified
QID-specific logic required
benchmark answer key required
contract invalid appears
unsupported confident appears
source_key_v2 or binding collision appears
TEB-04/TUZUK-05/YON-05 regress
MULGA-01/MULGA-05/TEB-06 regress
large traces staged
```

---

## Final Note

Phase24HS recovered the cross-family failures.

Phase24HT should focus only on same-family wrong-document selection for KANUN-08.
