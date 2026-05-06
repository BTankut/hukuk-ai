# Post-Human-Review TEB-04 Materialization Update

Generated: 2026-05-06

## Decision
`TEB-04` official source acquisition and deterministic span extraction are closed as non-live artifacts.

This does not open internal eval, serving candidate, productization, live `8000`, Milvus write, model change, prompt change, or top-k change.

## Evidence
| item | value |
|---|---|
| Human review intake | `reports/benchmark/productization/human_legal_review_packet_20260506/intake/human_legal_review_intake_report.md` |
| Verified PDF | `reports/benchmark/productization/human_legal_review_packet_20260506/attachments/kdv_genteb_2026_official_gib.pdf` |
| PDF SHA-256 | `bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68` |
| Materialization script | `scripts/benchmark/phase24hr_teb04_kdv_gut_materialization.py` |
| Materialization report | `reports/benchmark/phase_24HR_teb04_kdv_gut_materialization_report.md` |
| Spans JSONL | `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.jsonl` |
| Spans CSV | `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.csv` |
| Chunked subspans JSONL | `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.jsonl` |
| Chunked subspans CSV | `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.csv` |
| Catalog delta | `reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/catalog_delta/teb04_kdv_gut_catalog_delta.json` |

## Materialized Locators
| locator | status |
|---|---|
| `I/C-2.1.3` | materialized from verified PDF |
| `I/C-2.1.5` | materialized from verified PDF |
| `I/C-2.1.5.2` | materialized from verified PDF |
| `I/C-2.1.5.2.1` | materialized from verified PDF |
| `I/C-2.1.5.2.2` | materialized from verified PDF |
| `I/C-2.1.5.3` | materialized from verified PDF |

## Remaining Gate
`TEB-04` remains blocked for serving/productization until a gated non-live retrieval/selector smoke proves the materialized spans are selected and answerable without regression.

`I/C-2.1.3` is 76,818 characters as a full section. The materialization script also produced 59 deterministic subheading chunks with max chunk length 6,410. Any runtime insertion should use the chunked subspan file rather than truncating the full section.
