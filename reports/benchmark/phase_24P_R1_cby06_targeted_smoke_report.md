# Phase 24P-R1 CBY-06 Targeted Smoke Report

## Decision

```text
status = PASS
full_shadow_allowed = true
live_8000_untouched = true
```

Valid run:

```text
reports/benchmark/runs/phase_24P_R1_cby06_targeted_smoke_loaded_20260504T1332Z
```

An earlier smoke run was discarded because the target Milvus collection was visible but not loaded, causing retrieval to continue without chunks. The valid run above was executed after explicit collection load.

## Runtime

```text
api_url = http://127.0.0.1:8034/v1
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
entity_count = 349405
vector_dimension = 1024
guardrails = disabled
verification = disabled
```

## Runtime Contract

```text
total = 10
answered = 10
refused_or_empty = 0
errors = 0
missing_trace = 0
missing_contract_fields = 0
contract_valid = 10
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
hallucinated_source_count = 0
```

## Score Summary

```text
raw_score_proxy = 80.51 / 100
average_score_0_10_proxy = 8.05
pass_proxy = 9
fail_proxy = 1
```

## Per-QID

| qid | score | result | claimed_family | claimed_identifier | effective_state | gate_note |
|---|---:|---|---|---|---|---|
| CBY-06 | 8.58 | PASS | CB_YONETMELIK | DEGISIKLIK m.1 | active | target improved/PASS |
| MULGA-01 | 8.37 | PASS | MULGA | 2547 m.54 | repealed | guard pass |
| MULGA-05 | 7.10 | PASS | MULGA | 6570 m.gec1 | repealed | guard pass |
| TEB-06 | 8.90 | PASS | TEBLIGLER | 23093 | active | guard pass |
| KANUN-12 | 8.99 | PASS | KANUN | 5651 | active | guard pass |
| YON-04 | 8.22 | PASS | YONETMELIK | KVKK İmha Yönetmeliği m.10/f.0 | active | guard pass |
| TUZUK-04 | 4.63 | FAIL | MULGA | 859727 m.4 | repealed | not active-current-law claim |
| CBG-01 | 8.65 | PASS | CB_GENELGE | 2024/7 m.0 | active | guard pass |
| CBKAR-08 | 9.25 | PASS | CB_KARAR | 9903 | active | guard pass |
| UY-01 | 7.82 | PASS | UY | 24839 m.7 | active | guard pass |

## Gate Findings

```text
CBY-06 improves_or_PASS = true
MULGA-01_PASS = true
MULGA-05_PASS = true
TEB-06_PASS = true
contract_valid_all = true
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
TUZUK-04_active_current_law_claim = false
```

## Decision

Phase 24P-R1 targeted smoke passes. Full shadow benchmark is authorized by the Phase 24P-R condition because CBY-06 is now PASS.
