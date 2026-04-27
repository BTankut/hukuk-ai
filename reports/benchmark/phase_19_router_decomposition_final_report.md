# Phase 19 Router Decomposition Final Report

Date: 2026-04-27

## Commit SHAs

- `bb1e824` - R7A router surface inventory
- `e0f93d6` - R7B safe unused router wrapper cleanup
- `652c25c` - R7C collision profile import cleanup
- `1d48a43` - R7D chat route shortcut orchestration extraction

## Created / Changed Surfaces

- No new runtime module was created in R7.
- Reports created:
  - `reports/benchmark/phase_19_R7_chat_router_surface_inventory.md`
  - `reports/benchmark/phase_19_R7B_safe_wrapper_cleanup_report.md`
  - `reports/benchmark/phase_19_R7C_import_cleanup_report.md`
  - `reports/benchmark/phase_19_R7D_route_boundary_report.md`
  - `reports/benchmark/phase_19_router_decomposition_final_report.md`

## Line Counts

```text
chat.py before Phase 19: not re-measured in R7; see Phase 19 earlier reports
chat.py after R6/R7A: 9718
chat.py after R7B: 9510
chat.py after R7D/R7E: 9538
test_chat_router.py before R7: 7226
test_chat_router.py after R7: 7226
chat_completions before R7D: 1570
chat_completions after R7D: 1270
```

The near-term `<5000` target was not realistic in R7 without higher-risk extraction of retrieval/orchestration blocks. R8 should continue with retrieval phase decomposition and broad-router test split.

## Helper Groups

Removed safe unused wrappers:

- 27 dead/duplicate wrappers across article/span, answer-slot, and answer-synthesis surfaces.

Moved imports away from `chat.py` where safe:

- `_source_key_collision_profile`
- `_source_key_v2_collision_profile`

Retained in `chat.py`:

- Runtime namespace wrappers required by `rag.article_span_selection`.
- Route-local source identity wrappers that preserve router-specific resolver behavior.
- RAG retrieval/orchestrator/finalization path.
- OpenAI-compatible response construction and streaming/non-streaming response path.

Extracted route-local boundaries:

- `_request_history_from_messages`
- `_prepare_chat_request_context`
- `_try_shortcut_chat_response`

## Test Split Status

- Small import split completed for source identity collision profiles.
- Full `test_chat_router.py` split remains open.
- Recommended R8 test split targets:
  - `test_source_identity.py`
  - `test_article_span_selection.py`
  - `test_answer_slots.py`
  - `test_answer_synthesis.py`
  - focused endpoint-only router tests

## Known Stale Tests

`test_chat_router.py -q` currently has 7 broad/stale expectation failures. These include:

- Source-family confidence expectations that no longer match current family prior behavior.
- Retrieval call-count assertions that conflict with current multi-lane retrieval.
- Native-dialog exact-content assertion that conflicts with current answer contract/synthesis surface.

These were not changed in R7 because R7 is behavior-preserving router slimming, not test expectation redesign.

## Smoke Results

R7B smoke:

```text
run_dir=reports/benchmark/runs/20260427T_phase19_R7B_wrapper_cleanup_smoke20_envparity
raw_score_proxy=140.23/200
pass_proxy=15/20
contract_valid=20/20
unsupported_confident_answer=0
source_key_v2_collision_detected_count=0
binding_source_key_collision_detected_count=0
critical_diff_vs_R6F=0
```

R7C smoke:

```text
run_dir=reports/benchmark/runs/20260427T_phase19_R7C_import_cleanup_smoke20_envparity
raw_score_proxy=140.23/200
pass_proxy=15/20
contract_valid=20/20
unsupported_confident_answer=0
critical_diff_vs_R7B=0
```

R7D smoke:

```text
run_dir=reports/benchmark/runs/20260427T_phase19_R7D_route_boundary_smoke20_envparity
raw_score_proxy=140.23/200
pass_proxy=15/20
contract_valid=20/20
unsupported_confident_answer=0
critical_diff_vs_R7C=0
```

## Full Benchmark Gate

R7E full run:

```text
run_dir=reports/benchmark/runs/20260427T_phase19_R7E_full_envparity
runtime_provenance_git_sha=1d48a4313bd725a656f08de892f09df9600ae6b8
DGX_MODEL=/models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
MILVUS_ENTITY_COUNT=349191
VECTOR_DIMENSION=1024
answered=100/100
errors=0
missing_trace=0
contract_valid=100/100
unsupported_confident_answer=0
raw_score_proxy=756.61/1000
pass_proxy=79/100
wrong_family=10
wrong_document=9
hallucinated_identifier=11
source_key_v2_collision_detected_count=0
binding_source_key_collision_detected_count=0
```

Family gates:

```text
CB_GENELGE=4/4
UY=10/10
MULGA=3/5
YONETMELIK=6/10
```

Delta vs A1.10 baseline `reports/benchmark/runs/20260426T_phase18_recovery_A1_10_live_full100_retry`:

```text
raw_score_proxy_delta=0.00
pass_proxy_delta=0
fail_proxy_delta=0
hallucinated_source_count_delta=0
unsupported_confident_answer_delta=0
answer_contract_invalid_delta=0
wrong_family_delta=0
wrong_document_delta=0
hallucinated_identifier_delta=0
```

Green lane:

```text
out_dir=reports/benchmark/green_lane/20260427T_phase19_R7E_full_envparity
status=PASS
answer_rows=100
trace_rows=100
runtime_provenance_present=True
provenance_missing_fields=[]
provenance_warning_fields=[]
```

## Decision

R7 is accepted. Router slimming/refactor preserved runtime behavior against smoke and full benchmark gates.

Phase 18 slot-completion redesign can be reopened as a separate brief.

Productization remains closed. Fine-tuning remains closed.

Recommended next engineering step: R8 retrieval/orchestration decomposition plus stale broad-router test split, still under behavior-preserving gates.
