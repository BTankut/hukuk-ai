# DGX1 Merged Stable Rerun

Date: 2026-03-21
Scope: rerun the full `faz1-50` post-train eval against the updated `dgx1` merged endpoint after the inference service was retuned for better stability
Decision: the retuned `dgx1` lane is materially better than the first failed attempt, but it still does not clear Faz 1 because the serving path continues to break under sustained load

## Runtime Context

User-provided serving changes on `dgx1`:

- `--gpu-memory-utilization-gb 106`
- `--kv-cache-dtype fp8`
- `--max-num-seqs 8`
- CUDA graphs enabled
- FlashInfer enabled

Evaluated lane:

- remote endpoint: `http://dgx1:30000/v1`
- local bridge: `127.0.0.1:30004 -> dgx1:30000`
- local candidate gateway: `127.0.0.1:8004`
- model: `/models/merged_model_fabric_stage_20260321`

## Quick Verification Before Rerun

- `GET /v1/models` passed
- `GET /v1/health` on `8004` passed
- short cited smoke passed:
  - `TBK m.49`
- short weak-slice check had already shown `8004` better than the older `8003` node3 merged lane on the 5-question slice

## Full Faz 1 Rerun Result

Report:

- `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_stable_20260321.json`

Summary:

- citation: `76.5%`
- correct source: `68.4%`
- hallucination: `0.0%`
- refusal accuracy: `100.0%`
- avg response time: `15593 ms`
- error count: `16`

Gate status:

- citation gate: fail
- correct source gate: fail
- hallucination gate: pass
- refusal gate: pass
- overall: fail

## What Improved

Compared with the first `dgx1` full run:

- error count improved from `35 -> 16`
- the lane stayed healthy through roughly the first `30` questions
- source quality stayed meaningfully higher before the failure wave
- no hallucination was recorded in the finished report

## Remaining Failure Mode

The lane still collapsed under sustained load starting around:

- `TBK-031`

Observed gateway-side root error:

- `openai.APIConnectionError: Connection error`
- underlying `httpx.ReadError`

Interpretation:

- this is not just a quality issue
- the `dgx1` inference service is improved, but not yet stable enough for a full `faz1-50` run on the current end-to-end RAG path

## Additional Note

The repo already requests `chat_template_kwargs.enable_thinking=false` in both:

- `evaluation/eval_runner.py`
- `api-gateway/src/llm/client.py`

So the next service-side optimization should not be "increase context length first".
The better next step remains:

1. enforce no-thinking behavior reliably in the serving layer
2. then continue stabilizing long-run connection handling

## Conclusion

- `dgx1` is now a better merged lane than the first failed attempt
- but it is still not eligible to replace the current accepted post-train measurement lane
- the blocker remains serving stability under sustained eval load
