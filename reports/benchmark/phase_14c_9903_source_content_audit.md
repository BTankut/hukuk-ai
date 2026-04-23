# Phase 14C-A Source Content Audit: 9903

- generated_at: `2026-04-23T20:37:26.119016+00:00`
- identifier: `9903`
- article_rows_path: `/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl`
- article_rows_hit_count: `4`
- milvus_status: `ok`
- milvus_hit_count: `4`
- source_key_collision_detected: `True`
- cb_karar_real_body_span_count: `0`
- corpus_materialization_required: `True`

## Corpus Truth Table

| source | family | article | title_only | body_available | body_len | control_count | effective | title |
|---|---|---:|---:|---:|---:|---:|---|---|
| 9903:9903:m0:f0:from2025-05-30:to9999-12-31 | cb_karar | 0 | True | False | 197 | 159 | active | YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903) |
| 9903:9903:m1:f0:from2006-02-10:to9999-12-31 | teblig | 1 | False | True | 384 | 0 | active | GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ (TEBLİĞ NO: TRKGM-2006/1) |
| 9903:9903:m2:f0:from2006-02-10:to9999-12-31 | teblig | 2 | False | True | 53 | 0 | active | GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ (TEBLİĞ NO: TRKGM-2006/1) |
| 9903:9903:m3:f0:from2006-02-10:to9999-12-31 | teblig | 3 | False | True | 65 | 0 | active | GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ (TEBLİĞ NO: TRKGM-2006/1) |

## Source-Key Collision

| source_key | collision | family | article | body_available | title |
|---|---:|---|---:|---:|---|
| 9903 | True | cb_karar | 0 | False | YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR (KARAR SAYISI: 9903) |
| 9903 | True | teblig | 1 | True | GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ (TEBLİĞ NO: TRKGM-2006/1) |
| 9903 | True | teblig | 2 | True | GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ (TEBLİĞ NO: TRKGM-2006/1) |
| 9903 | True | teblig | 3 | True | GARANTİ BELGESİ SÜRELERİNİN UZATILMASINA İLİŞKİN TEBLİĞ (TEBLİĞ NO: TRKGM-2006/1) |

## Finding

The selected source identity is present, but the canonical `cb_karar` source has no selectable non-title body span in the current corpus/index. The only `cb_karar` row for `9903` is `m.0`; its body is non-text/control-character content from the PDF extraction path. Rows `m.1`-`m.3` under the same numeric key are a different `teblig`, so they must not be materialized as `CB_KARAR 9903` support.

Runtime implication: Phase 14C-B/C should expose this as `corpus_materialization_required` and degrade title-only answers instead of treating `m.0` as sufficient legal support.
