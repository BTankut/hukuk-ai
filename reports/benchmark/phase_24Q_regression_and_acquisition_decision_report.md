# Phase 24Q Regression and Acquisition Decision Report

## Commit SHA List

```text
Phase24Q-A audit = 4844b26
Phase24Q-B decision = f39cdf7
Phase24Q-C acquisition plan = 299cef7
Phase24Q-D trace policy = b7367d7
Phase24Q-E final report = commit containing this file
```

## CBY-Only Full Regression Audit

Phase24Q-A produced the required 100-row delta table:

```text
baseline_run = reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full
cby_run = reports/benchmark/runs/phase_24P_R_full_shadow_20260504T1340Z
phase23RE_raw_score_proxy = 816.86
phase24PR_raw_score_proxy = 806.87
raw_score_delta = -9.99
phase23RE_pass_proxy = 91
phase24PR_pass_proxy = 90
pass_to_fail_count = 5
fail_to_pass_count = 4
cby_span_interference_detected = false
```

The five pass-to-fail rows did not contain the new CBY span in Phase24P-R evidence. `CBY-05` saw the new CBY span but stayed `PASS` with unchanged score, so it was classified as benign same-family neighbor visibility.

## CBY Merge Decision

```text
selected_option = Option B - Keep CBY span but require selector scoping and matched rerun
live_cutover = no
collection_merge = no
diagnostic_value = keep
```

CBY-06 improved from 6.80 to 8.58, but the full run is not merge-safe. The Phase23R-E vs Phase24P-R comparison is not a clean same-runtime A/B pair because API URL, collection, and gateway/selector SHAs differ. The safe next step is a matched same-runtime base-vs-CBY run before reconsidering merge.

## TEB Raw Acquisition Decision

```text
selected_option = Option B - Manual browser capture required
teb04_materialization = blocked
runtime_patch = no
official_source = GIB CDN PDF
```

Official source: [GIB KDV Genel Uygulama Tebligi PDF](https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf).

Browser/web access renders the official PDF, but local scripted capture still returns HTTP 400 JSON for tested `getFile`, `getFileResources`, browser UA, Accept, Referer, and Origin variants. No TEB-04 materialization is allowed until the browser-saved raw PDF, SHA-256, byte size, source URL, and acquisition record are committed.

## Trace Artifact Policy

```text
max_trace_size_committed_to_git = 25 MB
default_trace_storage = local_only
commit_summary_artifacts = yes
commit_large_trace_by_default = no
git_lfs_required = no for Phase24Q
history_rewrite = no
```

`.gitignore` now explicitly ignores trace file patterns under `reports/benchmark/runs/`. `git add -f` must not be used for `trace*.jsonl`, compressed traces, or full run directories unless a written exception exists in the phase report.

## Productization / Eval / Fine-Tuning

```text
productization = closed
internal_eval = closed
fine_tuning = closed
model_prompt_topk_changes = none
qid_specific_runtime_branch = none
benchmark_answer_key_used = no
```

## Final Live 8000 State

Read-only health probe:

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Live `8000` was not modified during Phase24Q.

## Next Recommended Phase

Open Phase24R as a controlled evidence phase, not a remediation merge:

```text
1. Run matched same-runtime base-vs-CBY full benchmark with identical model, prompt, top-k, gateway code, scorer, and runtime knobs.
2. Keep live 8000 unchanged.
3. Intake manually captured TEB-04 raw PDF and SHA-256 if delivered.
4. Only after hashable TEB raw exists, open TEB-04 section materialization.
5. Do not add large traces to git; commit summary artifacts only.
```
