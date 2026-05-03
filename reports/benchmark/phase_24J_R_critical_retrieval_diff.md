# Phase 24J-R Critical Retrieval Diff

- generated_at_utc: `2026-05-03T16:29:27.168018+00:00`
- base_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- target_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j`
- direct_top_k: `24`
- status: `PASS`

## Finding

Direct Milvus vector retrieval does not show Phase24J span interference for the three critical guard rows. The TARGET collection contains retrievable guard candidates, but the Phase 24J runtime trace has empty `rerank_list`, empty `assembled_evidence`, and no selector-selected span for each guard row.

This places the divergence before answer synthesis and after/around runtime retrieval binding, not in the LLM answer surface.

## Direct Top-K Equality

| qid | top24_exact_same_base_vs_target | phase24j_new_span_in_target_top24 | target_runtime_evidence_count | target_runtime_rerank_count |
|---|---:|---:|---:|---:|
| MULGA-01 | `True` | 0 | 0 | 0 |
| MULGA-05 | `True` | 0 | 0 | 0 |
| TEB-06 | `True` | 0 | 0 | 0 |

## Runtime Selector Divergence

| qid | BASE result | BASE selected span | TARGET result | TARGET selected span | Divergence point |
|---|---|---|---|---|---|
| MULGA-01 | PASS 8.37 | `YOK_DISIPLIN_2012 m.22/f.0` | FAIL 3.25 | `` | TARGET runtime retrieval/selector produced no evidence bundle |
| MULGA-05 | PASS 7.10 | `6570 m.GEC1/f.0` | FAIL 2.50 | `` | TARGET runtime retrieval/selector produced no evidence bundle |
| TEB-06 | PASS 8.90 | `23093 m.13/f.0` | FAIL 3.10 | `` | TARGET runtime retrieval/selector produced no evidence bundle |

## Decision

Phase 24J-R-A status: `PASS`.

The exact observed divergence is not that the 17 Phase24J spans outrank the old guard evidence. The direct collection diff is stable. The failure mode is that the Phase 24J candidate runtime did not build a retrieval/selector evidence bundle for the guard rows.
