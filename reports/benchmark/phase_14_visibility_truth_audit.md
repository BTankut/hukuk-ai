# Phase 11A Source Visibility / Index Truth Audit

- source_run_dir: `reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic`
- rows_analyzed: 18

## Visibility Probe Status
- present_but_family_misclassified: 7
- present_but_not_retrieved: 5
- truly_missing_from_index: 4
- visible_but_lost_after_retrieval: 2

## Owner Counts
- canonical_mapping: 7
- retrieval_routing: 5
- corpus_ingestion: 4
- selector_identity: 2

## Milvus Index Status
- not_checked: 18

## Expected Family Counts
- KANUN: 4
- YONETMELIK: 4
- CB_GENELGE: 2
- CB_YONETMELIK: 2
- MULGA: 2
- TUZUK: 2
- CB_KARAR: 1
- TEBLIGLER: 1

## Open Rows
- CBG-01: status=truly_missing_from_index; expected=CB_GENELGE; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- CBG-04: status=visible_but_lost_after_retrieval; expected=CB_GENELGE; matched_family=cb_genelge; index=not_checked; path=pre_rerank:1; owner=selector_identity; action=Source appears in initial candidates; inspect selector/reranker identity lock and article-span choice.
- CBKAR-05: status=present_but_not_retrieved; expected=CB_KARAR; matched_family=cb_karar; index=not_checked; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBY-01: status=truly_missing_from_index; expected=CB_YONETMELIK; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- CBY-04: status=present_but_family_misclassified; expected=CB_YONETMELIK; matched_family=kky; index=not_checked; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `33899` from `kky` toward title-inferred `cb_yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- KANUN-02: status=present_but_family_misclassified; expected=KANUN; matched_family=kky; index=not_checked; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `6249` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- KANUN-03: status=present_but_family_misclassified; expected=KANUN; matched_family=kky; index=not_checked; path=pre_rerank:1; owner=canonical_mapping; action=Fix source family mapping for `12459` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- KANUN-04: status=present_but_family_misclassified; expected=KANUN; matched_family=kky; index=not_checked; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `24038` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- KANUN-18: status=truly_missing_from_index; expected=KANUN; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- MULGA-03: status=visible_but_lost_after_retrieval; expected=MULGA; matched_family=tuzuk; index=not_checked; path=pre_rerank:1; owner=selector_identity; action=Source appears in initial candidates; inspect selector/reranker identity lock and article-span choice.
- MULGA-04: status=present_but_not_retrieved; expected=MULGA; matched_family=kanun; index=not_checked; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- TEB-06: status=present_but_not_retrieved; expected=TEBLIGLER; matched_family=kanun; index=not_checked; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- TUZUK-04: status=present_but_not_retrieved; expected=TUZUK; matched_family=kanun; index=not_checked; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- TUZUK-05: status=truly_missing_from_index; expected=TUZUK; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- YON-02: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=not_checked; path=pre_rerank:1; owner=canonical_mapping; action=Fix source family mapping for `20237` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-05: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=not_checked; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `23722` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-06: status=present_but_not_retrieved; expected=YONETMELIK; matched_family=kanun; index=not_checked; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- YON-08: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=not_checked; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `13948` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.

## Interpretation
- `truly_missing_from_index`: no reliable canonical catalog/index match was found.
- `present_but_not_retrieved`: source exists in catalog/index but was absent from initial retrieval candidates.
- `present_but_family_misclassified`: source exists, but canonical family does not align with expected family.
- `visible_but_lost_after_retrieval`: source is visible before selection; next owner is selector/identity, not corpus acquisition.
