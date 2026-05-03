# Phase 24J-R Regression Diagnostic Report

- generated_at_utc: `2026-05-03T16:29:27.171161+00:00`
- final_decision: `RERUN_WITH_NORMALIZED_PROVENANCE`
- productization_status: `CLOSED`
- fine_tuning_status: `CLOSED`

## Commit SHA List

| Commit | Scope |
|---|---|
| `1c90f69` | Audit Phase 24J critical retrieval diff |
| `e17e760` | Audit Phase 24J new span interference |
| `5a9fbf3` | Audit Phase 24J runtime provenance diff |
| `ff2dd13` | Design Phase 24J regression remediation |
| report commit | Report Phase 24J retrieval regression diagnostic |

## Critical Retrieval Diff Summary

Direct Milvus retrieval for BASE and TARGET is stable for `MULGA-01`, `MULGA-05`, and `TEB-06`. The TARGET runtime trace nevertheless has empty `rerank_list`, empty `assembled_evidence`, and no selected span for all three guard rows.

## Span Interference Audit Summary

All 17 Phase24J spans were classified. None appeared in TARGET direct top100 for the three guard rows. Span interference is not the supported root cause.

## Runtime Provenance Diff Summary

Material provenance differences beyond collection: `api_url, git_sha, gateway_health.lane, gateway_health.api_version`.

Catalog/config/source supplement hashes are equal in captured provenance, but API URL, `git_sha`, lane, API version, and collection differ.

## Root Cause

Most likely root cause: Phase 24J-D smoke was not a clean collection-only comparison. The candidate runtime produced no retrieval/selector evidence for guard rows despite the TARGET collection containing retrievable guard candidates. This points to runtime lane/provenance or collection-load/availability behavior, not LLM quality and not Phase24J span semantic interference.

## Recommended Next Phase

Open a narrow normalized-provenance rerun phase. Do not implement a filter, selector change, prompt change, or answer-synthesis change until BASE/TARGET are rerun under identical runtime provenance with explicit collection-load verification.

## Final Decisions

| Area | Decision |
|---|---|
| Productization | CLOSED |
| Fine-tuning | CLOSED |
| Internal eval | CLOSED |
| Phase24J shadow collection | Keep as diagnostic candidate only |
| Next action | Rerun with normalized provenance |

## Live 8000

Live `8000` was not modified by this diagnostic phase. Final health must be verified in terminal closeout.
