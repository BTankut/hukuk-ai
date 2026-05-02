# Phase 23 Serving Config Separation Audit

Generated: 2026-05-02T20:21:54Z

Scope: controlled cutover readiness only. No live `8000` change was made.

## Decision

Phase 23 cutover, if later approved, must be treated as `benchmark_only` or `internal_eval` lane cutover. It is not a public serving cutover and it is not productization.

Public/normal serving remains closed until a separate serving policy audit defines and validates guardrails, verification, privacy, logging, trace exposure, manual review, and confidence threshold behavior.

## Observed Benchmark Candidate Config

Source: `reports/benchmark/runs/20260502T1858Z_phase22F_S7_full_shadow_benchmark/runtime_provenance.json`.

| Setting | Observed Value | Audit Interpretation |
|---|---|---|
| API URL | `http://127.0.0.1:8028/v1` | Shadow benchmark candidate |
| Lane | `phase22f_s7_full_shadow` | Internal benchmark lane |
| Model | `hukuk-ai-poc` | Gateway model alias |
| DGX model | `/models/merged_model_fabric_stage_20260321` | Fine-tuned merged model backend |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | Candidate retrieval corpus |
| Entity count | `349403` | Candidate corpus count |
| Vector dimension | `1024` | Expected embedding dimension |
| `GUARDRAILS_ENABLED` | `false` | Benchmark-only; not public serving policy |
| `USE_VERIFICATION` | `false` | Benchmark-only; not public serving policy |
| `PRESIDIO_ENABLED` | `false` | Benchmark-only; not public serving policy |
| `API_AUTH_ENABLED` | `false` | Acceptable for local shadow smoke only |
| `AUDIT_LOG_ENABLED` | `false` | Not acceptable as public serving default without separate decision |
| `SESSION_STORE_BACKEND` | `memory` | Local shadow only |
| `PARITY_TRACE_ENABLED` | `false` | Trace not emitted from candidate smoke lane |

## Observed Current Live Baseline

Source: live `8000` health/process probe captured in Phase 22F-S7 provenance and rechecked during Phase 23-A.

| Setting | Observed Value | Audit Interpretation |
|---|---|---|
| API URL | `http://127.0.0.1:8000/v1` | Current live binding |
| Lane | `current_serving_lane` | Current lane label |
| Model | `hukuk-ai-poc` | Gateway model alias |
| DGX model | `/models/merged_model_fabric_stage_20260321` | Fine-tuned merged model backend |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024` | Baseline corpus, not p0_backfill |
| Entity count | `349191` | Baseline corpus count |
| Guardrails | `disabled` | Current live is also not a finalized public-serving policy |
| Verification | `disabled` | Current live is also not a finalized public-serving policy |

## Required Serving Policy Decisions

These remain undecided and must not be inferred from benchmark success:

| Policy Area | Required Decision Before Public Serving |
|---|---|
| Guardrails policy | Whether `GUARDRAILS_ENABLED=true`, strict mode, input moderation, and latency limits are required |
| Verification policy | Whether verification is enabled, strict, advisory, or benchmark-disabled only |
| Presidio/privacy policy | Whether PII masking/anonymization is enabled for public traffic |
| Logging policy | Audit log enablement, retention, redaction, and access control |
| Trace exposure policy | Whether runtime trace is hidden, internal-only, or sampled |
| Manual review policy | Which risk classes route to lawyer/human review |
| Confidence threshold policy | When low-confidence answers are suppressed, hedged, or answered with caveats |
| Auth policy | Whether public/internal API requires API keys or gateway auth |
| Session store policy | Whether Redis-backed durable sessions are required |

## Cutover Scope

The only acceptable Phase 23 cutover scope is one of:

- `benchmark_only`
- `internal_eval`

`serving_candidate` is not accepted by this audit without a separate productization/serving policy gate.

## Non-Actions

- No live `8000` binding was changed.
- No productization was opened.
- No source acquisition, corpus materialization, model change, prompt change, or retrieval behavior change was made.

## Audit Result

Serving config separation: PASS for readiness documentation.

Operational gate remains closed: explicit approval and rollback plan are required before any live binding change, and public serving requires a separate serving policy audit.
