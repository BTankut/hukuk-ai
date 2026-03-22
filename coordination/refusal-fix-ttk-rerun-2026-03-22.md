# Refusal Fix TTK Rerun

Date: 2026-03-22
Scope: fix the `TBK-019` out-of-scope refusal miss by extending deterministic scope refusal to `TTK`/`TCK`, then rerun full `faz1-50`
Decision: the refusal miss is fixed, but the run still fails Faz 1 because source precision remains just below threshold and hallucination rose on a few general-law questions

## Code Change

- `api-gateway/src/routers/chat.py`
  - deterministic scope refusal now covers:
    - `TTK`
    - `TCK`
- test coverage added:
  - `api-gateway/tests/test_chat_router.py`

## Verification

- targeted smoke:
  - `TTK uyarinca anonim sirket kurulus asgari sermayesi nedir?`
  - result: deterministic refusal
- targeted router tests:
  - `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
  - result: pass

## Full Rerun

Report:

- `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_refusal_fix_20260322.json`

Summary:

- citation: `79.6%`
- correct source: `68.6%`
- hallucination: `6.1%`
- refusal accuracy: `100.0%`
- avg response time: `16268 ms`
- error count: `1`

## Outcome

- `TBK-019` is fixed
- refusal accuracy recovered to `100%`
- citation and source metrics improved slightly versus the docker-refresh run
- but Faz 1 still fails narrowly:
  - citation short by `0.4pp`
  - correct source short by `1.4pp`

## New Risk Observed

The rerun surfaced new or worsened hallucination on general-law questions:

- `TBK-044`
- `TBK-045`
- `TBK-037`/`TBK-038` area drift during the run

Interpretation:

- the refusal fix is correct and should be kept
- the next blocker is no longer out-of-scope refusal
- the next blocker is article/source precision in the general-law cluster, especially the `TBK-044` family
