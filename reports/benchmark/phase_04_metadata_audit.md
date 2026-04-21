# Phase 4 Metadata Enrichment Audit

- milvus_uri: `http://127.0.0.1:19530`
- collection: `mevzuat_faz1_shadow_20260418_compat1024`
- collection_row_count: 349191
- scanned_rows: 349191
- max_rows: None

## Global Raw vs Enriched Coverage
| field | raw missing | enriched missing | recovered by runtime catalog |
| --- | ---: | ---: | ---: |
| full_title | 349191 (100.0%) | 0 (0.0%) | 349191 |
| issuer | 349191 (100.0%) | 153793 (44.0%) | 195398 |
| official_gazette_no | 62 (0.0%) | 62 (0.0%) | 0 |
| official_gazette_date | 37120 (10.6%) | 37120 (10.6%) | 0 |
| effective_start | 37120 (10.6%) | 37120 (10.6%) | 0 |
| effective_end | 7568 (2.2%) | 7568 (2.2%) | 0 |
| canonical_identifier_display | 0 (0.0%) | 0 (0.0%) | 0 |
| source_family_canonical | 0 (0.0%) | 0 (0.0%) | 0 |
| effective_state | 349191 (100.0%) | 0 (0.0%) | 349191 |

## Family Row Counts
- uy: 109822
- kky: 109392
- teblig: 43912
- kanun: 38601
- cb_yonetmelik: 7537
- mulga_kanun: 7451
- tuzuk: 7197
- yonetmelik: 6718
- cb_kararname: 6575
- cb_karar: 6036
- khk: 5917
- cb_genelge: 33

## Interpretation
- This report measures runtime enrichment, not a destructive Milvus reindex.
- Fields still missing after enrichment are corpus/source-acquisition or deeper canonical metadata backlog.
- Retrieval and verification code should prefer enriched canonical fields before raw aliases.
