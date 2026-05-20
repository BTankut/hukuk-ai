# FAZ 2A Wave 2 — Turkish Normalization + Concept Anchor Rerun

**Date:** 2026-03-22  
**Decision:** keep the centralized Turkish normalization and exact-anchor retrieval hooks, but do **not** declare retrieval requalification on `tmk_cross_law`; the next wave should pivot to source-locking / answer-discipline rather than adding more lexical anchors.

## Scope

This wave closed two gaps left open after FAZ 2A wave 1:

1. stop treating Turkish spelling variants as ad hoc router exceptions
2. rerun the `tmk_cross_law` diagnostic subset on fresh matched baseline/candidate lanes with trace enabled

## Implemented

### 1. Centralized Turkish normalization

Router matching no longer depends on repeatedly listing Turkish spelling variants inline.

Added:

- centralized normalization helper in [api-gateway/src/routers/chat.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/routers/chat.py)
- normalized law-name matching
- normalized boundary-safe query-term matching

This specifically closed the earlier false-positive pattern where `gerçekte` could trip the naive `çek`/`TTK` path.

### 2. Concept-anchor exact article forcing

Low-risk concept bundles now force exact article retrieval for narrow cross-law slices such as:

- aile konutu + kira/fesih
- kefalet + eş rızası
- malik olmayan + kira
- mal rejimi + borç/sözleşme
- haksız fiil + TMK m.174
- muris muvazaası
- eşin rızası + geçersizlik

Trace now carries:

- `forced_article_refs`
- normalized `applied_expansions`

### 3. Cascade risk removed

Agent review correctly flagged that concept-anchor rules were matching against the mutated `retrieval_query`, which could cascade later rules and create false positives.

That is now fixed:

- anchor rules evaluate against the original user query
- duplicate expansions are deduped before they enter the retrieval query

## Verification

- `python3 -m py_compile api-gateway/src/routers/chat.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
- added negative coverage for:
  - no duplicate expansion injection on the muris muvazaası path
  - no irrelevant exact-article forcing on a kefalet/eş rızası query

## Fresh Matched Lanes

- baseline lane: `127.0.0.1:8018 -> dgxnode2`
- candidate lane: `127.0.0.1:8019 -> dgx1 merged`

Both lanes were relaunched fresh after the normalization refactor and verified with `/v1/health`.

## Fresh `tmk_cross_law` Results

### Baseline fresh rerun

Report:

- [eval_diagnostic_faz2a_tmk_cross_law_20260322_165259.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_165259.json)

Summary:

- citation `80.0%`
- correct source `46.9%`
- hallucination `6.7%`
- refusal `96.7%`
- error `0`

### Candidate fresh rerun

Report:

- [eval_diagnostic_faz2a_tmk_cross_law_20260322_170327.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_170327.json)

Summary:

- citation `93.1%`
- correct source `46.6%`
- hallucination `17.2%`
- refusal `100.0%`
- error `1` (`TMK-CL-015` timeout)

## Interpretation

### What improved

Relative to the earlier post-fix candidate diagnostic (`20260322_162725`):

- correct source `44.4% -> 46.6%`
- hallucination `20.0% -> 17.2%`
- refusal `96.7% -> 100.0%`

So the normalization and exact-anchor wave is directionally useful.

### What did not improve enough

Against the **fresh baseline on the same wave**, the candidate is still not meaningfully ahead:

- citation `80.0% -> 93.1%` better
- correct source `46.9% -> 46.6%` slightly worse
- hallucination `6.7% -> 17.2%` materially worse
- latency `20.0s -> 24.4s` worse

This means the wave improved retrieval access to expected articles, but the candidate model still fails to consistently convert that context into disciplined source selection.

### Candidate-specific failure signals

The fresh candidate report shows issues that are no longer best explained by retrieval alone:

- `TMK-CL-002` returned a generic assistant-style blob despite having `TBK m.584` and `TMK m.185` in context
- `TMK-CL-015` timed out
- hallucination-heavy failures remain on:
  - `TMK-CL-005`
  - `TMK-CL-010`
  - `TMK-CL-021`
  - `TMK-CL-025`
  - `TMK-CL-026`

## Steering Outcome

This wave closes the router-side Turkish matching concern and proves that the system no longer depends on patch-by-patch Turkish keyword additions.

However, the FAZ 2A blocker is no longer primarily:

- Turkish spelling variance
- missing lexical boosts
- missing exact-article retrieval hooks

The dominant blocker is now:

- wrong source despite retrieved evidence
- unstable answer discipline on the candidate lane
- source-locking / citation-selection failure

## Next Correct Step

Do **not** spend the next wave adding more Turkish spelling variants or more lexical/article expansions first.

Next wave should target:

1. source-locking / cited-source discipline in the post-retrieval answer path
2. sanitizing bad upstream assistant-wrapper outputs like the `TMK-CL-002` blob
3. only after that, a new matched rerun on `tmk_cross_law`
