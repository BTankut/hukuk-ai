# Phase 16A Corpus Materialization Remediation

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T081121Z_phase15_full`
- corpus_materialization_required_rows: 13
- body_text_available_rows: 10
- selected_article_zero_or_empty_rows: 12
- source_key_collision_rows: 3

## By Family
- CB_GENELGE: 4 rows; qids=CBG-01, CBG-02, CBG-03, CBG-04
- CB_KARAR: 2 rows; qids=CBKAR-07, CBKAR-08
- KANUN: 1 rows; qids=KANUN-06
- KHK: 1 rows; qids=KHK-05
- TEBLIGLER: 3 rows; qids=TEB-01, TEB-03, TEB-04
- TUZUK: 1 rows; qids=TUZUK-05
- YONETMELIK: 1 rows; qids=YON-04

## Reason Counts
- body_span_available_but_title_or_article_zero: 10
- source_key_collision_without_family_body_span: 2
- title_only_or_unreadable_body: 1

## Owner Counts
- canonical_parser: 7
- source_identity+canonical_parser: 3
- canonical_parser+cb_genelge_body_span: 2
- corpus_ingestion: 1

## Status Counts
- body_exists_but_article_zero_materialization_required: 9
- blocked_by_family_source_key_collision: 3
- text_extraction_repair_required: 1

## Explicit Remediation Rows
- CBG-01: expected=CB_GENELGE, selected=CB_GENELGE, reason=body_span_available_but_title_or_article_zero, body=True:306, collision=False, owner=canonical_parser+cb_genelge_body_span, status=body_exists_but_article_zero_materialization_required
- CBG-02: expected=CB_GENELGE, selected=CB_GENELGE, reason=body_span_available_but_title_or_article_zero, body=True:265, collision=True, owner=source_identity+canonical_parser, status=blocked_by_family_source_key_collision
- CBG-03: expected=CB_GENELGE, selected=CB_GENELGE, reason=body_span_available_but_title_or_article_zero, body=True:294, collision=False, owner=canonical_parser+cb_genelge_body_span, status=body_exists_but_article_zero_materialization_required
- CBG-04: expected=CB_GENELGE, selected=CB_GENELGE, reason=source_key_collision_without_family_body_span, body=False:257, collision=True, owner=source_identity+canonical_parser, status=blocked_by_family_source_key_collision
- CBKAR-07: expected=CB_KARAR, selected=CB_KARAR, reason=body_span_available_but_title_or_article_zero, body=True:1928, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required
- CBKAR-08: expected=CB_KARAR, selected=CB_KARAR, reason=source_key_collision_without_family_body_span, body=False:197, collision=True, owner=source_identity+canonical_parser, status=blocked_by_family_source_key_collision
- KANUN-06: expected=KANUN, selected=KANUN, reason=title_only_or_unreadable_body, body=False:915, collision=False, owner=corpus_ingestion, status=text_extraction_repair_required
- KHK-05: expected=KHK, selected=KHK, reason=body_span_available_but_title_or_article_zero, body=True:522, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required
- TEB-01: expected=TEBLIGLER, selected=TEBLIGLER, reason=body_span_available_but_title_or_article_zero, body=True:5028, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required
- TEB-03: expected=TEBLIGLER, selected=TEBLIGLER, reason=body_span_available_but_title_or_article_zero, body=True:2354, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required
- TEB-04: expected=TEBLIGLER, selected=TEBLIGLER, reason=body_span_available_but_title_or_article_zero, body=True:7988, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required
- TUZUK-05: expected=TUZUK, selected=TUZUK, reason=body_span_available_but_title_or_article_zero, body=True:5566, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required
- YON-04: expected=YONETMELIK, selected=YONETMELIK, reason=body_span_available_but_title_or_article_zero, body=True:11465, collision=False, owner=canonical_parser, status=body_exists_but_article_zero_materialization_required

## Phase 16A Decision
- 13/13 corpus-required rows are explicitly classified.
- High-impact first fix should target document-level body-span materialization for CB_GENELGE/CB_KARAR/TEBLIGLER rows where body exists but selected article is m.0.
- Source-key v2 is required before collision rows can be trusted as materialized.
- KANUN-06 remains a text extraction/body readability repair, not a selector prompt issue.
