# Phase 7A Visibility Probe

- tracker: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/phase_07_acquisition_tracker.csv`
- catalog: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/phase_05_canonical_source_catalog.csv`
- collection: `mevzuat_faz1_shadow_20260418_compat1024`
- top_k: 50
- rows: 18
- open_acquisition_or_reindex_rows: 1
- gold_document_not_retrieved_rows: 0

## Acceptance Signals
- needs_corpus_acquisition_open_rows_target_le_8: PASS (1/8)
- gold_document_not_retrieved_rows_phase6_baseline_6_target_le_3: PASS (0/3)
- every_open_row_has_owner_and_next_action: PASS

## Availability Status
- indexed_and_retrieval_visible: 13
- indexed_and_retrieval_visible_catalog_backfill_required: 4
- not_available_in_current_corpus: 1

## Resolution Status
- visibility_resolved_pending_benchmark_rerun: 13
- visibility_resolved_catalog_backfill_required: 4
- open_source_acquisition_required: 1

## Phase 7 Blocker Type
- visibility_resolved: 17
- not_retrieved_or_not_indexed: 1

## Family Counts
- YONETMELIK: 5
- CB_YONETMELIK: 4
- CB_KARAR: 3
- KANUN: 2
- KKY: 2
- UY: 1
- TUZUK: 1

## Open Rows
- TUZUK-05: status=open_source_acquisition_required; action=index_visibility_or_metadata_filter_repair; owner=needs_corpus_acquisition; next=acquire_primary_source_then_reindex; title=ilgili yürürlükteki tüzük hükümleri

## Visibility-Resolved Rows
- CBKAR-01: catalog=3350 [cb_karar]; title=İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350)
- CBKAR-05: catalog=8914391 [cb_karar]; title=TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARAR
- CBKAR-08: catalog=9903 [cb_karar]; title=YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903)
- CBY-04: catalog=33899 [kky]; title=DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK
- CBY-05: catalog=20046801 [cb_yonetmelik]; title=KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ
- CBY-06: catalog=20046801 [cb_yonetmelik]; title=KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ
- KANUN-06: catalog=TTK [kanun]; title=TÜRK TİCARET KANUNU
- YON-02: catalog=20237 [kky]; title=MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ
- YON-05: catalog=23722 [kky]; title=PLANLI ALANLAR İMAR YÖNETMELİĞİ
- YON-08: catalog=13948 [kky]; title=YÜKSEKÖĞRETİM KURUMLARINDA ÖNLİSANS VE LİSANS DÜZEYİNDEKİ PROGRAMLAR ARASINDA GEÇİŞ, ÇİFT ANADAL, YA
- UY-07: catalog=10498 [uy]; title=KOCAELİ ÜNİVERSİTESİ DEVLET KONSERVATUVARI ÖNLİSANS-LİSANS EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ
- KKY-02: catalog=38568 [kky]; title=BANKALARCA KULLANILACAK UZAKTAN KİMLİK TESPİTİ YÖNTEMLERİNE VE ELEKTRONİK ORTAMDA SÖZLEŞME İLİŞKİSİN
- KKY-10: catalog=24039 [kky]; title=ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN TÜKETİCİ HAKLARI YÖNETMELİĞİ

## Visibility-Resolved With Catalog Backfill
- CBY-01: status=visibility_resolved_catalog_backfill_required; next=backfill_source_catalog_metadata_then_rerun_benchmark; title=Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik
- KANUN-19: status=visibility_resolved_catalog_backfill_required; next=backfill_source_catalog_metadata_then_rerun_benchmark; title=7201 sayılı Tebligat Kanunu
- YON-01: status=visibility_resolved_catalog_backfill_required; next=backfill_source_catalog_metadata_then_rerun_benchmark; title=Elektronik Tebligat Yönetmeliği
- YON-06: status=visibility_resolved_catalog_backfill_required; next=backfill_source_catalog_metadata_then_rerun_benchmark; title=Konkordato Komiserliği Yönetmeliği

## Interpretation
- `indexed_and_retrieval_visible` can move out of corpus-acquisition ownership after the next benchmark rerun.
- `indexed_and_retrieval_visible_catalog_backfill_required` means live retrieval can see the source, but the source-level catalog needs metadata alignment.
- `indexed_but_dense_retrieval_gap` means the source exists in catalog/scalar probes but current dense retrieval still misses it.
- `catalog_only_not_indexed` requires reindexing from the canonical article source into the serving Milvus collection.
- `not_available_in_current_corpus` remains a real source acquisition or parser coverage gap.
