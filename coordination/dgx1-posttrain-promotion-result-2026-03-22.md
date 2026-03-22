# DGX1 Post-Train Promotion Result

Date: 2026-03-22
Scope: freeze the strongest matched `dgx1` merged-model post-train result for the current `807` candidate and compare it against the frozen Faz 1 baseline contract
Decision: the `dgx1` merged lane is now the official post-train promotion artefact for the current Qwen3.5 candidate; it clears the formal promotion contract and also materially improves the live serving picture

## Candidate Identity

- model ref: `hukuk_ai_sft_qwen35_807`
- checkpoint ref: `dgx1_merged_8010_post_promotion_cleanup`
- raw report role: `post_train`
- eval family: `faz1-50`
- runner: `eval_runner`

## Evaluation Lineage

### 1) Docker refresh rerun - stable infra, still below gate

- raw report:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_docker_refresh_20260322.json`
- summary:
  - citation `78.0%`
  - correct source `68.2%`
  - hallucination `2.0%`
  - refusal `100.0%`
  - avg response `16696 ms`

### 2) Precision-fix rerun - first gate-passing dgx1 artefact

- raw report:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_precision_fix_20260322.json`
- evidence manifest:
  - `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_precision_fix_20260322.json`
- summary:
  - citation `86.0%`
  - correct source `82.0%`
  - hallucination `2.0%`
  - refusal `100.0%`
  - avg response `10172.4 ms`

### 3) Post-promotion cleanup rerun - current official artefact

- raw report:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`
- evidence manifest:
  - `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`
- train package sha:
  - `1139008106af2bc655246b878d2dbc78bc6bad6a2e732fdb0caabd2f2fece3b0`
- summary:
  - citation `88.0%`
  - correct source `86.0%`
  - hallucination `0.0%`
  - refusal `100.0%`
  - avg response `9116.5 ms`
  - error count `0`

This third run supersedes the earlier `precision_fix` artefact as the current official post-train evidence file for the `dgx1` lane.

## Promotion Contract Result

Canonical promotion gate:

- baseline manifest:
  - `evaluation/reports/evidence_baseline_faz1_50_20260308.json`
- post-train manifest:
  - `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`

Gate result: `READY`

Why it passes:

1. frozen `807`-row train package is unchanged
2. held-out leakage check passes
3. duplicate excess remains `0`
4. baseline and post-train artefacts share `eval_family=faz1-50`
5. baseline and post-train artefacts share `runner=eval_runner`
6. checkpoint identities are distinct and traceable

## Interpretation

- the repo's formal promotion contract is satisfied
- the candidate also clears the original live-lane concern that existed on `node3`:
  - avg response time is now `~9.1s`, not `~120s`
- this means the candidate is no longer only governance-valid; it is also operationally credible on the selected merged serving lane

## Next Step

1. keep `dgx1` merged as the official post-train measurement lane
2. keep `node3` merged only as a fallback/debug lane
3. preserve the original baseline lane separately until an explicit production cutover decision is made
