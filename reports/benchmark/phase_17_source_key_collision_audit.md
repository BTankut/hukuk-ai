# Phase 15C Source-Key Collision Remediation Plan

- collision_rows_in_corpus_backlog: 1
- permanent_fix: replace numeric-only runtime source-key joins with family-qualified canonical source keys.
- required_key_shape: `{source_family}:{canonical_identifier}:{canonical_title_hash_or_doc_uuid}` plus article/span ids.
- migration_rule: keep numeric `belge_no` as alias only; never use it alone for cross-family body materialization.
- validation_rule: fail corpus materialization when one numeric key resolves to multiple source families and the selected family has no non-title body span.

## Collision Rows
- CBKAR-08: family=CB_KARAR, pair=9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1, fix=family_aware_source_key_materialization
