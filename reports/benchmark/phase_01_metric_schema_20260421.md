# Phase 1 Metric Schema Groundwork

This document defines the benchmark-specific schema added after Phase 0.5.

## Canonical Source Families

- `KANUN`
- `CB_KARARNAME`
- `YONETMELIK`
- `CB_YONETMELIK`
- `CB_KARAR`
- `CB_GENELGE`
- `KHK`
- `TUZUK`
- `KKY`
- `UY`
- `TEBLIGLER`
- `MULGA`

## Canonical Source Signal

Each scored answer may expose:

- `source_family_canonical`
- `source_title_canonical`
- `source_identifier_canonical`
- `article_or_section_canonical`
- `effective_state_canonical`: `active`, `amended`, `repealed`, or `unknown`
- `temporal_anchor`

## Phase 1 Sub-Metrics

The upgraded scorer must output:

- `family_match_score`
- `document_match_score`
- `article_match_score`
- `temporal_validity_score`
- `grounding_score`
- `answer_contract_score`
- `hallucinated_source_penalty`
- `auto_fail_triggered`

## Phase 1 Failure Taxonomy

The upgraded scorer must track:

- `wrong_family`
- `wrong_document`
- `wrong_article`
- `repealed_source_used_as_active`
- `missing_temporal_qualification`
- `hallucinated_identifier`
- `unsupported_confident_claim`
- `answer_contract_missing`
- `partial_grounding_only`

The schema is heuristic and measurement-oriented. It is not a legal correctness oracle.
