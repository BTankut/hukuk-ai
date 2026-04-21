# Phase 4 Verification-First Final Summary

## 1. Scope

Phase 4 implemented verification-first hardening on top of Phase 3 retrieval routing:

- Runtime metadata enrichment for canonical title, issuer, official gazette, effective dates, canonical identifier, family, and effective state.
- Article/span-aware evidence selection and richer evidence serialization.
- Same-evidence verification between claimed source and selected evidence.
- Evidence-grounded fallback behavior for weak source-lock paths.
- Coverage/source-selection backlog separation for failures that should not be hidden with question-specific prompt fixes.

## 2. Commits

- `6b3d9db` - `gateway: add phase 4 metadata enrichment groundwork`
- `50d96eb` - `gateway: add article span evidence selector`
- `3c9fee3` - `gateway: add same-evidence verification gate`
- Final reporting/routing commit - includes general source-family prior hardening, coverage backlog report, v4 run scoring, and final Phase 4 summary.

## 3. Runtime Binding

- API gateway: `http://127.0.0.1:8000/v1`
- Gateway session: `hukuk_phase4_gateway`
- Model exposed to benchmark: `hukuk-ai-poc`
- DGX model binding: `/models/merged_model_fabric_stage_20260321`
- DGX base URL: `http://192.168.12.243:30000/v1`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Embedding backend: `intfloat/multilingual-e5-large-instruct`, dimension `1024`

## 4. Final Run

- Run directory: `reports/benchmark/runs/20260421T211914Z_phase4_verification_first_final_v4`
- Answered: `100/100`
- Refused or empty: `0`
- API errors: `0`
- Trace rows: `100`
- Contract valid: `100/100`
- Green lane: `pass`

## 5. Score Comparison

| metric | Phase 3 final | Phase 4 v4 | delta |
| --- | ---: | ---: | ---: |
| raw_score_proxy | 658.94 | 640.88 | -18.06 |
| average_score_0_10_proxy | 6.59 | 6.41 | -0.18 |
| pass_proxy | 56 | 48 | -8 |
| unsupported_confident_claim | 49 | 33 | -16 |
| hallucinated_identifier | 46 | 51 | +5 |
| hallucinated_source_count | 23 | 22 | -1 |
| wrong_family | 34 | 38 | +4 |
| wrong_document | 23 | 22 | -1 |
| wrong_article | 3 | 3 | 0 |
| missing_required_content_signal | 98 | 97 | -1 |
| partial_grounding_only | 98 | 97 | -1 |
| repealed_source_used_as_active | 5 | 5 | 0 |

## 6. Forensics Comparison

| mechanism | Phase 3 final | Phase 4 v4 | delta |
| --- | ---: | ---: | ---: |
| right-document wrong-article/span | 36 | 30 | -6 |
| evidence insufficiency | 16 | 15 | -1 |
| generation overreach | 16 | 22 | +6 |
| wrong-family retrieval | 13 | 12 | -1 |
| right-family wrong-document | 12 | 13 | +1 |
| temporal_miss | 5 | 5 | 0 |

## 7. Metadata Audit

- Collection rows scanned: `349191`
- `full_title`: raw missing `100.0%`, runtime-enriched missing `0.0%`
- `issuer`: raw missing `100.0%`, runtime-enriched missing `44.0%`
- `official_gazette_date` and `effective_start`: missing `10.6%`
- `effective_end`: missing `2.2%`
- `canonical_identifier_display`, `source_family_canonical`, `effective_state`: runtime surface complete

Interpretation: runtime enrichment fixed title/effective-state visibility, but issuer and official-gazette/effective-date gaps remain corpus/canonical metadata backlog.

## 8. Coverage Backlog

- Rows analyzed: `100`
- Failing rows: `97`
- Needs corpus acquisition: `18`
- Needs metadata enrichment: `53`

Coverage status counts:

- `right_doc_wrong_article_or_span`: `74`
- `not_retrieved_or_not_indexed`: `12`
- `gold_document_not_retrieved`: `6`
- `temporal_state_gap`: `5`
- `not_backlog`: `3`

## 9. Acceptance Result

Phase 4 is not fully accepted against the proposed numeric targets.

Passed criteria:

- Green lane stayed green.
- Contract validity stayed `100/100`.
- Metadata audit was produced.
- Coverage backlog was produced.
- Final scoring and forensics were produced.
- `unsupported_confident_claim` improved materially from `49` to `33`.
- `right-document wrong-article/span` improved from `36` to `30`.

Failed or incomplete criteria:

- `unsupported_confident_claim` did not reach target `<=30`.
- `hallucinated_identifier` regressed from `46` to `51`, target was `<=25`.
- `wrong_family` regressed from `34` to `38`, target was `<=20`.
- `wrong_document` improved only from `23` to `22`, target was `<=15`.
- `missing_required_content_signal` and `partial_grounding_only` stayed effectively flat at `97`.
- Dominant `right-document wrong-article/span` improved but did not reach target `<=20`.

## 10. Residual Technical Diagnosis

The main remaining blocker is not answer-contract shape. It is source/evidence selection quality:

- General natural-language questions still retrieve semantically similar but legally wrong neighboring sources.
- Some expected documents are absent from initial retrieval or indistinguishable without stronger title/issuer/year metadata.
- Article/span selection improves the dominant cluster but still lets weak topical overlap outrank exact legal-document identity.
- Same-evidence verification lowers confidence/manual-review behavior but does not by itself recover the correct source when retrieval candidates are wrong.

Next work should prioritize corpus-aware source identity selection and metadata-first candidate generation before any question-specific tuning.

## 11. Generated Artifacts

- `reports/benchmark/phase_04_metadata_audit.md`
- `reports/benchmark/phase_04_metadata_audit.csv`
- `reports/benchmark/phase_04_trace_forensics.md`
- `reports/benchmark/phase_04_failure_clusters.csv`
- `reports/benchmark/phase_04_coverage_backlog.md`
- `reports/benchmark/phase_04_coverage_backlog.csv`
- `reports/benchmark/phase_04_scored.csv`
- `reports/benchmark/runs/20260421T211914Z_phase4_verification_first_final_v4/score_summary.md`
- `reports/benchmark/runs/20260421T211914Z_phase4_verification_first_final_v4/scored.csv`

## 12. Verification Commands

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/source_family_resolver.py api-gateway/src/answer_contract_v2.py api-gateway/src/rag/orchestrator.py scripts/benchmark/phase4_metadata_audit.py scripts/benchmark/phase4_coverage_backlog.py`
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py api-gateway/tests/test_answer_contract_v2.py api-gateway/tests/test_orchestrator_smoke.py api-gateway/tests/test_source_catalog.py -q`
- `scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260421T211914Z_phase4_verification_first_final_v4`
