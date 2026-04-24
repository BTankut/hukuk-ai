# Phase 15C Source-Key Collision Remediation Plan

- collision_rows_in_corpus_backlog: 3
- permanent_fix: replace numeric-only runtime source-key joins with family-qualified canonical source keys.
- required_key_shape: `{source_family}:{canonical_identifier}:{canonical_title_hash_or_doc_uuid}` plus article/span ids.
- migration_rule: keep numeric `belge_no` as alias only; never use it alone for cross-family body materialization.
- validation_rule: fail corpus materialization when one numeric key resolves to multiple source families and the selected family has no non-title body span.

## Collision Rows
- CBG-02: family=CB_GENELGE, pair=26=cb_genelge:yurt disinda yurutulen faaliyetlerde dikkat edilmesi gereken hususlar ile ilgili|cb_karar:4 7 1956 tarihli ve 6772 sayili kanun kapsamina giren kurumlarda calisan isciler; 29=cb_genelge:ulusal akilli sehirler stratejisi ve eylem plani ile ilgili|cb_karar:turkakim kara kismi 2 gaz boru hatti projesi kapsaminda tekirdag ve kirklareli i, fix=family_aware_source_key_materialization
- CBG-04: family=CB_GENELGE, pair=3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:ust kademe kamu yoneticilerinin atanmalarina iliskin usul ve esaslar ile kamu ku, fix=family_aware_source_key_materialization
- CBKAR-08: family=CB_KARAR, pair=9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1, fix=family_aware_source_key_materialization
