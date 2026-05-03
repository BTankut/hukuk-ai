# Phase 24J-R Span Interference Audit

- generated_at_utc: `2026-05-03T16:29:27.170454+00:00`
- new_span_count_classified: `17`
- guard_qids: `MULGA-01, MULGA-05, TEB-06`
- checked_top_k: `100`
- phase24j_new_span_top_k_hits: `0`
- status: `PASS`

## Finding

No Phase24J new span entered TARGET direct retrieval top100 for `MULGA-01`, `MULGA-05`, or `TEB-06`.

The regression is therefore not supported as span semantic interference. The evidence points to runtime binding/provenance or collection-load/selector-lane behavior.

## Per-Source Summary

| source_family | span_count | top100_hits |
|---|---:|---:|
| kanun | 4 | 0 |
| tuzuk | 2 | 0 |
| yonetmelik | 11 | 0 |

## Decision

Phase 24J-R-B status: `PASS`.
