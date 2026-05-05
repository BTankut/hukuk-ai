# Phase 24U-B BASE Trace-On Full Benchmark Summary

Generated UTC: `2026-05-05T13:14:12Z`  
Report HEAD before commit: `66de1538b6f007d29f6b50189d53b0d3116dd97e`

## Run

```text
run_dir = reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z
api_url = http://127.0.0.1:8037/v1
model = hukuk-ai-poc
include_trace = True
git_sha = 66de1538b6f007d29f6b50189d53b0d3116dd97e
DGX_MODEL = /models/merged_model_fabric_stage_20260321
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
vector_dimension = 1024
live_8000_untouched = True
```

Command shape:

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8037/v1 \
  --model hukuk-ai-poc \
  --api-key benchmark \
  --out-dir reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z \
  --allow-missing-trace

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z/candidate_answers.csv \
  --out-dir reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z
```

## Contract / Stop-Rule Counters

| Counter | Value |
|---|---:|
| total | 100 |
| answered | 100 |
| refused_or_empty | 0 |
| errors | 0 |
| missing_trace | 0 |
| missing_contract_fields | 0 |
| contract_valid | 100 |
| unsupported_confident_answer | 0 |
| answer_contract_invalid | 0 |
| source_key_v2_collision_detected | 0 |
| binding_source_key_collision_detected | 0 |

## Score

```text
raw_score_proxy = 805.09 / 1000
pass_proxy = 89 / 100
fail_proxy = 11
hallucinated_identifier = 7
wrong_family = 8
wrong_document = 3
missing_gold_document_signal = 3
auto_fail_triggered = 2
```

Failure rows:

```text
CBY-06, KANUN-02, KANUN-08, KKY-01, KKY-03, MULGA-04, TEB-04, TUZUK-04, TUZUK-05, YON-05, YON-08
```

Failure class counts:

```text
missing_required_content_signal = 93
partial_grounding_only = 93
wrong_family = 8
hallucinated_identifier = 7
missing_gold_document_signal = 3
wrong_document = 3
auto_fail_triggered = 2
insufficient_canonical_span_evidence = 1
```

## Reference Comparison

| Reference | Raw | Pass | Delta raw | Delta pass |
|---|---:|---:|---:|---:|
| Phase23R-E | 816.86 | 91 | -11.77 | -2 |
| Phase24T-D current trace-on | 805.09 | 89 | +0.00 | +0 |

## Interpretation

Phase24U-B completed cleanly under the BASE collection with trace enabled. It reproduces the Phase24T-D current trace-on result exactly (`805.09 / 89`) and confirms the remaining gap versus Phase23R-E (`-11.77 raw / -2 pass`) is still present under a non-live candidate runtime.

This is diagnostic evidence only. It does not authorize productization, internal eval, fine-tuning, or CBY cutover. It does authorize Phase24U-C because the BASE trace-on run completed cleanly with no stop-rule counter breach.
