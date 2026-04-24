# Phase 15C Corpus Materialization Backlog

- source_run_dir: `reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- corpus_materialization_required_rows: 13
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

## Fix Type Counts
- article_zero_reparse_or_body_span_link: 7
- family_aware_source_key_materialization: 3
- official_genelge_body_acquisition: 2
- text_extraction_repair: 1

## Owner Counts
- canonical_parser: 7
- corpus_ingestion: 3
- source_identity+canonical_parser: 3

## Rows
- CBG-01: family=CB_GENELGE, fix=official_genelge_body_acquisition, owner=corpus_ingestion, reason=body_span_available_but_title_or_article_zero, collision=none
- CBG-02: family=CB_GENELGE, fix=family_aware_source_key_materialization, owner=source_identity+canonical_parser, reason=body_span_available_but_title_or_article_zero, collision=26=cb_genelge:yurt disinda yurutulen faaliyetlerde dikkat edilmesi gereken hususlar ile ilgili|cb_karar:4 7 1956 tarihli ve 6772 sayili kanun kapsamina giren kurumlarda calisan isciler; 29=cb_genelge:ulusal akilli sehirler stratejisi ve eylem plani ile ilgili|cb_karar:turkakim kara kismi 2 gaz boru hatti projesi kapsaminda tekirdag ve kirklareli i
- CBG-03: family=CB_GENELGE, fix=official_genelge_body_acquisition, owner=corpus_ingestion, reason=body_span_available_but_title_or_article_zero, collision=none
- CBG-04: family=CB_GENELGE, fix=family_aware_source_key_materialization, owner=source_identity+canonical_parser, reason=source_key_collision_without_family_body_span, collision=3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:ust kademe kamu yoneticilerinin atanmalarina iliskin usul ve esaslar ile kamu ku
- CBKAR-07: family=CB_KARAR, fix=article_zero_reparse_or_body_span_link, owner=canonical_parser, reason=body_span_available_but_title_or_article_zero, collision=none
- CBKAR-08: family=CB_KARAR, fix=family_aware_source_key_materialization, owner=source_identity+canonical_parser, reason=source_key_collision_without_family_body_span, collision=9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1
- KANUN-06: family=KANUN, fix=text_extraction_repair, owner=corpus_ingestion, reason=title_only_or_unreadable_body, collision=none
- KHK-05: family=KHK, fix=article_zero_reparse_or_body_span_link, owner=canonical_parser, reason=body_span_available_but_title_or_article_zero, collision=none
- TEB-01: family=TEBLIGLER, fix=article_zero_reparse_or_body_span_link, owner=canonical_parser, reason=body_span_available_but_title_or_article_zero, collision=none
- TEB-03: family=TEBLIGLER, fix=article_zero_reparse_or_body_span_link, owner=canonical_parser, reason=body_span_available_but_title_or_article_zero, collision=none
- TEB-04: family=TEBLIGLER, fix=article_zero_reparse_or_body_span_link, owner=canonical_parser, reason=body_span_available_but_title_or_article_zero, collision=none
- TUZUK-05: family=TUZUK, fix=article_zero_reparse_or_body_span_link, owner=canonical_parser, reason=body_span_available_but_title_or_article_zero, collision=none
- YON-04: family=YONETMELIK, fix=article_zero_reparse_or_body_span_link, owner=canonical_parser, reason=body_span_available_but_title_or_article_zero, collision=none
