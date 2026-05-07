# Phase 24HT-B Same-Family Domain Compatibility Design

## Goal

Prevent a generic source inside the same legal family from winning solely because it has article-level semantic overlap or a stale selected-source lock.

## Feature Flag

`ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true`

Default is off. Candidate smoke enables it only on non-live `8042`.

## Scoring Inputs

- `query_domain_terms`: normalized legal/domain terms from the user query, for example consumer, distance sale, cayma, exception, internet, custom production.
- `document_domain_terms`: normalized title/body/source metadata terms from candidate documents.
- `issuer_or_regulator_signal`: issuer/regulator compatibility. This is supporting evidence only; it cannot by itself override explicit user law/article references.
- `title_overlap_signal`: source title and canonical title overlap with query domain terms.
- `article_semantic_signal`: article/body overlap with query terms.
- `source_identity_signal`: source identity reranker score, lane sources, and reasons.
- `primary_vs_supporting_law_role`: if query explicitly names a law/article, that named source remains primary; otherwise source identity can arbitrate primary document role.

## Tie Break Rules

1. Explicit law/article references win. Same-family domain scoring must not override `TBK m.255`, `6502 m.48`, numbered law, or exact article requests.
2. Relation or historical/legacy scope selectors remain outside this rule. They already have dedicated arbitration.
3. Same-family override requires source identity to be applied and to expose a top document in `top_scores`.
4. Top source identity document must have score at least `45`.
5. Top source identity document must be dual-lane confirmed via `dual_lane_confirmation` or both `metadata_guided_recall` and `semantic_dense_recall`.
6. Target document must be present in the article selector candidate pool and have span-level support, such as text overlap, heading/title overlap, exception signal, or scope signal.
7. Target and currently locked documents must be same family or temporally compatible same-family aliases.
8. Source identity margin over the currently locked document must be at least `20`.
9. If all checks pass, article selector changes document lock reason to `same_family_domain_identity_lock`.

## Trace Fields

- `phase24ht_same_family_domain_scoring_enabled`
- `phase24ht_same_family_domain_lock_applied`
- `phase24ht_same_family_domain_lock_reason`
- `phase24ht_same_family_domain_selected_source_key`
- `phase24ht_same_family_domain_selected_source_title`
- `phase24ht_same_family_domain_selected_document_identity_score`
- `phase24ht_same_family_domain_replaced_document_identity_score`
- `phase24ht_same_family_domain_score_margin`

## Safety

The design does not include QID strings, answer-key values, hardcoded law titles, top-k expansion, prompt changes, model changes, or live collection changes.

The intended implementation surface is `api-gateway/src/rag/article_span_selection.py` plus the `routers/chat.py` wrapper so the existing source identity trace can be passed to article selector.
