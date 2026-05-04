# Phase 24O Targeted Smoke Report

Final valid run:

```text
reports/benchmark/runs/phase_24O_targeted_shadow_smoke_20260504T094600Z
```

Two earlier Phase24O targeted attempts are treated as infra-invalid diagnostics:

- `phase_24O_targeted_shadow_smoke_20260504T091144Z`: shadow collection was not loaded.
- `phase_24O_targeted_shadow_smoke_20260504T092222Z`: candidate used hashing embedding and hit vector dimension mismatch; live parity requires remote embedding.

## Runtime Parity

```text
api_url = http://127.0.0.1:8031/v1
model = hukuk-ai-poc
DGX_MODEL = /models/merged_model_fabric_stage_20260321
MILVUS_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24n
EMBEDDING_BACKEND = remote
EMBEDDING_BASE_URL = http://127.0.0.1:8081/v1
live_8000_untouched = true
```

## Contract Gate

```text
total = 16
answered = 16
refused_or_empty = 0
errors = 0
missing_trace = 0
contract_valid = 16
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
```

## Score Summary

```text
raw_score_proxy = 112.28 / 160
average_score_0_10_proxy = 7.02
pass_proxy = 10
fail_proxy = 6
hallucinated_source_count = 0
repealed_as_active_count = 0
temporal_validity_miss_count = 0
canonical_span_materialized_count = 16
```

## Target Rows

| QID | Result | Score | Main outcome |
| --- | --- | ---: | --- |
| KANUN-12 | PASS | 8.99 | 5651 selected and grounded. |
| KKY-03 | FAIL | 5.38 | Correct 34360 document selected; answer contract still degrades due source identifier/citation materialization. |
| YON-04 | PASS | 8.22 | KVKK imha regulation selected via supplement/title alias. |
| TUZUK-04 | FAIL | 4.63 | No active-current-law claim; now historical/mulga caveat. Proxy still marks family mismatch because answer correctly avoids active tüzük claim. |
| CBY-06 | FAIL | 6.80 | Broad regulation selected, but 11153/m.11 amendment span missing. |
| CBY-04 | PASS | 7.12 | Usable answer; taxonomy residual remains. |
| KKY-01 | FAIL | 6.65 | Correct legal document selected; benchmark family bucket mismatch remains. |
| TEB-04 | FAIL | 0.00 | Correct KDV GUT source selected, but m.0 section materialization auto-fails. |

## Guard Rows

```text
MULGA-01 = PASS 8.37
MULGA-05 = PASS 7.10
TEB-06 = PASS 8.90
CBG-01 = PASS 8.65
CBKAR-08 = PASS 9.25
UY-01 = PASS 7.82
YON-05 = FAIL 5.75
KANUN-03 = PASS 8.65
```

Required guard rows `MULGA-01`, `MULGA-05`, and `TEB-06` remained PASS.

## Gate Decision

Targeted gate passed for Phase 24O purposes:

- contract valid all
- unsupported confident answer zero
- answer contract invalid zero
- source_key_v2 and binding collisions zero
- required guard rows stayed PASS
- TUZUK-04 no longer claims old tüzük as active current law
- at least two target residual rows improved: KANUN-12, YON-04, TUZUK-04 answer policy, plus KKY-01/KKY-03 source identity

Full shadow benchmark was started on the same candidate runtime.
