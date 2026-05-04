# Phase 24P-R1 CBY-06 Materialization Plan

- generated_at_utc: `2026-05-04T13:15:53.527038+00:00`
- base_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- target_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06`
- live_8000_modified: `false`
- base_collection_overwrite: `false`
- qid_specific_runtime_branch: `false`

## Input Provenance

- official_url: `https://www.resmigazete.gov.tr/eskiler/2026/04/20260403-7.pdf`
- raw_file_path: `reports/benchmark/source_acquisition/phase_24P/raw/cby_06_rg_20260403_33213_karar_11153.pdf`
- raw_sha256: `ee7fb174b947cb3e0b56aec314fd553ad1c4a9edd80c1acd77f5ebde185577ae`
- normalized_ocr_path: `reports/benchmark/source_acquisition/phase_24P/normalized/cby_06_rg_20260403_33213_karar_11153_ocr_transcription.txt`
- normalized_ocr_sha256: `9ffabf7aa48476431298308b2bfd302d017704c8baf734bbfd20ee5c57656fe2`

## Planned Spans

| span | source_identifier | article | role |
|---|---|---|---|
| Karar 11153 amendment article | 11153 | m.1 | amendment metadata and added paragraph |
| Consolidated regulation added paragraph | 20046801 | m.11 | direct current m.11 evidence |

## Metadata Contract

Both rows preserve `CB_YONETMELIK` as raw family label, canonical `cb_yonetmelik` for runtime compatibility, `effective_state=amended/current`, `publication_date=2026-04-03`, `official_gazette_no=33213`, `decision_no=11153`, raw PDF SHA, and normalized OCR SHA.
