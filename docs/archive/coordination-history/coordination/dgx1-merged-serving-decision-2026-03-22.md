# DGX1 Merged Serving Decision

Date: 2026-03-22
Scope: decide the primary post-train candidate serving lane after the `dgx1` cleanup rerun and compare it against the earlier `node3` merged lane
Decision: promote the `dgx1` merged lane as the primary post-train candidate serving path and demote the older `node3` merged lane to fallback/debug only

## Compared Lanes

### Previous merged lane

- lane:
  - `node3` merged checkpoint + `vllm-node-tf5` + local bridge
- report:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_merged_20260321.json`

### New preferred merged lane

- lane:
  - `dgx1:30000/v1` merged runtime + local bridge + candidate gateway
- report:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`
- manifest:
  - `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_post_promotion_cleanup_20260322.json`

## Metric Delta

| Metric | Node3 Merged | DGX1 Cleanup | Delta |
|--------|--------------|--------------|-------|
| Citation Rate | `87.76%` | `88.0%` | `+0.24pp` |
| Correct Source Rate | `72.99%` | `86.0%` | `+13.01pp` |
| Hallucination Rate | `6.12%` | `0.0%` | `-6.12pp` |
| Refusal Accuracy | `100.0%` | `100.0%` | `same` |
| Avg Response Time | `21876.2 ms` | `9116.5 ms` | `-12759.7 ms` |

## Why DGX1 Wins

- clears the formal Faz 1 bar with more margin
- substantially better source precision
- hallucination dropped to zero in the matched rerun
- latency is less than half of the `node3` merged lane
- sustained-load stability held for the full 50-question run with `error_count=0`

## Operating Decision

1. `dgx1` merged is now the primary post-train candidate serving lane.
2. `node3` merged remains available only as fallback/debug.
3. the baseline/base-model lane remains separate and untouched.

## Repo Lock-In

- launcher:
  - `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh`
- default remote host is now pinned to:
  - `btankut@192.168.12.243`

This avoids depending on local hostname resolution drift and keeps the preferred lane reproducible.

## Next Step

1. keep all future matched post-train evals on the `dgx1` merged lane unless the user explicitly switches runtime strategy
2. treat `node3` as non-primary for measurement and promotion claims
