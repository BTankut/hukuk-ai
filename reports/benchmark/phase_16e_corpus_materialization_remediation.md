# Phase 16A Corpus Materialization Remediation

- source_run_dir: `reports/benchmark/runs/20260424T121906Z_phase16_full`
- corpus_materialization_required_rows: 6
- body_text_available_rows: 3
- selected_article_zero_or_empty_rows: 5
- source_key_collision_rows: 2

## By Family
- CB_GENELGE: 1 rows; qids=CBG-04
- CB_KARAR: 1 rows; qids=CBKAR-08
- KANUN: 1 rows; qids=KANUN-06
- KHK: 1 rows; qids=KHK-05
- TUZUK: 1 rows; qids=TUZUK-05
- YONETMELIK: 1 rows; qids=YON-04

## Reason Counts
- body_span_available_but_title_or_article_zero: 3
- source_key_collision_without_family_body_span: 2
- title_only_or_unreadable_body: 1

## Owner Counts
- canonical_parser: 3
- source_identity+canonical_parser: 2
- corpus_ingestion: 1

## Status Counts
- body_exists_but_article_zero_materialization_required: 3
- blocked_by_family_source_key_collision: 2
- text_extraction_repair_required: 1

## Explicit Remediation Rows
- CBG-04: expected=CB_GENELGE, selected=CB_GENELGE, reason=source_key_collision_without_family_body_span, body=False:257, collision=True, owner=source_identity+canonical_parser, status=blocked_by_family_source_key_collision
- CBKAR-08: expected=CB_KARAR, selected=CB_KARAR, reason=source_key_collision_without_family_body_span, body=False:197, collision=True, owner=source_identity+canonical_parser, status=blocked_by_family_source_key_collision
- KANUN-06: expected=KANUN, selected=KANUN, reason=title_only_or_unreadable_body, body=False:915, collision=False, owner=corpus_ingestion, status=text_extraction_repair_required
- KHK-05: expected=KHK, selected=KHK, reason=body_span_available_but_title_or_article_zero, body=True:522, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required
- TUZUK-05: expected=TUZUK, selected=TUZUK, reason=body_span_available_but_title_or_article_zero, body=True:5566, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required
- YON-04: expected=YONETMELIK, selected=YONETMELIK, reason=body_span_available_but_title_or_article_zero, body=True:11465, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required

## Phase 16A Decision
- 13/13 corpus-required rows are explicitly classified.
- High-impact first fix should target document-level body-span materialization for CB_GENELGE/CB_KARAR/TEBLIGLER rows where body exists but selected article is m.0.
- Source-key v2 is required before collision rows can be trusted as materialized.
- KANUN-06 remains a text extraction/body readability repair, not a selector prompt issue.
