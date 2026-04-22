# Phase 5 Canonical Source Catalog Audit

- source_records: 18934
- catalog_artifact: `reports/benchmark/phase_05_canonical_source_catalog.csv`

## Field Completeness
| field | missing |
| --- | ---: |
| source_family_canonical | 0 (0.0%) |
| canonical_title | 0 (0.0%) |
| canonical_title_normalized | 0 (0.0%) |
| canonical_identifier | 0 (0.0%) |
| canonical_identifier_type | 0 (0.0%) |
| issuer | 8264 (43.6%) |
| issuer_normalized | 8264 (43.6%) |
| official_gazette_no | 6 (0.0%) |
| official_gazette_date | 310 (1.6%) |
| effective_start | 310 (1.6%) |
| effective_end | 33 (0.2%) |
| effective_state | 0 (0.0%) |
| year_signals | 272 (1.4%) |
| alias_titles | 0 (0.0%) |
| cross_refs | 0 (0.0%) |

## Source Families
- uy: 5396
- teblig: 4732
- kky: 3658
- cb_karar: 3646
- kanun: 769
- khk: 173
- cb_yonetmelik: 168
- yonetmelik: 165
- tuzuk: 109
- cb_kararname: 51
- mulga_kanun: 47
- cb_genelge: 20

## Identifier Types
- rg_sayi: 9494
- teblig_no: 4732
- karar_sayisi: 3646
- kanun_no: 816
- khk_no: 173
- kararname_no: 51
- genelge_no: 20
- source_no: 2

## Interpretation
- This is a source-level canonical catalog, not a chunk-level retrieval trace.
- It supplies normalized title, identifier, issuer, temporal, alias, and cross-reference signals for metadata-first source identity selection.
- Remaining missing values should be treated as metadata backfill or source acquisition backlog, not prompt tuning work.
