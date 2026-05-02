# Phase 22F-S4-R Remediation Design

Date: 2026-05-02

## Scope

This is a design-only report based on:

- `reports/benchmark/phase_22F_S4_R_family_identifier_residual_audit.md`
- `reports/benchmark/phase_22F_S4_R_delta_vs_baselines.md`

No runtime behavior was changed in S4-R.

## Design Decision

Recommended option: `Open Phase 22F-S5 deterministic fix`.

The S5 scope must stay narrow. It should address only generalizable family/identifier residual patterns proven by the audit. It must not introduce QID-specific branches, prompt/model changes, source acquisition, corpus materialization, retrieval top-k changes, productization, fine-tuning, or live `8000` cutover.

## Candidate Fix 1: Active Selected Evidence Historical-Surface Clamp

Target rows:

```text
TUZUK-04
```

Observed issue:

```text
selected_source_family = tuzuk
selected_effective_state = active
split_temporal_policy_bucket = legacy_mulga_historical_surface_without_relation_chain
claimed_family = MULGA
```

This violates the intended S4 Rule 3 boundary because legacy MULGA historical surface should require historical/repealed selected evidence or a safe MULGA-like selected source. Active selected non-MULGA evidence should not be surfaced as MULGA solely because the question contains historical-risk language.

General deterministic design:

```text
If relation_chain_expansion_applied is false
AND selected source family is active non-MULGA
AND selected effective_state is active/current/unknown_non_repealed
THEN historical_claim_surface_allowed must remain false
AND claim_family_rewrite_allowed must remain false
unless selected evidence itself is MULGA/repealed/historical.
```

Expected effect:

- Reduce `wrong_family` by 1.
- Reduce `hallucinated_identifier` by 1.
- Preserve S4 targeted MULGA rows because their selected evidence is MULGA/repealed.

Risk:

- Must rerun S4-C and S4-D to prove MULGA historical surface remains intact.

Safe action:

```text
fix_now_generalizable
```

## Candidate Fix 2: Historical Article Surface Guard

Target rows:

```text
MULGA-05
```

Observed issue:

```text
Phase22A: PASS, document-level/article-344 surface
S4: FAIL, selected GEC1 surface, wrong_article
```

General deterministic design:

```text
Do not elevate a repeal/temporary/legacy article identifier as the substantive claimed article
when the query does not explicitly ask that article
and selector_article_lock_type is none/title_only.
```

The answer may still explain temporal invalidity, but the claimed article surface must not become a brittle generic repeal or temporary article unless support is exact.

Expected effect:

- Recover `MULGA-05` or reduce wrong-article risk.
- Does not directly affect wrong_family target, but removes a new pass-to-fail regression.

Risk:

- Needs targeted MULGA smoke because over-suppressing article claims can reduce grounding.

Safe action:

```text
fix_now_generalizable
```

## Candidate Fix 3: UY vs YONETMELIK Family Boundary Guard

Target rows:

```text
UY-01
```

Observed issue:

```text
Phase22A: UY / 18757 m.4, PASS
S4: YONETMELIK / 12420 m.4, FAIL
collision_resolution_reason = central_higher_education_regulation_prefers_yonetmelik
```

General deterministic design:

```text
If query family prior is UY
AND collision pair is uy|yonetmelik
AND query contains university-specific undergraduate/course-registration terms
THEN do not override a viable UY candidate with a generic YONETMELIK candidate
unless metadata identity is stronger for YONETMELIK by exact title/issuer evidence.
```

This is not a QID-specific rule; it is a family taxonomy boundary rule for university implementing regulations.

Expected effect:

- Potentially reduce `wrong_family` by 1.
- Potentially reduce `hallucinated_identifier` by 1.
- Combined with Candidate Fix 1, this can restore the full gate targets:

```text
wrong_family: 8 -> 6
hallucinated_identifier: 6 -> 4 or 5
```

Risk:

- Needs a focused UY/YON regression smoke because some central higher-education questions correctly prefer YONETMELIK.

Safe action:

```text
fix_now_generalizable, conditional on trace proof
```

## Candidate Fix 4: TEB Domain Mismatch Guard

Target rows:

```text
TEB-04
```

Observed issue:

```text
Question domain: KDV tevkifat/iade consolidated main communique
Selected document: Elektronik Tebligat Sistemi Genel Tebliği
```

General deterministic design:

```text
For TEBLIGLER document selection, high-signal tax terms such as KDV, tevkifat, iade,
and konsolide ana tebliğ should reject unrelated electronic-notification communique
surfaces unless the title/body also carries the same tax-domain anchors.
```

Risk:

- This touches document identity selection and can become a broad retrieval/rerank change.
- It should not be implemented until a trace-only candidate-pool audit proves the correct KDV tebliğ candidate is already present.

Safe action:

```text
fix_now_generalizable only after trace proof; otherwise defer_corpus_backfill
```

## Do Not Patch in S5 Without Legal/Scorer Review

Rows:

```text
CBY-04
KKY-01
KANUN-12
KKY-03
TUZUK-05
YON-04
CBY-06
```

Reasons:

- `CBY-04`: CB_YONETMELIK vs CB_KARARNAME taxonomy boundary; selected article is exact.
- `KKY-01`: selected banking IT regulation appears substantively right, but scorer expects KKY while source title/family surfaces as YONETMELIK.
- `KANUN-12`, `KKY-03`, `YON-04`: wrong-document source identity failures; safe fix likely requires candidate-pool/corpus/legal review, not blind runtime patching.
- `TUZUK-05`: hierarchy question with title-only/wrong-document behavior; likely scorer/rubric or source identity review.
- `CBY-06`: pre-existing partial-grounding/update residual, not a family/identifier blocker.

## S5 Acceptance Proposal

S5 should run in this order:

1. Unit tests for active selected non-MULGA clamp, historical article surface guard, and UY/YON family-boundary behavior.
2. Targeted residual smoke on:

```text
CBY-04 CBY-06 KANUN-12 KKY-01 KKY-03 MULGA-05 TEB-04 TUZUK-04 TUZUK-05 UY-01 YON-04
```

3. S4-C targeted smoke rerun.
4. S4-D P0/TEB guard rerun.
5. S4-E regression guard rerun.
6. Full shadow benchmark only if targeted gates pass.

Minimum S5 full targets:

```text
raw_score_proxy >= 800
pass_proxy >= 89
wrong_family <= 6
wrong_document <= 5
hallucinated_identifier <= 5
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
```

## Stop Rules

Stop S5 immediately if:

```text
MULGA guard falls below 4/5
TEBLIGLER guard falls below 6/8
TEB-06 fails
active non-MULGA overapplication returns
wrong_family increases above 8
hallucinated_identifier increases above 6
unsupported_confident_answer > 0
answer_contract_invalid > 0
source_key_v2_collision > 0
binding_collision > 0
live 8000 is modified
QID-specific branch appears
```

## Productization / Fine-Tuning

Productization remains closed.

Fine-tuning remains closed.

The residuals are deterministic source-family, identifier-surface, article-surface, and source-identity issues. They do not justify model training.
