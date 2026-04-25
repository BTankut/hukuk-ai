# Repo Large File / Long File Audit for Planner

Date: 2026-04-25

Purpose: Identify files over 10K lines, separate code risk from generated/data artifacts, and define a safe planner-level remediation path.

## Executive Summary

Yes, some files over 10K lines exist. Most are not application code.

The main code-level abnormality is:

- `api-gateway/src/routers/chat.py` -> **14,514 lines**

That is not a healthy size for a runtime router/module. It is now acting as a mixed endpoint, retrieval planner, source selector, answer synthesizer, trace builder, guard/finalizer and benchmark adaptation surface. This should be split systemically before more benchmark hardening is added.

Large non-code files are mostly expected artifacts:

- tracked `evaluation/reports/**/*.json`
- primary source normalized legal text under `data/primary_sources/full_acquisition/**/normalized_source.txt`
- benchmark/catalog CSV outputs
- untracked `logs/traces/*.json`

These are normal as data/artifacts, but not all should live as tracked first-class repo files.

## Methodology

Commands used:

```bash
git ls-files -z | while IFS= read -r -d '' f; do
  if [ -f "$f" ]; then
    lines=$(wc -l < "$f" | tr -d ' ')
    printf '%s\t%s\n' "$lines" "$f"
  fi
done

git ls-files --others --exclude-standard -z | while IFS= read -r -d '' f; do
  if [ -f "$f" ]; then
    lines=$(wc -l < "$f" | tr -d ' ')
    printf '%s\t%s\n' "$lines" "$f"
  fi
done
```

Note: 3 tracked paths are currently deleted in the working tree and were excluded from line counts.

## Tracked Files Summary

| Metric | Value |
|---|---:|
| existing tracked files scanned | 3,454 |
| total tracked lines | 16,683,940 |
| tracked files over 10K lines | 166 |
| tracked files over 5K lines | 203 |
| deleted tracked paths excluded | 3 |

Tracked 10K+ category breakdown:

| Category | Count | Lines |
|---|---:|---:|
| evaluation reports | 157 | 15,685,331 |
| primary source legal text | 4 | 73,243 |
| coordination artifacts | 2 | 21,066 |
| benchmark catalog/report | 1 | 18,935 |
| fixture | 1 | 14,663 |
| api gateway code/test | 1 | 14,514 |

## Tracked Code Files Over Threshold

10K+ source-code files:

| File | Lines | Assessment |
|---|---:|---|
| `api-gateway/src/routers/chat.py` | 14,514 | Critical refactor candidate |

5K+ source-code/test files:

| File | Lines | Assessment |
|---|---:|---|
| `api-gateway/src/routers/chat.py` | 14,514 | Critical |
| `api-gateway/tests/test_chat_router.py` | 6,820 | Should be split after router split |

Largest functions inside `chat.py`:

| Start line | Length | Function |
|---:|---:|---|
| 13,004 | 1,463 | `async def chat_completions(...)` |
| 6,798 | 924 | `_build_precise_tbk_answer(...)` |
| 3,818 | 844 | `_select_article_span_evidence(...)` |
| 10,199 | 444 | `_build_trace_payload(...)` |
| 5,524 | 425 | `_rerank_chunks_by_source_identity(...)` |
| 12,633 | 371 | `_finalize_chat_response(...)` |

Additional structure:

- `chat.py` contains 312 function definitions and 6 classes.
- This is a clear module-boundary failure, not just a long endpoint file.

## Non-Code Tracked 10K+ Files

Important non-evaluation tracked 10K+ files:

| File | Lines | Assessment |
|---|---:|---|
| `data/primary_sources/full_acquisition/ttk/normalized_source.txt` | 33,628 | Acceptable corpus text |
| `reports/benchmark/phase_05_canonical_source_catalog.csv` | 18,935 | Generated/catalog artifact; review tracking policy |
| `data/primary_sources/full_acquisition/tmk_core_corpus/normalized_source.txt` | 16,282 | Acceptable corpus text |
| `api-gateway/src/data_pipeline/fixtures/tbk_detail.html` | 14,663 | Fixture; acceptable only if required by tests |
| `data/primary_sources/full_acquisition/ik/normalized_source.txt` | 13,054 | Acceptable corpus text |
| `coordination/faz30-reference-pack-2026-03-29.json` | 10,689 | Artifact; review tracking policy |
| `coordination/faz28-reference-pack-2026-03-28.json` | 10,377 | Artifact; review tracking policy |
| `data/primary_sources/full_acquisition/cmk/normalized_source.txt` | 10,279 | Acceptable corpus text |

