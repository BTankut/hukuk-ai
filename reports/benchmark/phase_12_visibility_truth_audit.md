# Phase 11A Source Visibility / Index Truth Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full`
- rows_analyzed: 26

## Visibility Probe Status
- present_but_not_retrieved: 13
- present_but_family_misclassified: 9
- truly_missing_from_index: 4

## Owner Counts
- retrieval_routing: 13
- canonical_mapping: 9
- corpus_ingestion: 4

## Milvus Index Status
- index_present: 22
- not_checked: 4

## Expected Family Counts
- YONETMELIK: 6
- KKY: 5
- CB_YONETMELIK: 4
- KANUN: 4
- CB_GENELGE: 2
- CB_KARAR: 2
- KHK: 1
- TUZUK: 1
- UY: 1

## Open Rows
- CBG-01: status=truly_missing_from_index; expected=CB_GENELGE; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- CBG-03: status=present_but_not_retrieved; expected=CB_GENELGE; matched_family=cb_genelge; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBKAR-01: status=present_but_not_retrieved; expected=CB_KARAR; matched_family=cb_karar; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBKAR-05: status=present_but_not_retrieved; expected=CB_KARAR; matched_family=cb_karar; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBY-01: status=truly_missing_from_index; expected=CB_YONETMELIK; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- CBY-04: status=present_but_family_misclassified; expected=CB_YONETMELIK; matched_family=kky; index=index_present; path=pre_rerank:12; owner=canonical_mapping; action=Fix source family mapping for `33899` from `kky` toward title-inferred `cb_yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- CBY-05: status=present_but_not_retrieved; expected=CB_YONETMELIK; matched_family=cb_yonetmelik; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBY-06: status=present_but_not_retrieved; expected=CB_YONETMELIK; matched_family=cb_yonetmelik; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KANUN-02: status=present_but_family_misclassified; expected=KANUN; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `6249` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- KANUN-03: status=present_but_family_misclassified; expected=KANUN; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `12459` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- KANUN-06: status=present_but_not_retrieved; expected=KANUN; matched_family=kanun; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KANUN-19: status=present_but_family_misclassified; expected=KANUN; matched_family=teblig; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `29033` from `teblig` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- KHK-03: status=truly_missing_from_index; expected=KHK; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- KKY-02: status=present_but_not_retrieved; expected=KKY; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KKY-04: status=present_but_not_retrieved; expected=KKY; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KKY-06: status=present_but_not_retrieved; expected=KKY; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KKY-09: status=present_but_not_retrieved; expected=KKY; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KKY-10: status=present_but_not_retrieved; expected=KKY; matched_family=kanun; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- TUZUK-05: status=truly_missing_from_index; expected=TUZUK; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- UY-07: status=present_but_not_retrieved; expected=UY; matched_family=kanun; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- YON-01: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=teblig; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `29033` from `teblig` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-02: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `20237` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-05: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `23722` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-06: status=present_but_not_retrieved; expected=YONETMELIK; matched_family=kanun; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- YON-07: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=index_present; path=pre_rerank:1; owner=canonical_mapping; action=Fix source family mapping for `20435` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-08: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `13948` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.

## Interpretation
- `truly_missing_from_index`: no reliable canonical catalog/index match was found.
- `present_but_not_retrieved`: source exists in catalog/index but was absent from initial retrieval candidates.
- `present_but_family_misclassified`: source exists, but canonical family does not align with expected family.
- `visible_but_lost_after_retrieval`: source is visible before selection; next owner is selector/identity, not corpus acquisition.
