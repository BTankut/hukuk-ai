# Phase 24U-D Source Supplement Ablation Summary

Generated UTC: `2026-05-05T15:31:56Z`  
Report HEAD before commit: `c351588bd497681d41f8dcc0ba49db21c44a196e`

## Run

```text
run_dir = /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/phase_24U_D_source_supplement_ablation_full_20260505T143052Z
api_url = http://127.0.0.1:8039/v1
model = hukuk-ai-poc
include_trace = True
git_sha = 66de1538b6f007d29f6b50189d53b0d3116dd97e
DGX_MODEL = /models/merged_model_fabric_stage_20260321
collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
entity_count = 349403
vector_dimension = 1024
ENABLE_PHASE24N_SOURCE_SUPPLEMENTS = false
live_8000_untouched = True
```

Note: the benchmark provenance schema does not currently include `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS`, so this flag value is taken from the verified `8039` process env at launch time.

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
raw_score_proxy = 804.42 / 1000
pass_proxy = 89 / 100
fail_proxy = 11
hallucinated_identifier = 7
wrong_family = 8
wrong_document = 3
missing_gold_document_signal = 3
auto_fail_triggered = 2
insufficient_canonical_span_evidence = 2
```

Failure rows:

```text
CBY-06, KANUN-02, KANUN-08, KKY-01, KKY-03, MULGA-04, TEB-04, TUZUK-04, TUZUK-05, YON-05, YON-08
```

Changed rows vs current BASE trace-on:

```text
YON-04: 8.22 PASS -> 7.55 PASS
```

Slowest response rows:

```text
KKY-03 = 56302ms
KANUN-02 = 56019ms
KANUN-05 = 55612ms
MULGA-04 = 53447ms
YON-08 = 53214ms
CBY-05 = 51785ms
YON-02 = 51774ms
TEB-03 = 51677ms
```

## Interpretation

Disabling Phase24N source supplements did not restore Phase23R-E. The ablation slightly worsened the BASE current trace-on score by `-0.67` raw with no pass change. The only changed row is `YON-04`, which worsened from `8.22 PASS` to `7.55 PASS` and added `insufficient_canonical_span_evidence`.

Therefore source supplement drift is not sufficient to explain the remaining Phase23R-E gap. The safe next action is commit-level regression audit between the Phase23R-E accepted state and current runtime code/config, not a source supplement removal or live setting change.
