# Phase 3 Index Metadata Audit

- milvus_uri: `http://127.0.0.1:19530`
- collection: `mevzuat_faz1_shadow_20260418_compat1024`
- collection_row_count: 349191
- scanned_rows: 349191
- max_rows: None

## Global Missing Field Coverage
- title: missing 349191 (100.0%)
- issuer: missing 349191 (100.0%)
- official_gazette_date: missing 37120 (10.6%)
- effective_start: missing 37120 (10.6%)
- effective_end: missing 7568 (2.2%)
- official_gazette_number: missing 62 (0.0%)
- family: missing 0 (0.0%)
- short_title: missing 0 (0.0%)
- identifier: missing 0 (0.0%)
- article: missing 0 (0.0%)
- section: missing 0 (0.0%)

## Family Row Counts
- uy: 109770
- kky: 109491
- teblig: 44013
- kanun: 41916
- mulga_kanun: 7560
- cb_yonetmelik: 7487
- tuzuk: 7192
- yonetmelik: 6768
- cb_kararname: 6370
- cb_karar: 6054
- khk: 2538
- cb_genelge: 32

## Highest Risk Metadata Gaps
- cb_genelge: title missing 100.0%
- cb_genelge: issuer missing 100.0%
- cb_karar: title missing 100.0%
- cb_karar: issuer missing 100.0%
- cb_kararname: title missing 100.0%
- cb_kararname: issuer missing 100.0%
- cb_kararname: official_gazette_date missing 92.1%
- cb_yonetmelik: title missing 100.0%
- cb_yonetmelik: issuer missing 100.0%
- kanun: title missing 100.0%
- kanun: issuer missing 100.0%
- khk: title missing 100.0%
- khk: issuer missing 100.0%
- kky: title missing 100.0%
- kky: issuer missing 100.0%
- mulga_kanun: title missing 100.0%
- mulga_kanun: issuer missing 100.0%
- teblig: title missing 100.0%
- teblig: issuer missing 100.0%
- tuzuk: title missing 100.0%
- tuzuk: issuer missing 100.0%
- uy: title missing 100.0%
- uy: issuer missing 100.0%
- yonetmelik: title missing 100.0%
- yonetmelik: issuer missing 100.0%

## Retrieval Hardening Implications
- Family and identifier metadata are broadly usable for source-family routing and exact identifier boosts.
- Missing full title/issuer fields limit issuer-aware tie-breakers for university/agency regulations until canonical enrichment is added.
- Active/repealed control should use `mulga` plus `yururluk_bitis`; rows with conflicting state are listed in the CSV.

## Metadata Keys Seen
```json
{
  "belge_kisa_adi": 349191,
  "belge_no": 349191,
  "belge_turu": 349191,
  "canonical_source_locator": 349191,
  "display_citation": 349191,
  "fikra_no": 349191,
  "kanun_kisa_adi": 349191,
  "kanun_no": 349191,
  "kind": 349191,
  "madde_no": 349191,
  "madde_no_int": 349191,
  "metin_sha256": 349191,
  "mulga": 349191,
  "resmi_gazete_sayi": 349191,
  "resmi_gazete_tarih": 349191,
  "shadow_embedding_method": 349191,
  "shadow_original_text_length": 349191,
  "shadow_primary_id": 349191,
  "shadow_row_ordinal": 349191,
  "shadow_text_length": 349191,
  "shadow_text_truncated": 349191,
  "source_id": 349191,
  "yururluk_baslangic": 349191,
  "yururluk_bitis": 349191
}
```
