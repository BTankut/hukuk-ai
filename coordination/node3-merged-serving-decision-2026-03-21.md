# Node3 Merged Serving Decision

Date: 2026-03-21
Scope: decide whether the merged `dgxnode3` vLLM path should replace the slower adapter/proxy candidate path for the current `807` post-train model
Decision: promote the merged `vllm-node-tf5` path as the primary post-train candidate serving path, while keeping the older adapter/proxy path only as fallback

## Compared Paths

### Previous candidate path

- node3 adapter serve + OpenAI proxy + local tunnel + candidate gateway
- report:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`

### New candidate path

- node3 merged checkpoint + `vllm-node-tf5` + local tunnel + candidate gateway
- report:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_merged_20260321.json`
- manifest:
  - `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_merged_20260321.json`

## Metric Delta

| Metric | Old | Merged | Delta |
|--------|-----|--------|-------|
| Citation Rate | `90.00%` | `87.76%` | `-2.24pp` |
| Correct Source Rate | `77.13%` | `72.99%` | `-4.14pp` |
| Hallucination Rate | `2.00%` | `6.12%` | `+4.12pp` |
| Refusal Accuracy | `100.00%` | `100.00%` | `same` |
| Avg Keyword Coverage | `54.25%` | `55.99%` | `+1.74pp` |
| Phrase Hit Rate | `62.79%` | `66.67%` | `+3.88pp` |
| Avg Response Time | `120302.8 ms` | `21876.2 ms` | `-98426.6 ms` |

## Interpretation

- The merged path is **quality-worse but still gate-passing**.
- All formal Faz 1 acceptance gates still pass:
  - citation `87.76%`
  - correct source `72.99%`
  - hallucination `6.12%`
  - refusal accuracy `100%`
- The latency win is large enough to matter operationally:
  - average response time fell by about `81.8%`

## Additional Verification

- merged runtime health:
  - `http://127.0.0.1:30003/v1/models` => `200`
- merged candidate gateway health:
  - `http://127.0.0.1:8003/v1/health` => `200`
- timed cited smoke:
  - query: `TBK m.49 neyi duzenler? Kisa ve kaynakli cevap ver.`
  - elapsed: `15.889s`
  - citations: `TBK m.49`

## Risk Notes

- The merged path is not a free win:
  - source precision dropped
  - hallucination rose
- The single eval timeout on `TBK-043` did not reproduce on immediate manual retry; the retry returned in `25.835s`, but with extra citations/noise. So the real issue is source quality drift more than a hard availability fault.
- `tbk_kefalet` remains the most obvious weak slice in the merged run.

## Operating Decision

1. Use the merged `vLLM` path as the **primary post-train candidate serving lane**.
2. Keep the adapter/proxy lane as **fallback only**.
3. Do **not** overwrite the older baseline/base-model production lane automatically in this milestone.

This keeps the repo aligned with the gate-first Faz 1 discipline:

- baseline is still preserved
- the fine-tuned candidate now has a materially better serving path
- the serving upgrade is accepted only because the merged path still clears the formal Faz 1 bar

## Next Step

1. keep `8003` merged lane as the main post-train measurement lane
2. use the new compare utility for future serving/report deltas
3. target the weak slices (`TBK-043`, kefalet cluster) in the next fine-tune/eval wave
