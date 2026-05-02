# Phase 22F-S4-R Family / Identifier Residual Audit

Date: 2026-05-02

## Scope

Audit-only classification of the 11 Phase 22F-S4 full-shadow fail rows. No runtime behavior, retrieval, prompt, model, corpus, or live serving state was changed.

## Inputs

- Candidate: `reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark`
- Phase 22A baseline: `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`
- Phase 21F baseline: `reports/benchmark/runs/20260429T174747Z_phase21F_full`

## Acceptance

- Rows classified: `11/11`
- New vs pre-existing residuals separated: `yes`
- Runtime behavior changed: `no`

## Root Cause Counts

- `family_taxonomy_boundary`: 3
- `preexisting_residual`: 1
- `s4_policy_side_effect`: 2
- `source_identity_wrong_document`: 5

## Safe Action Counts

- `defer_corpus_backfill`: 3
- `defer_manual_legal_review`: 1
- `defer_scorer_rubric_review`: 2
- `fix_now_generalizable`: 4
- `watch_only`: 1

## New Regressions vs Phase 22A

| QID | S4 score | Phase22A score | Root cause | Safe action |
| --- | ---: | ---: | --- | --- |
| MULGA-05 | 5.45 | 7.25 | s4_policy_side_effect | fix_now_generalizable |
| TEB-04 | 0.00 | 7.25 | source_identity_wrong_document | fix_now_generalizable |
| UY-01 | 6.02 | 8.09 | family_taxonomy_boundary | fix_now_generalizable |

## Pre-Existing Residuals

| QID | S4 score | Phase22A score | Root cause | Safe action |
| --- | ---: | ---: | --- | --- |
| CBY-04 | 6.85 | 6.85 | family_taxonomy_boundary | defer_manual_legal_review |
| CBY-06 | 6.80 | 6.80 | preexisting_residual | watch_only |
| KANUN-12 | 1.45 | 1.45 | source_identity_wrong_document | defer_corpus_backfill |
| KKY-01 | 6.65 | 6.65 | family_taxonomy_boundary | defer_scorer_rubric_review |
| KKY-03 | 1.45 | 1.45 | source_identity_wrong_document | defer_corpus_backfill |
| TUZUK-04 | 4.63 | 0.00 | s4_policy_side_effect | fix_now_generalizable |
| TUZUK-05 | 3.25 | 3.25 | source_identity_wrong_document | defer_scorer_rubric_review |
| YON-04 | 3.25 | 3.25 | source_identity_wrong_document | defer_corpus_backfill |

## Row-Level Audit

| QID | Failure classes | Claimed | Selected source | S4 bucket | Root cause | Safe action |
| --- | --- | --- | --- | --- | --- | --- |
| CBY-04 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only | CB_KARARNAME / 11 m.10 | cb_kararname / 11 / 11 m.10/f.0 | not_applicable | family_taxonomy_boundary | defer_manual_legal_review |
| CBY-06 | missing_required_content_signal ; partial_grounding_only | CB_YONETMELIK / 20046801 m.14 | cb_yonetmelik / 20046801 / 20046801 m.14/f.0 | not_applicable | preexisting_residual | watch_only |
| KANUN-12 | missing_gold_document_signal ; missing_required_content_signal ; wrong_family ; wrong_document ; partial_grounding_only | KKY / unknown | yonetmelik / 12879 / 12879 m.15/f.0 | not_applicable | source_identity_wrong_document | defer_corpus_backfill |
| KKY-01 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only | YONETMELIK / 34360 m.1 | yonetmelik / 34360 / 34360 m.1/f.0 | not_applicable | family_taxonomy_boundary | defer_scorer_rubric_review |
| KKY-03 | missing_gold_document_signal ; missing_required_content_signal ; wrong_family ; wrong_document ; partial_grounding_only | YONETMELIK / unknown | yonetmelik / 12879 / 12879 m.4/f.0 | not_applicable | source_identity_wrong_document | defer_corpus_backfill |
| MULGA-05 | missing_required_content_signal ; wrong_article ; partial_grounding_only | MULGA / 6570 m.gec1 | mulga_kanun / 6570 / 6570 m.GEC1/f.0 | legacy_mulga_historical_surface_without_relation_chain | s4_policy_side_effect | fix_now_generalizable |
| TEB-04 | auto_fail_triggered ; missing_required_content_signal ; partial_grounding_only | TEBLIGLER / 24345 m.1 | teblig / 24345 / 24345 m.1/f.0 | active_non_mulga_preserve_family | source_identity_wrong_document | fix_now_generalizable |
| TUZUK-04 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only | MULGA / 859727 m.4 | tuzuk / 859727 / 859727 m.4/f.0 | legacy_mulga_historical_surface_without_relation_chain | s4_policy_side_effect | fix_now_generalizable |
| TUZUK-05 | missing_gold_document_signal ; missing_required_content_signal ; wrong_document ; partial_grounding_only | TUZUK / unknown | tuzuk / 315481 / 315481 m.0/f.0 | not_applicable | source_identity_wrong_document | defer_scorer_rubric_review |
| UY-01 | missing_required_content_signal ; wrong_family ; hallucinated_identifier ; partial_grounding_only | YONETMELIK / 12420 m.4 | yonetmelik / 12420 / 12420 m.4/f.0 | not_applicable | family_taxonomy_boundary | fix_now_generalizable |
| YON-04 | missing_gold_document_signal ; missing_required_content_signal ; wrong_document ; partial_grounding_only | YONETMELIK / unknown | yonetmelik / 12536 / 12536 m.23/f.0 | not_applicable | source_identity_wrong_document | defer_corpus_backfill |

## Audit Notes

- `CBY-04`: Pre-existing CB_YONETMELIK/CB_KARARNAME taxonomy boundary; selected document/article are exact, so runtime patch is unsafe without legal taxonomy decision.
- `CBY-06`: Pre-existing partial-grounding/update residual; no wrong_family or hallucinated_identifier signal in S4.
- `KANUN-12`: Pre-existing wrong-document selection: hosting/BTK traffic query lands on nuclear reactor safety regulation.
- `KKY-01`: Pre-existing taxonomy/scorer boundary: correct banking IT regulation is surfaced as YONETMELIK while benchmark family is KKY.
- `KKY-03`: Pre-existing wrong-document selection: banking/KVKK/cloud query lands on nuclear reactor safety regulation.
- `MULGA-05`: New S4 regression; legacy historical surface selects GEC1 while Phase22A used a document-level/article-344 surface.
- `TEB-04`: New regression; KDV tevkifat/iade query lands on Electronic Notification General Communique instead of consolidated KDV communique surface.
- `TUZUK-04`: Existing failure improved in score but S4 historical-surface policy rewrites active selected TUZUK evidence to MULGA.
- `TUZUK-05`: Pre-existing wrong-document/title-only hierarchy residual; selected old food/public health tüzük does not satisfy the conflict question.
- `UY-01`: New regression; UY-vs-YONETMELIK collision resolution prefers a graduate regulation over the undergraduate course-registration UY surface.
- `YON-04`: Pre-existing wrong-document selection: KVKK destruction/imha query lands on nuclear power plant safety regulation.

## Conclusion

There is no basis for broad runtime patching in S4-R. A small set of generalizable candidates exists for a later S5 design, but several rows are pre-existing source identity, legal taxonomy, scorer/rubric, or corpus/materialization residuals.
