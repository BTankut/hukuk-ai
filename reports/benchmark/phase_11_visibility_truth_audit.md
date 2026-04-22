# Phase 11A Source Visibility / Index Truth Audit

- source_run_dir: `reports/benchmark/runs/20260422T204628Z_phase11_full`
- rows_analyzed: 21

## Visibility Probe Status
- present_but_not_retrieved: 12
- present_but_family_misclassified: 6
- truly_missing_from_index: 3

## Owner Counts
- retrieval_routing: 12
- canonical_mapping: 6
- corpus_ingestion: 3

## Milvus Index Status
- index_present: 18
- not_checked: 3

## Expected Family Counts
- YONETMELIK: 5
- CB_KARAR: 4
- CB_YONETMELIK: 4
- KKY: 3
- KANUN: 2
- CB_GENELGE: 1
- TUZUK: 1
- UY: 1

## Open Rows
- CBG-01: status=truly_missing_from_index; expected=CB_GENELGE; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- CBKAR-01: status=present_but_not_retrieved; expected=CB_KARAR; matched_family=cb_karar; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBKAR-04: status=present_but_not_retrieved; expected=CB_KARAR; matched_family=cb_karar; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBKAR-05: status=present_but_not_retrieved; expected=CB_KARAR; matched_family=cb_karar; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBKAR-08: status=present_but_not_retrieved; expected=CB_KARAR; matched_family=cb_karar; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBY-01: status=truly_missing_from_index; expected=CB_YONETMELIK; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- CBY-04: status=present_but_family_misclassified; expected=CB_YONETMELIK; matched_family=kky; index=index_present; path=pre_rerank:12; owner=canonical_mapping; action=Fix source family mapping for `33899` from `kky` toward title-inferred `cb_yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- CBY-05: status=present_but_not_retrieved; expected=CB_YONETMELIK; matched_family=cb_yonetmelik; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- CBY-06: status=present_but_not_retrieved; expected=CB_YONETMELIK; matched_family=cb_yonetmelik; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KANUN-06: status=present_but_not_retrieved; expected=KANUN; matched_family=kanun; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KANUN-19: status=present_but_family_misclassified; expected=KANUN; matched_family=teblig; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `29033` from `teblig` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- KKY-02: status=present_but_not_retrieved; expected=KKY; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KKY-06: status=present_but_not_retrieved; expected=KKY; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Add retrieval path coverage via family bucket, metadata-first source lookup, or query expansion; source is catalog/index visible but absent from initial candidates.
- KKY-10: status=present_but_not_retrieved; expected=KKY; matched_family=kanun; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- TUZUK-05: status=truly_missing_from_index; expected=TUZUK; matched_family=none; index=not_checked; path=not_seen_in_run_trace; owner=corpus_ingestion; action=Acquire or reindex canonical source rows; no reliable catalog/index match was found.
- UY-07: status=present_but_not_retrieved; expected=UY; matched_family=kanun; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- YON-01: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=teblig; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `29033` from `teblig` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-02: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `20237` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-05: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `23722` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.
- YON-06: status=present_but_not_retrieved; expected=YONETMELIK; matched_family=kanun; index=index_present; path=not_seen_in_run_trace; owner=retrieval_routing; action=Matched expected companion source is catalog/index visible; primary-family retrieval still needs source coverage.
- YON-08: status=present_but_family_misclassified; expected=YONETMELIK; matched_family=kky; index=index_present; path=not_seen_in_run_trace; owner=canonical_mapping; action=Fix source family mapping for `13948` from `kky` toward title-inferred `yonetmelik` or update benchmark family expectation if audit confirms catalog is correct.

## Interpretation
- `truly_missing_from_index`: no reliable canonical catalog/index match was found.
- `present_but_not_retrieved`: source exists in catalog/index but was absent from initial retrieval candidates.
- `present_but_family_misclassified`: source exists, but canonical family does not align with expected family.
- `visible_but_lost_after_retrieval`: source is visible before selection; next owner is selector/identity, not corpus acquisition.
