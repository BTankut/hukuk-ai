# FAZ 2A Wave 3 — Source-Lock Rerun

**Date:** 2026-03-22  
**Decision:** keep the source-lock fallback, because it materially repairs the no-citation / generic-wrapper class and raises source precision on both lanes; however FAZ 2A is still not requalified because `tmk_cross_law` hallucination remains above threshold and the candidate still does not clearly beat the fresh baseline.

## Scope

This wave targeted the post-retrieval answer path, not retrieval itself.

The main goals were:

1. stop upstream stringified/generic assistant blobs from leaking through unchanged
2. force a narrow source-locked fallback when the generated answer has no usable citation discipline

## Implemented

### 1. LLM output wrapper parsing

The LLM client now normalizes stringified upstream wrapper outputs before they reach the orchestrator:

- [client.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/llm/client.py)

This closes cases where the model lane returns content like:

- `response=[{'role': 'assistant', 'content': ...}] llm_output=None ...`

### 2. Source-lock fallback in orchestrator

The orchestrator now builds a narrow fallback from the top priority retrieved chunks when the generated answer is clearly untrustworthy for citation discipline:

- generic assistant-style blob
- no citations at all
- citations with zero overlap against the top priority retrieved chunk citations

Implementation:

- [orchestrator.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/rag/orchestrator.py)

The fallback is intentionally narrow:

- max `2` unique priority chunk citations
- direct chunk excerpting
- explicit `source_lock_fallback` reason tagging

### 3. Tests

Added/expanded coverage in:

- [test_llm_client.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/tests/test_llm_client.py)
- [test_orchestrator_smoke.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/tests/test_orchestrator_smoke.py)

Verified:

- `python3 -m py_compile api-gateway/src/llm/client.py api-gateway/src/rag/orchestrator.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_llm_client.py api-gateway/tests/test_orchestrator_smoke.py api-gateway/tests/test_chat_router.py -q`

## Fresh Source-Lock Lanes

- baseline lane: `127.0.0.1:8020 -> dgxnode2`
- candidate lane: `127.0.0.1:8022 -> dgx1 merged`

## Smoke Result

The earlier `TMK-CL-002` candidate failure class was explicitly rechecked.

Result:

- candidate now returns a source-locked cited answer instead of the earlier generic assistant blob
- citations: `TBK m.584`, `TMK m.185`
- reason tag: `source_lock_fallback`

## Fresh `tmk_cross_law` Reruns

### Baseline source-lock rerun

Report:

- [eval_diagnostic_faz2a_tmk_cross_law_20260322_174351.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_174351.json)

Summary:

- citation `100.0%`
- correct source `56.0%`
- hallucination `13.8%`
- refusal `100.0%`
- error `1`

Delta vs previous fresh baseline (`20260322_165259`):

- citation `80.0% -> 100.0%`
- correct source `46.9% -> 56.0%`
- hallucination `6.7% -> 13.8%`

### Candidate source-lock rerun

Report:

- [eval_diagnostic_faz2a_tmk_cross_law_20260322_175651.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_175651.json)

Summary:

- citation `100.0%`
- correct source `55.6%`
- hallucination `13.3%`
- refusal `100.0%`
- error `0`

Delta vs previous fresh candidate (`20260322_170327`):

- citation `93.1% -> 100.0%`
- correct source `46.6% -> 55.6%`
- hallucination `17.2% -> 13.3%`
- error `1 -> 0`

## Interpretation

### What this wave clearly fixed

- no-citation class is effectively closed on both lanes
- the `TMK-CL-002` generic-wrapper failure class is repaired
- source precision improved by roughly `+9` points on both lanes

### Why FAZ 2A still remains open

The candidate still does not materially outrun the fresh baseline:

- baseline correct source `56.0%`
- candidate correct source `55.6%`

And both lanes are still above the hallucination ceiling:

- baseline hallucination `13.8%`
- candidate hallucination `13.3%`

So this wave improved answer discipline, but it did not yet produce a requalified `tmk_cross_law` lane.

## Steering Outcome

This wave should be kept and built on; it is not a dead end.

But the next move should not be more retrieval expansion.

The next move should be a narrower post-answer precision wave:

1. make source-lock excerpts more query-aware and less over-inclusive
2. reduce hallucination on the still-bad cluster:
   - `TMK-CL-021`
   - `TMK-CL-022`
   - `TMK-CL-025`
   - `TMK-CL-026`
   - `TMK-CL-027`
3. then rerun `tmk_cross_law` again before touching `tbk_critical`
