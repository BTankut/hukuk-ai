# Phase 24H Legal / Scorer Review Follow-Up

Generated: 2026-05-03T12:31:00Z

Branch: B — review results do not exist.

Purpose: refresh the Phase 24B legal/scorer review packet and define exactly what reviewers must return before internal_eval or productization can advance.

Source packet:

- `reports/benchmark/phase_24B_legal_scorer_review_packet.md`
- `reports/benchmark/phase_24B_legal_scorer_review_packet.csv`

Return checklist:

- `reports/benchmark/phase_24H_legal_scorer_review_checklist.md`

## Rows Requiring Review

| QID | Review Type | Blocking Effect |
|---|---|---|
| CBY-04 | legal taxonomy + scorer expectation | blocks productization |
| CBY-06 | scorer rubric + amended-source completeness | blocks productization |
| KKY-01 | legal taxonomy + scorer compatibility | blocks productization |
| TEB-04 | scorer rubric + legal source sufficiency | blocks internal_eval and productization |
| TUZUK-04 | legal framing + scorer completeness | blocks productization; affects source backfill safety |

## Questions To Reviewers

| QID | Legal Question | Scorer Question |
|---|---|---|
| CBY-04 | Should archive retention/selection/transfer/destruction workflow be answered from a CB yönetmelik as primary source, with CBK 11 only as institutional basis? | Should CBK 11 be scored as supporting source only and fail if the primary regulation is not selected? |
| CBY-06 | Which amended provision after April 2026 controls transportation of personnel children in public personnel service vehicles? | Does the benchmark require a different article/span or additional fact slots for the April 2026 amendment? |
| KKY-01 | Should the banking information systems regulation be classified as KKY or general YONETMELIK for this benchmark taxonomy? | Should KKY/YONETMELIK be compatible for institution-specific regulations? |
| TEB-04 | Is the consolidated KDV Genel Uygulama Tebliği the correct main source for KDV tevkifat/iade questions? | Is the current auto-fail due to scorer/materialization mismatch rather than wrong source selection? |
| TUZUK-04 | Is Radyasyon Güvenliği Tüzüğü sufficient for the 2026 old-tüzük/current-law risk framing? | Should the item require explicit comparison with 6331/current regulations? |

## Allowed Decision Enums

Reviewers must return exactly one primary decision per row:

- `runtime_fix_allowed`
- `runtime_fix_not_allowed`
- `scorer_rubric_mismatch`
- `legal_taxonomy_confirmed`
- `manual_residual_accepted`
- `needs_more_review`

Optional secondary tags:

- `requires_corpus_backfill`
- `requires_article_span_materialization`
- `requires_source_identity_design`
- `blocks_internal_eval`
- `blocks_productization`

## Return File Names

Expected returned files:

- `reports/benchmark/legal_review_returns/filled_phase_24H_legal_scorer_review_return.csv`
- Optional narrative: `reports/benchmark/legal_review_returns/filled_phase_24H_legal_scorer_review_notes.md`

## Blocking Effect

Until returns are received and normalized:

- TEB-04 continues to block internal_eval.
- All five review rows continue to block productization.
- No runtime fix is authorized.
- No QID-specific rule is authorized.

## Decision

Phase 24H Branch B follow-up is ready. Continue to Phase 24I source acquisition readiness.
