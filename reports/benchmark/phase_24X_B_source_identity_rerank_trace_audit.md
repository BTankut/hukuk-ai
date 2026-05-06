# Phase 24X-B Source Identity Rerank Trace Audit

## Scope
- Rows: `KANUN-08`, `YON-05`.
- Input: `reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z/trace.jsonl`.
- No new benchmark execution, no scorer/key use, no live `8000` change.

## Interpretation
- `candidate_selected=true` means selected by the source identity reranker rank (`selected_document_rank_after_identity_rerank == 1`). Final answer assembly may later surface a different article from the same locked source family/key.
- `candidate_score_metadata=100` denotes `metadata_first_match=true`; it is not a separate calibrated model probability.
- `candidate_score_domain=-block` marks the candidate that Phase24X-C should block or demote from the primary-source pool under a default-off compatibility gate.

## Findings
- `KANUN-08`: source identity rerank sees only two regulation-family candidates; `24039` wins with a very large metadata-first score even though the sector-specific title is not supported by the user scenario. The expected TBK source is absent before rerank, so source identity can only prevent the bad primary lock and force fallback.
- `YON-05`: metadata lookup includes `23722`, but exact identifier narrowing selects `3194`/`5216` law candidates. Rerank then strongly rewards those law candidates through `metadata_first_match` and `family_match`; the expected regulation candidate never reaches final rerank.
- The recurring failure pattern is not answer synthesis. It is primary-source identity: metadata lookup and rerank treat support-law cues as primary identity cues.

## CSV
- `reports/benchmark/phase_24X_B_source_identity_rerank_trace_audit.csv`

## Candidate Summary
| qid | selected_identity_candidate | selected_filter_reason |
|---|---|---|
| KANUN-08 | `24039 m.0 / 24039 m.0/f.0` | domain_incompatible_title_only_primary; sector title terms are not query-supported |
| YON-05 | `3194 m.1 / 3194 m.37/f.0` | support_identifier_context; explicit law number is framed as insufficient and should not primary-lock |

## Filter Candidates
- `KANUN-08` `24039 m.0 | 24039 m.0/f.0`: domain_incompatible_title_only_primary; sector title terms are not query-supported
- `YON-05` `3194 m.1 | 3194 m.37/f.0`: support_identifier_context; explicit law number is framed as insufficient and should not primary-lock
- `YON-05` `3194 m.1 | 3194 m.8/f.0`: support_identifier_context; explicit law number is framed as insufficient and should not primary-lock
- `YON-05` `3194 m.1 | 3194 m.18/f.0`: support_identifier_context; explicit law number is framed as insufficient and should not primary-lock
- `YON-05` `3194 m.1 | 3194 m.8/f.0`: support_identifier_context; explicit law number is framed as insufficient and should not primary-lock
- `YON-05` `5216 m.1 | 5216 m.7/f.0`: regulation_requested; law-family candidate has no primary-source preservation rule
- `YON-05` `5216 m.1 | 5216 m.31/f.0`: regulation_requested; law-family candidate has no primary-source preservation rule
- `YON-05` `5216 m.1 | 5216 m.11/f.0`: regulation_requested; law-family candidate has no primary-source preservation rule
- `YON-05` `5216 m.1 | 5216 m.0/f.0`: regulation_requested; law-family candidate has no primary-source preservation rule

## Next
- Phase24X-C should design a default-off compatibility gate that protects primary-source selection without deleting supporting-source evidence.
