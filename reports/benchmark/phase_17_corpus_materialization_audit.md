# Phase 15C Corpus Materialization Backlog

- source_run_dir: `reports/benchmark/runs/20260424T212636_phase17f_full`
- corpus_materialization_required_rows: 2
- source_key_collision_rows: 1

## By Family
- CB_KARAR: 1 rows; qids=CBKAR-08
- KANUN: 1 rows; qids=KANUN-06

## Reason Counts
- title_only_or_unreadable_body: 2

## Fix Type Counts
- family_aware_source_key_materialization: 1
- text_extraction_repair: 1

## Owner Counts
- source_identity+canonical_parser: 1
- corpus_ingestion: 1

## Rows
- CBKAR-08: family=CB_KARAR, fix=family_aware_source_key_materialization, owner=source_identity+canonical_parser, reason=title_only_or_unreadable_body, collision=9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1
- KANUN-06: family=KANUN, fix=text_extraction_repair, owner=corpus_ingestion, reason=title_only_or_unreadable_body, collision=none
