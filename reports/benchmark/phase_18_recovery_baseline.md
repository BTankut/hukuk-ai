# Phase 18 Recovery Baseline

## Decision

`Phase 18 Recovery Baseline` is accepted.

Live `8000` is bound to the full mevzuat corpus and remains the stable recovery baseline for the next behavior-preserving router decomposition phase.

## Baseline Commit And Runtime

- baseline_marker_created_at: `2026-04-26`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- latest_report_commit_before_marker: `89e51f4`
- live_full_run_git_sha: `ea3f6ad94591e008d53dc1c732c33e5efbb6a0c3`
- live_full_run: `reports/benchmark/runs/20260426T_phase18_recovery_A1_10_live_full100_retry`
- live_full_runtime_provenance: `reports/benchmark/runs/20260426T_phase18_recovery_A1_10_live_full100_retry/runtime_provenance.json`
- green_lane: `reports/benchmark/green_lane/20260426T_phase18_recovery_A1_10_live_full100_retry`
- cutover_decision: `reports/benchmark/phase_18_recovery_A1_10_cutover_decision.md`
- candidate_live_comparison: `reports/benchmark/phase_18_recovery_A1_10_directional_equivalence.md`

## Live Binding

```text
api_url=http://127.0.0.1:8000/v1
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
MILVUS_ENTITY_COUNT=349191
VECTOR_DIMENSION=1024
DGX_MODEL=/models/merged_model_fabric_stage_20260321
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

## A1.10 Gate Results

| Metric | Result | Gate | Status |
| --- | ---: | ---: | --- |
| raw_score_proxy | 756.61 | >= 735 | PASS |
| pass_proxy | 79/100 | >= 73 | PASS |
| wrong_family | 10 | <= 15 | PASS |
| wrong_document | 9 | <= 15 | PASS |
| hallucinated_identifier | 11 | <= 23 | PASS |
| unsupported_confident_claim | 0 | <= 8 | PASS |
| contract_valid | 100/100 | 100/100 | PASS |
| green_lane | pass | PASS | PASS |
| corpus_materialization_required_count | 2 | <= 6 | PASS |
| canonical_span_materialized_count | 98 | >= 90 | PASS |
| MULGA pass | 3/5 | >= 3/5 | PASS |
| YONETMELIK pass | 6/10 | >= 6/10 | PASS |
| UY pass | 10/10 | >= 9/10 | PASS |
| CB_GENELGE pass | 4/4 | >= 4/4 | PASS |

## Directional Candidate/Live Equivalence

| Metric | Candidate | Live | Live - Candidate | Gate | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| raw_score_proxy | 766.48 | 756.61 | -9.87 | >= -10 | PASS |
| pass_proxy | 80 | 79 | -1 | >= -2 | PASS |
| wrong_family | 11 | 10 | -1 | <= +2 | PASS |
| wrong_document | 12 | 9 | -3 | <= +2 | PASS |
| hallucinated_identifier | 16 | 11 | -5 | <= +3 | PASS |

## Repeatability And Trace Drift

- repeatability_probe: `reports/benchmark/phase_18_recovery_A1_10_repeatability_probe.md`
- repeatability_result: `PASS`
- candidate_repeat: exact on 20-QID smoke
- live_repeat: exact on 20-QID smoke
- selected_document_match: `100%`
- selected_article_match: `100%`
- trace_diff: `reports/benchmark/phase_18_recovery_A1_10_trace_ordering_diff.md`
- trace_drift_status: `bounded / non-blocking before decomposition`

## Source Hash Anchors

Complete source hash arrays are recorded in the runtime provenance JSON. Key anchors:

| Path | SHA-256 |
| --- | --- |
| `api-gateway/src/rag/source_catalog.py` | `f04dc600f306f5724c8e795fcf462bf601083e62250505686c3da55fb2a9016e` |
| `api-gateway/src/rag/retriever.py` | `d036bc2152af51a90689464af303009d822594076feb7a6a07ac93c7db74b20a` |
| `api-gateway/src/source_family_resolver.py` | `953ae5c81a4a90380884ec940373ca78ff35f74d91198039180dbb8171d1d58f` |
| `reports/benchmark/phase_05_canonical_source_catalog.csv` | `3e1a906ca1c0daaffc839b8757c6bdac25228d8f4e60f5001c2534a00fa309b2` |
| `api-gateway/src/rag/source_supplements.py` | `11d0c2f29d399957095958fd894c87f1d7cabc6fda1f1719a269a07cd30196ce` |

## Worktree State

The A1.10 runtime provenance records `dirty_worktree=True`. This is justified and bounded:

- A1.10 intended artifacts were committed and pushed before this baseline marker.
- The dirty state consists of pre-existing unrelated deleted/modified docs and historical untracked reports/artifacts.
- Those unrelated files are not part of the accepted recovery baseline and must not be staged or reverted as part of router decomposition.

## Freeze Rules

- Productization remains closed.
- Fine-tuning remains closed.
- No new retrieval, source routing, prompt, answer synthesis, slot-completion, or QID-specific logic may be added during router decomposition.
- The next phase is structural risk reduction only: behavior-preserving decomposition of `api-gateway/src/routers/chat.py`.
