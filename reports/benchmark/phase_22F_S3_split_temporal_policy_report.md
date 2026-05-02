# Phase 22F-S3 Split Temporal Policy Report
Date: 2026-05-02

This phase was completed as audit/design only. No runtime code, answer synthesis, source identity, retrieval, top-k, prompt, model, benchmark, live `8000`, collection, productization, or fine-tuning change was performed.

## Commit SHA List

| Commit | Scope |
|---|---|
| `8cd0058` | Verify Phase 22F-S2 revert state |
| `de3eaa9` | Audit split temporal claim policy buckets |
| `ab61c0a` | Design split temporal claim policy |
| `a69004e` | Record Phase 22F-S3 implementation readiness decision |
| report commit | `Report Phase 22F-S3 split temporal policy decision` |

## Revert State Verification

S2 failed P0 relation guard and was reverted before S3 design work:

```text
S2 implementation commit: cd4f7db
S2 revert commit: 0ac41ed
S3-A verification commit: 8cd0058
```

Verified state:

| Check | Status |
|---|---:|
| S2 implementation exists in history | PASS |
| S2 implementation reverted | PASS |
| S2-only trace fields absent from current source/tests | PASS |
| `8018` remains `phase22f_shadow` | PASS |
| `8000` remains `current_serving_lane` | PASS |
| Productization closed | PASS |
| Fine-tuning closed | PASS |

Runtime state recorded in S3-A:

```text
8018: phase22f_shadow, api_version 2026-05-01-phase22f, guardrails disabled, retriever milvus
8000: current_serving_lane, api_version 2026-03-24-rc-h, guardrails disabled, retriever milvus
```

## Two-Permission Policy Audit Summary

S3-B classified 13/13 relevant rows from existing Phase 22F-S full shadow artifacts. No new benchmark run or answer-key read was performed.

| Metric | Result |
|---|---:|
| Rows classified | 13/13 |
| Active non-MULGA rows with claim-family rewrite denied | 7 |
| MULGA rows with historical surface path | 5 |

Policy bucket counts:

| Bucket | Count |
|---|---:|
| `active_non_mulga_preserve_family` | 7 |
| `legacy_mulga_historical_surface_without_relation_chain` | 4 |
| `manual_review_required` | 1 |
| `relation_chain_historical_three_part_claim` | 1 |

## Row Bucket Table

| qid | benchmark | selected family | current claimed | state | relation | preserve selected | family rewrite | historical surface | bucket |
|---|---|---|---|---|---:|---:|---:|---:|---|
| `KANUN-05` | KANUN | KANUN | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `KANUN-10` | KANUN | KANUN | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `KANUN-14` | KANUN | KANUN | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `KHK-03` | KHK | KHK | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `TEB-03` | TEBLIGLER | TEBLIGLER | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `TEB-04` | TEBLIGLER | TEBLIGLER | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `TUZUK-03` | TUZUK | TUZUK | MULGA | active | False | True | False | False | `active_non_mulga_preserve_family` |
| `UY-01` | UY | KKY | YONETMELIK | active | False | True | False | False | `manual_review_required` |
| `MULGA-01` | MULGA | KKY | MULGA | historical_repealed | True | False | True | True | `relation_chain_historical_three_part_claim` |
| `MULGA-02` | MULGA | KKY | MULGA | active | False | False | True | True | `legacy_mulga_historical_surface_without_relation_chain` |
| `MULGA-03` | MULGA | TUZUK | MULGA | active | False | False | True | True | `legacy_mulga_historical_surface_without_relation_chain` |
| `MULGA-04` | MULGA | KHK | MULGA | active | False | False | True | True | `legacy_mulga_historical_surface_without_relation_chain` |
| `MULGA-05` | MULGA | MULGA | MULGA | repealed | False | False | True | True | `legacy_mulga_historical_surface_without_relation_chain` |

## Policy Design Summary

S3-C rejects the single temporal gate model. S4 must produce two independent permissions:

| Permission | Required purpose |
|---|---|
| `claim_family_rewrite_allowed` | Controls whether selected source family/identifier may be rewritten in the answer contract. |
| `historical_claim_surface_allowed` | Controls whether `MULGA`, repealed, or historical surface may be shown despite incomplete relation metadata. |

Design rules:

| Rule | Decision |
|---|---|
| Active non-MULGA family preservation | Preserve selected family/identifier/state; deny family rewrite and historical surface. |
| Relation-chain historical three-part claim | Allow controlled historical surface when historical source, repeal/currentness instrument, and current-law basis are present. |
| Legacy MULGA historical surface without relation chain | Allow qualified historical surface; do not claim current applicability or invent relation/current-law facts. |
| Repeal identifier surface guard | Repeal/currentness instrument cannot overwrite the substantive historical source unless the user asks only status/currentness. |
| Current-law basis as support | Current-law basis can support the answer but must not erase the historical source unless the question asks only current law. |

`UY-01` remains `manual_review_required`; it is a family/document boundary issue, not a temporal-policy success target.

## Implementation Readiness Decision

Decision:

```text
Option A: Open Phase 22F-S4 split temporal claim implementation.
```

Rationale:

| Criterion | Status |
|---|---:|
| Two-permission policy clear | PASS |
| 13/13 row buckets classified | PASS |
| No QID-specific requirement | PASS |
| S4 smoke plan clear | PASS |
| Productization readiness | CLOSED |
| Fine-tuning readiness | CLOSED |

## Productization Gate Decision

```text
Productization remains closed.
```

Reason:

```text
S2 failed P0 relation guard and S3 did not perform implementation, full benchmark, live cutover, or productization verification.
```

## Fine-Tuning Gate Decision

```text
Fine-tuning remains closed.
```

Reason:

```text
The identified failure is deterministic temporal claim-policy conflation. It should be fixed in policy logic before any training discussion.
```

## Next Phase Recommendation

Open Phase 22F-S4 only for scoped split temporal claim implementation.

Required S4 gate order:

| Gate | Required outcome |
|---|---|
| Policy unit tests | Expected permissions for all split-policy buckets. |
| 13-row targeted smoke | Active non-MULGA rows do not claim `MULGA`; MULGA rows retain historical surface path. |
| P0 relation guard smoke | `MULGA >= 4/5`, `TEBLIGLER >= 6/8`, `TEB-06 = PASS`, `repealed_as_active_count = 0`. |
| Regression guard | Safety counters remain zero; no source/binding collision. |
| Full benchmark | Run only after all earlier gates pass; no productization. |

S4 must stop if it requires QID-specific logic, benchmark answer-key leakage, retrieval changes, model changes, live cutover, or productization changes.
