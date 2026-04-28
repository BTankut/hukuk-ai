# Hukuk-AI Phase 19 R8-D Evidence Bundle Fixture

Date: 2026-04-28

Purpose: pre-change fixture for behavior-preserving evidence bundle extraction.

Run directory: `reports/benchmark/runs/20260428T_phase19_R8C_fixture_post_envparity`
Trace source: `reports/benchmark/runs/20260428T_phase19_R8C_fixture_post_envparity/trace.jsonl`

Fixture QIDs:
- `CBG-01`
- `MULGA-02`
- `CBKAR-08`
- `YON-01`
- `KANUN-01`
- `TEB-01`
- `UY-07`
- `KKY-10`

Captured fields:

- `selected_context_sources`: source identifiers in assembled evidence order.
- `selected_chunk_ids`: chunk/citation/span ids in assembled evidence order.
- `citation_labels`: `context_chunk_citations` from trace context assembly.
- `context_order`: 1-based evidence order.
- `context_text_hashes`: first 16 hex chars of SHA-256 over each evidence excerpt/text.
- `evidence_bundle_hash`: first 16 hex chars of SHA-256 over stable JSON of assembled evidence.

CSV:

`reports/benchmark/phase_19_R8D_evidence_bundle_fixture.csv`

Baseline metrics for source run:

- total: 8
- answered: 8
- errors: 0
- missing_trace: 0
- contract_valid: 8/8
- unsupported_confident_answer: 0
- raw_score_proxy: 59.33 / 80
- pass_proxy: 6/8

R8-D acceptance use:

After moving evidence bundle helpers, regenerate this CSV from a post-change fixture run. Required material diff: `0`.
