# Phase 16A Corpus Materialization Remediation

- source_run_dir: `reports/benchmark/runs/20260424T_phase17a_sourcekey_binding_smoke`
- corpus_materialization_required_rows: 2
- body_text_available_rows: 0
- selected_article_zero_or_empty_rows: 2
- legacy_source_key_collision_rows: 2
- binding_source_key_collision_rows: 0

## By Family
- CB_GENELGE: 1 rows; qids=CBG-04
- CB_KARAR: 1 rows; qids=CBKAR-08

## Reason Counts
- title_only_or_unreadable_body: 2

## Owner Counts
- corpus_ingestion: 2

## Status Counts
- text_extraction_repair_required: 2

## Explicit Remediation Rows
- CBG-04: expected=CB_GENELGE, selected=CB_GENELGE, reason=title_only_or_unreadable_body, body=False:257, legacy_collision=True, binding_collision=False, owner=corpus_ingestion, status=text_extraction_repair_required
- CBKAR-08: expected=CB_KARAR, selected=CB_KARAR, reason=title_only_or_unreadable_body, body=False:197, legacy_collision=True, binding_collision=False, owner=corpus_ingestion, status=text_extraction_repair_required

## Phase 16A Decision
- Corpus-required rows are explicitly classified.
- Legacy source-key collision is treated as a blocker only when canonical v2 binding is absent or binding collision remains true.
- Rows with clean v2 binding but unreadable/title-only body remain corpus/parser backlog, not source-key blockers.
