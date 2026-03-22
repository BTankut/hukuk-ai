# FAZ 2A Implementation Plan

**Date:** 2026-03-22  
**Reference:** `docs/FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-YOL-HARITASI-2026-03-22.md`  
**Intent:** turn the FAZ 2A planning document into a repo-native execution order with concrete artefacts, code touchpoints, and gates

## Executive Position

FAZ 2A is being executed as a retrieval/source-precision re-qualification phase, not as a new training wave.

Primary question:

> Can the system materially reduce `wrong source despite retrieved evidence` and `cross-law confusion` on the preserved family without hiding behind training or cutover rhetoric?

This implementation plan keeps the work ordered as:

1. freeze the failure set and measurement contract,
2. add retrieval/context trace so the next reruns become decision-grade,
3. repair query parsing, source selection, and evidence assembly one wave at a time,
4. only then rerun matched family eval and reopen steering.

## Current Repo Reality At Start

- preserved baseline and promoted candidate source-of-record reports already exist for `faz1-50`, `v2-95`, `v3-170`
- FAZ 1.5 steering already closed as `NO-GO - Retrieval/Coverage first`
- dominant failure classes on `v3-170` candidate:
  - `wrong source despite retrieved evidence`: `56`
  - `cross-law confusion`: `20`
  - `over-refusal`: `9`
  - `serving_error`: `5`
- current eval reports are sufficient for answer-level taxonomy
- current eval reports are not sufficient for parse/retrieval/context attribution because query/retrieval trace is not persisted

## Frozen Source Of Record

- baseline:
  - `evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
- candidate:
  - `evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_post_promotion_cleanup_20260322.json`
- taxonomy:
  - `evaluation/reports/faz1_5-category-breakdown-2026-03-22.md`
  - `evaluation/reports/faz1_5-category-breakdown-2026-03-22.json`

## Work Packages

### WP-1 — Failure Freeze and Diagnostic Subsets

Goal:
- turn the `v3-170` failures into a frozen, reproducible pack and split the first diagnostic subsets

Repo actions:
- publish failure freeze markdown:
  - `evaluation/reports/faz2a-failure-freeze-2026-03-22.md`
- publish failure pack:
  - `evaluation/reports/faz2a-failure-pack-v3-170-2026-03-22.jsonl`
- publish diagnostic subsets:
  - `configs/evaluation/test_questions_faz2a_tmk_cross_law_v3_30.json`
  - `configs/evaluation/test_questions_faz2a_tbk_critical_v3_61.json`

Exit:
- critical failures are frozen with stable issue labels and scope subsets

### WP-2 — Measurement Contract and Canonical Eval Family Labels

Goal:
- remove label drift and make future reports comparable by construction

Repo actions:
- freeze canonical labels:
  - `faz1-50`
  - `v2-95`
  - `v3-170`
- align:
  - `evaluation/report_metadata.py`
  - `scripts/run_eval_matrix.sh`
- publish:
  - `coordination/faz2a-measurement-contract-2026-03-22.md`

Exit:
- no new FAZ 2A artefact should emit `phase3-95` or `faz2-170` as the canonical family name

### WP-3 — Trace Instrumentation

Goal:
- persist enough runtime evidence to separate parse failure, retrieval failure, context contamination, and source-locking failure

Repo actions:
- add optional trace request/response plumbing to:
  - `api-gateway/src/routers/chat.py`
  - `evaluation/eval_runner.py`
  - `evaluation/metrics.py`
- include:
  - parsed query signals
  - retrieval query
  - top-k requested/effective
  - explicit article refs
  - pre-rerank candidates
  - post-rerank candidates
  - assembled context output
  - verification payload

Exit:
- the next diagnostic reruns can emit per-question trace without changing default live behavior

### WP-4 — Query Parsing and Retrieval Precision Wave

Goal:
- reduce wrong-law and wrong-article candidates before answer generation

Primary code touchpoints:
- `api-gateway/src/routers/chat.py`
- `api-gateway/src/rag/retriever.py`
- `api-gateway/src/rag/reranker.py`

Exit:
- top-k visibility and category-level source precision must improve on focus subsets before full-family reruns

### WP-5 — Evidence Assembly and Source-Locking Wave

Goal:
- tighten the answer to retrieved evidence rather than asking the model to behave better in the abstract

Primary code touchpoints:
- `api-gateway/src/rag/orchestrator.py`
- `api-gateway/src/rag/verification_engine.py`
- `api-gateway/src/guardrails/pipeline.py`
- `api-gateway/src/llm/client.py`

Exit:
- `wrong source despite retrieved evidence` must show a visible drop on focus subsets

### WP-6 — Targeted Coverage and Metadata Integrity

Goal:
- patch only the slices that are proven to be coverage or metadata defects

Exit:
- coverage claims must be supported by audit evidence, not used as a vague residual explanation

### WP-7 — Re-Qualification

Goal:
- rerun `faz1-50`, `v2-95`, `v3-170` only after a meaningful retrieval/source-precision delta exists

Exit:
- the next steering package must choose between pass, partial pass, or retrieval-closed/model-behavior next

## Code Touchpoint Map

Agent-assisted mapping confirmed the current live path as:

`chat.py` → `retriever.py` → `orchestrator.py` → `client.py` → `guardrails/pipeline.py` → `verification_engine.py`

This means:

- query parsing and deterministic retrieval boosts belong in `chat.py`
- candidate generation/filter semantics belong in `retriever.py`
- source-locking and context discipline belong in `orchestrator.py` and `verification_engine.py`
- prompt-level evidence discipline belongs in `client.py`

## Gate Discipline

FAZ 2A will not reopen a cutover claim unless:

- failure freeze exists
- measurement contract is explicit
- trace instrumentation exists
- focus-slice reruns show real signal
- full-family reruns show family-level support for the next steering claim

Until then, the valid state is active FAZ 2A execution, not cutover discussion.
