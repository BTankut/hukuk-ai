# Phase 24U-C CBY Trace-On Full Benchmark Summary

Generated UTC: `2026-05-05T14:29:20Z`  
Report HEAD before commit: `84e9c22e5731a32a48980f7397a682e3489a798f`

## Run

```text
run_dir = /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/phase_24U_C_cby_trace_on_full_20260505T131540Z
api_url = http://127.0.0.1:8038/v1
model = hukuk-ai-poc
include_trace = True
git_sha = 66de1538b6f007d29f6b50189d53b0d3116dd97e
DGX_MODEL = /models/merged_model_fabric_stage_20260321
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
entity_count = 349405
vector_dimension = 1024
live_8000_untouched = True
```

Execution note: the answer collection completed successfully. The first scoring invocation from the pinned worktree lacked the private answer key file, so scoring was rerun with the same pinned scorer script and explicit absolute answer key path from the main repo.

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
raw_score_proxy = 807.27 / 1000
pass_proxy = 90 / 100
fail_proxy = 10
hallucinated_identifier = 7
wrong_family = 8
wrong_document = 3
missing_gold_document_signal = 3
auto_fail_triggered = 2
```

Failure rows:

```text
KANUN-02, KANUN-08, KKY-01, KKY-03, MULGA-04, TEB-04, TUZUK-04, TUZUK-05, YON-05, YON-08
```

Slowest response rows:

```text
CBKAR-07 = 277046ms
CBKAR-04 = 161042ms
CBKAR-06 = 126892ms
CBKAR-03 = 93433ms
CBY-05 = 90694ms
CBKAR-01 = 73457ms
CBKAR-02 = 72420ms
CBY-03 = 65206ms
```

## Reference Comparison

| Reference | Raw | Pass | Delta raw | Delta pass |
|---|---:|---:|---:|---:|
| Phase24U-B BASE trace-on | 805.09 | 89 | +2.18 | +1 |
| Phase23R-E | 816.86 | 91 | -9.59 | -1 |

## Interpretation

CBY trace-on completed cleanly and improved over BASE by `+2.18` raw and `+1` pass. The improvement is narrow: `CBY-06` moved from FAIL to PASS, while aggregate wrong-family, wrong-document, and hallucinated-identifier counters did not increase.

This passes CBY consideration criteria for this diagnostic phase, but it still does not restore Phase23R-E score parity. Productization, internal eval, fine-tuning, and live cutover remain closed.
