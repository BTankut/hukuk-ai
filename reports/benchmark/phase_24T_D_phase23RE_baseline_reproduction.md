# Phase 24T-D Phase23R-E Baseline Reproduction

Generated at UTC: `2026-05-05T11:18:59Z`  
Git HEAD before D commit: `6b8418928d5fa8aa613fd7a945c922753d6ae84d`

## Run

```text
run_dir = reports/benchmark/runs/phase_24T_D_phase23RE_reproduction_trace_on_20260505T101732Z
api_url = http://127.0.0.1:8000/v1
model = hukuk-ai-poc
include_trace = true
top_k = 20
max_tokens = 1200
live_8000_changed = false
```

## Runtime Provenance

```text
runtime_git_sha = 57d13b6278814f82f42f711160afcf26d76432d8
DGX_MODEL = /models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
vector_dimension = 1024
lane = phase22f_s7_full_shadow
api_version = 2026-05-03-phase23R-E-benchmark-only-cutover
```

## Contract Result

```text
answered = 100 / 100
refused_or_empty = 0
errors = 0
missing_trace = 0
contract_valid = 100 / 100
unsupported_confident_answer = 0
answer_contract_invalid = 0
```

## Score Result

| Metric | Phase23R-E E5 | Phase24T-D trace-on current | Delta | Reproduced? |
| --- | ---: | ---: | ---: | --- |
| raw_score_proxy | 816.86 | 805.09 | -11.77 | NO |
| pass_proxy | 91 | 89 | -2 | NO |
| wrong_family | 6 | 8 | +2 | NO |
| wrong_document | 4 | 3 | -1 | NO |
| hallucinated_identifier | 4 | 7 | +3 | NO |

## Decision

Phase24T-D does not reproduce the exact Phase23R-E baseline. It reproduces most of the lost score relative to Phase24R/S trace-off runs, but remains below the accepted Phase23R-E gate.

```text
Phase23R-E = 816.86 / 91
Phase24R BASE trace-off = 725.40 / 72
Phase24T-D current trace-on = 805.09 / 89
trace_on_recovery_vs_24R_base = +79.69 raw, +17 pass
remaining_gap_vs_23R_E = -11.77 raw, -2 pass
```

Interpretation:

- The 725/72 collapse is primarily non-equivalent trace-off benchmark evidence.
- The remaining 805.09/89 gap indicates current code/source supplement drift since Phase23R-E.
- Open a narrow code/source supplement regression audit before any CBY merge or runtime remediation.

## Changed Rows vs Phase23R-E

```text
changed_rows = 18
pass_to_fail = 5
fail_to_pass = 3
```

### Worst Score Deltas

| QID | Phase23R-E | Phase24T-D | Delta | Phase23R-E pass | Phase24T-D pass | Phase24T-D failure classes |
| --- | ---: | ---: | ---: | --- | --- | --- |
| MULGA-04 | 7.55 | 0.00 | -7.55 | PASS | FAIL | auto_fail_triggered \| missing_required_content_signal \| partial_grounding_only |
| KANUN-08 | 7.55 | 1.45 | -6.10 | PASS | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_family \| wrong_document \| partial_grounding_only |
| KANUN-02 | 8.65 | 3.25 | -5.40 | PASS | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| YON-05 | 9.55 | 5.75 | -3.80 | PASS | FAIL | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |
| TUZUK-04 | 6.43 | 4.63 | -1.80 | FAIL | FAIL | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |
| KKY-04 | 9.32 | 7.55 | -1.77 | PASS | PASS | missing_required_content_signal \| partial_grounding_only |
| KKY-11 | 9.66 | 7.89 | -1.77 | PASS | PASS | missing_required_content_signal \| partial_grounding_only |
| KKY-08 | 9.55 | 8.00 | -1.55 | PASS | PASS | missing_required_content_signal \| partial_grounding_only |
| CBK-01 | 9.55 | 9.10 | -0.45 | PASS | PASS | missing_required_content_signal \| partial_grounding_only |
| YON-08 | 7.25 | 6.80 | -0.45 | PASS | FAIL | missing_required_content_signal \| partial_grounding_only |
| CBY-04 | 6.85 | 7.12 | +0.27 | FAIL | PASS | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |
| UY-05 | 9.19 | 9.46 | +0.27 | PASS | PASS | missing_required_content_signal \| partial_grounding_only |
| KKY-06 | 8.22 | 8.56 | +0.34 | PASS | PASS | missing_required_content_signal \| partial_grounding_only |
| KANUN-19 | 8.65 | 9.10 | +0.45 | PASS | PASS | missing_required_content_signal \| partial_grounding_only |
| KANUN-16 | 7.55 | 8.65 | +1.10 | PASS | PASS | missing_required_content_signal \| partial_grounding_only |
| KKY-03 | 1.45 | 5.38 | +3.93 | FAIL | FAIL | missing_required_content_signal \| wrong_family \| partial_grounding_only |
| YON-04 | 3.25 | 8.22 | +4.97 | FAIL | PASS | missing_required_content_signal \| partial_grounding_only |
| KANUN-12 | 1.45 | 8.99 | +7.54 | FAIL | PASS | missing_required_content_signal \| partial_grounding_only |

### Pass-to-Fail Rows

| QID | Phase23R-E | Phase24T-D | Delta | Phase23R-E pass | Phase24T-D pass | Phase24T-D failure classes |
| --- | ---: | ---: | ---: | --- | --- | --- |
| MULGA-04 | 7.55 | 0.00 | -7.55 | PASS | FAIL | auto_fail_triggered \| missing_required_content_signal \| partial_grounding_only |
| KANUN-08 | 7.55 | 1.45 | -6.10 | PASS | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_family \| wrong_document \| partial_grounding_only |
| KANUN-02 | 8.65 | 3.25 | -5.40 | PASS | FAIL | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| YON-05 | 9.55 | 5.75 | -3.80 | PASS | FAIL | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |
| YON-08 | 7.25 | 6.80 | -0.45 | PASS | FAIL | missing_required_content_signal \| partial_grounding_only |

## Required Follow-Up

Proceed with Phase24T-E design under Option A plus Option B:

- normalize benchmark command/provenance to trace-on for matched A/B before comparing BASE/CBY
- audit code/source supplement drift between Phase23R-E `b34ed1c` and current head, focused on the remaining 11.77 raw / 2 pass gap
- do not modify live `8000`
