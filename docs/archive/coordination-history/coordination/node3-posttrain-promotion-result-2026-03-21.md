# Node3 Post-Train Promotion Result

Date: 2026-03-21
Scope: freeze the first matched post-train evaluation result for the completed `dgxnode3` Qwen3.5 fine-tune run and compare it against the frozen Faz 1 baseline contract
Decision: the repo's formal promotion contract now passes for the node3 post-train candidate, but the currently served runtime still shows a material latency regression relative to the original Faz 1 live acceptance picture

## Candidate Identity

- model ref: `hukuk-ai-sft-qwen35-807-node3`
- checkpoint ref: `hukuk-ai-sft-qwen35-807-node3-20260321`
- raw report role: `post_train`
- eval family: `faz1-50`
- runner: `eval_runner`

## Evaluation Attempts

### 1) Initial attempt (`timeout=180s`) - audit only

- raw report: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321.json`
- error count: `11`
- citation rate: `0.8462`
- correct source rate: `0.6906`
- hallucination rate: `0.0513`
- refusal accuracy: `1.0000`
- avg response time: `93048.4 ms`

This run is retained for auditability, but it is not the official promotion artefact because timeout pressure corrupted the measurement.

### 2) Clean rerun (`timeout=600s`) - official promotion artefact

- raw report: `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`
- evidence manifest: `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`
- error count: `0`
- citation rate: `0.9000`
- correct source rate: `0.7713`
- hallucination rate: `0.0200`
- refusal accuracy: `1.0000`
- avg response time: `120302.8 ms`

## Promotion Contract Result

The canonical promotion gate was re-run with:

- baseline manifest: `evaluation/reports/evidence_baseline_faz1_50_20260308.json`
- post-train manifest: `evaluation/reports/evidence_post_train_faz1_50_hukuk_ai_sft_qwen35_807_node3_20260321_t600.json`

Gate result: `READY`

Why it passed:

1. train package is the frozen 807-row canonical package
2. held-out leakage check passes
3. duplicate excess remains `0`
4. baseline and post-train artefacts share the same `eval_family=faz1-50`
5. baseline and post-train artefacts share the same `runner=eval_runner`
6. checkpoint identities are distinct and traceable

## Important Caveat

The original `FAZ1-FINAL-RAPOR.md` live acceptance picture includes a latency expectation around `<=30s`.

The current node3 served candidate averaged:

- `120302.8 ms` (`~120.3s`)

Therefore:

- governance/order/gate discipline is aligned with the Faz 1 report
- the repo's formal promotion contract is satisfied
- but the currently served candidate should not be described as having matched the original Faz 1 live latency profile

## Next Step

1. improve the serving path for the node3 candidate or move the adapter behind a faster runtime
2. re-measure latency after the serving change
3. only claim full live parity when latency is brought back into an acceptable band
