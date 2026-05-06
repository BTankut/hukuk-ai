# Phase 24HR TEB-04 KDV GUT Materialization Report

- generated_at_utc: `2026-05-06T13:28:07.864279+00:00`
- status: `PASS`
- mode: `non_live_artifact_generation_only`
- qid_dependency: `TEB-04`
- source_title: `Katma Değer Vergisi Genel Uygulama Tebliği`
- source_identifier: `19631`
- gib_teblig_id: `9047`
- raw_file_path: `reports/benchmark/productization/human_legal_review_packet_20260506/attachments/kdv_genteb_2026_official_gib.pdf`
- raw_sha256: `bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68`
- normalized_text_path: `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/normalized/kdv_gut_2026_pdfkit_pages_001_055.txt`
- normalized_text_sha256: `092312f7d82c4511ffbb78b16cb2a29d59fb8f80e110b7950c38d0550eefe601`
- spans_jsonl: `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.jsonl`
- spans_csv: `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.csv`
- chunked_subspans_jsonl: `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.jsonl`
- chunked_subspans_csv: `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.csv`
- catalog_json: `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/catalog_delta/teb04_kdv_gut_catalog_delta.json`
- chunked_subspan_count: `59`
- max_chunked_subspan_length: `6410`
- live_8000_modified: `false`
- milvus_modified: `false`
- serving_candidate_created: `false`

## Materialized Spans

| locator | title | pdf pages | text length | span hash |
|---|---|---:|---:|---|
| `I/C-2.1.3` | Kısmi Tevkifat Uygulaması | 27-46 | 76818 | `fd43efde712e97cc8c863176e17e03296ed24608c45afd643c2722609b1871a6` |
| `I/C-2.1.5` | Tevkifata Tabi İşlemlerde KDV İadesi | 48-52 | 19379 | `59d63fe9ac1139f216acffa257f3bac2311ce393022de4a15b678edb170d99d0` |
| `I/C-2.1.5.2` | İade Uygulaması | 49-51 | 9228 | `d4653a3d448e8f967b545db04fc6bfd2296e7b6e5133bcdb09f50ae8e03542b9` |
| `I/C-2.1.5.2.1` | Mahsuben İade Talepleri | 49-50 | 5736 | `866fe878613a44697eaa2e6fbbd9c5d7fb7c17f30754f05e00ee8828888fde9a` |
| `I/C-2.1.5.2.2` | Nakden İade Talepleri | 50-51 | 3466 | `9861ac860185e4e11efcc7527ace77b70ed04601ccdc637a73c71380fec53730` |
| `I/C-2.1.5.3` | İade Uygulaması ile İlgili Diğer Hususlar | 51-52 | 5145 | `54817c9e49a96cd5a0e2005931b1c3607cfbf455b54f79f766b0e67ad6ecdae9` |

## Runtime Chunking Note

- `I/C-2.1.3` is larger than 65k characters as a full section; the chunked subspan file must be used for any runtime insertion to avoid truncation.
- Generated chunked subspans: `59`.
- Largest chunked subspan length: `6410`.

## Gate Impact

- TEB-04 official source acquisition and deterministic span extraction are now closed as non-live artifacts.
- This does not open productization by itself; the next step is a gated non-live retrieval/selector smoke using these spans.
- No question-specific runtime branch was introduced.
