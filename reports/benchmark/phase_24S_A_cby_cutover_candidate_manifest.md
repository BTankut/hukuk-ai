# Phase 24S-A CBY Cutover Candidate Manifest

## Candidate

```text
candidate_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
candidate_entity_count = 349405
base_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
base_entity_count = 349403
delta_vs_current_live = +2
scope = benchmark_only
```

## Runtime Binding

```text
git_sha = b63c75715be6419295caedd5249e86393d6bacb6
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
embedding_model = intfloat/multilingual-e5-large-instruct
productization = closed
internal_eval = closed
fine_tuning = closed
TEB-04 materialization = out_of_scope
```

## Matched A/B Evidence

```text
source_report = reports/benchmark/phase_24R_D_matched_ab_delta.md
BASE raw_score_proxy = 725.40
CBY raw_score_proxy = 727.18
raw_score_delta = +1.78
BASE pass_proxy = 72
CBY pass_proxy = 73
pass_delta = +1
changed_rows = CBY-06 only
expected_changed_row = CBY-06
expected_improvement = CBY-06 6.80 FAIL -> 8.58 PASS
guard_regression = false
```

## Rollback Target

```text
rollback_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
rollback_entity_count = 349403
rollback_lane = phase22f_s7_full_shadow
```

## Source Hashes

- source_catalog_hash_entries: `4`
- source_supplement_hash_entries: `8`

Full hash lists are recorded in the JSON manifest.
