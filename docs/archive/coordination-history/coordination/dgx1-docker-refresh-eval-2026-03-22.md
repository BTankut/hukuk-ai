# DGX1 Docker Refresh Eval

Date: 2026-03-22
Scope: rerun the full `faz1-50` post-train eval from scratch after the `dgx1` inference docker was changed
Decision: the docker refresh fixed the sustained-load serving failure, but the lane still misses Faz 1 by a narrow quality margin

## Runtime State

Verified before eval:

- local candidate gateway: `127.0.0.1:8004`
- tunneled upstream: `127.0.0.1:30004 -> dgx1:30000`
- model: `/models/merged_model_fabric_stage_20260321`

Short smoke before full run:

- `TBK m.49` → PASS
- `TBK m.586` → PASS
- `manevi tazminat` query → answered, but still showed source over-expansion

## Full Faz 1 Rerun

Report:

- `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_docker_refresh_20260322.json`

Summary:

- citation: `78.0%`
- correct source: `68.2%`
- hallucination: `2.0%`
- refusal accuracy: `98.0%`
- avg response time: `16696 ms`
- error count: `0`

Gate status:

- citation gate: fail
- correct source gate: fail
- hallucination gate: pass
- refusal gate: pass
- overall: fail

## What Changed vs. Previous Stable Rerun

Compared with:

- `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_stable_20260321.json`

Delta:

- error count: `16 -> 0` (major improvement)
- citation: `76.5% -> 78.0%`
- correct source: `68.4% -> 68.2%` (essentially flat)
- hallucination: `0.0% -> 2.0%`
- refusal: `100.0% -> 98.0%`
- avg response: `15593 ms -> 16696 ms`

Interpretation:

- the docker refresh solved the long-run connection collapse
- the remaining blocker is no longer serving stability
- the remaining blocker is source precision / refusal quality staying slightly below the formal Faz 1 bar

## Most Visible Quality Misses

- one refusal miss remained:
  - `TBK-019`
- one hallucination remained:
  - `TBK-044`
- narrow source-precision misses still concentrate in:
  - `tbk_genel`
  - `tbk_kira`
  - `tbk_vekaletname`
  - `tbk_satis`
  - `tbk_kefalet`

## Conclusion

- `dgx1` serving is now stable enough for a full 50-question run
- this closes the earlier "connection error wave" blocker
- but the lane still cannot be promoted because it remains just below the Faz 1 citation / source thresholds

## Next Step

1. treat serving stability as recovered
2. shift back to prompt/retrieval/guardrails precision work
3. target the narrow quality misses rather than infra recovery
