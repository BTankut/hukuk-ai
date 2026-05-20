# FAZ 6 Repair Gate Decision Table

- trace_complete_rate: `1.0000`
- reconciliation_closed: `true`
- explained_ratio: `1.0000`
- dominant_reason: `citation_omission_with_correct_primary_present`
- dominant_count: `45`
- repair_gate_open: `true`
- next_official_move: `serializer-only citation recovery`
- rc_g_permitted: `true`

## Mapping

- `assembly_primary_miss` -> `retrieval/source-locking reopening`
- `canonical_normalization_mismatch` -> `evaluator-normalization closure`
- `citation_omission_with_correct_primary_present` -> `serializer-only citation recovery`
- `evaluator_alignment_mismatch` -> `evaluator-normalization closure`
- `guardrail_mode_drop` -> `guardrail mode-boundary recovery`
- `model_primary_selection_miss` -> `generator source-anchoring recovery`
- `post_generation_primary_flip` -> `source-selection immutability recovery`
- `retrieval_source_absent` -> `retrieval/source-locking reopening`