## Untracked / Ignore-Visible Files

Untracked files visible to Git and not ignored:

| Metric | Value |
|---|---:|
| visible untracked files scanned | 3,928 |
| visible untracked files over 10K lines | 267 |
| visible untracked files over 5K lines | 1,485 |

Untracked 10K+ category breakdown:

| Category | Count | Lines |
|---|---:|---:|
| evaluation reports | 31 | 3,632,695 |
| logs/traces | 236 | 3,048,958 |

No untracked source-code file over 10K lines was found. The issue here is artifact/log hygiene, not code structure.

## Normal vs Abnormal

Normal or acceptable:

- Primary source normalized legal text can exceed 10K lines.
- Large evaluation JSON can exist as generated artifacts, but should be managed deliberately.
- Large fixtures can exist if they are stable and directly test-required.

Abnormal:

- Runtime application module over 10K lines: `api-gateway/src/routers/chat.py`.
- Test module approaching 7K lines: `api-gateway/tests/test_chat_router.py`.
- Large untracked logs/traces visible to Git; this increases status noise and accidental-add risk.
- Many very large tracked evaluation JSON reports; this makes clone/diff/search slower and obscures code review.

## Risk Assessment

`chat.py` risks:

- High regression probability because unrelated concerns share one file.
- High merge-conflict probability.
- Hard to enforce "no QID-specific fix" because benchmark adaptations and runtime logic are colocated.
- Slow code review and low test locality.
- Endpoint-level changes can accidentally alter retrieval, synthesis, trace and contract behavior at once.

Artifact/log risks:

- Repo size and grep/search cost are inflated.
- Generated reports can be mistaken for source of truth.
- Untracked logs/traces can be accidentally committed.
- Historical eval artifacts are not separated from active acceptance reports.

## Recommended Planner Tasks

### Phase L1: Guardrails and Policy

- Define thresholds: source code >3K warn, >5K refactor required, >10K critical.
- Add a CI/check script that reports long source files without failing initially.
- Add or tighten `.gitignore` for `logs/`, `logs/traces/`, and other local trace outputs.
- Document which report/artifact directories are allowed to be tracked.

### Phase L2: Split `chat.py` Without Behavior Change

Proposed module split:

- `routers/chat.py`: FastAPI route only, request/response wiring.
- `rag/retrieval_planning.py`: query planning, law/family hints, benchmark-neutral routing.
- `rag/source_identity.py`: metadata lookup, source-family selection, identity rerank.
- `rag/article_span_selection.py`: article/span selector and canonical span materialization.
- `rag/answer_slots.py`: required slot extraction and evidence-to-slot maps.
- `rag/answer_synthesis.py`: verified-slot answer plan and final answer synthesis.
- `rag/runtime_trace.py`: trace payload and parity trace assembly.
- `rag/source_supplements.py`: source supplement loading/materialization.

Rules:

- No behavior changes in the first split.
- Move code with import compatibility shims where needed.
- Keep tests green after each small move.
- Do not add QID-specific logic during the refactor.

### Phase L3: Split Router Tests

After `chat.py` is split:

- Move `test_chat_router.py` into focused test files matching new module boundaries.
- Keep a small endpoint integration test file.
- Preserve current coverage before adding new behavior.

### Phase L4: Artifact Hygiene

- Decide which `evaluation/reports/**/*.json` files are authoritative enough to track.
- Move old large eval JSON to ignored artifact storage, compressed archive, or Git LFS.
- Keep small markdown summaries and score summaries in Git.
- Add retention policy for local trace logs.

## Planner Decision Needed

Recommended immediate decision:

1. Open a behavior-preserving `chat.py` decomposition phase before new benchmark-hardening logic is added.
2. Treat artifact/log cleanup as a separate repo-hygiene phase.
3. Do not combine refactor with retrieval-quality changes.

This should reduce future regression risk without changing model/runtime behavior.
