# Phase 20F Decision

Status: CONDITIONAL_ACCEPT_PHASE20_C_D_AND_OPEN_PHASE21

## Decision

Phase 20C/D are retained because Phase 20F preserves pass no-regression (`79`) and all hard safety gates. Phase 20F does not satisfy the strict raw no-regression target: raw score is `755.6`, below the preferred `>=760` threshold and `1.01` below R8 raw. This is not a promotion decision. The next phase should be Phase 21 source/span-family remediation, not more Phase 20 slot/synthesis patching.

## Gates

| Gate | Result |
| --- | --- |
| raw_score_proxy >= 760 preferred | FAIL (`755.6`) |
| raw_score_proxy >= 756 no regression | FAIL (`755.6`) |
| pass_proxy >= 79 no regression | PASS (`79`) |
| unsupported_confident_claim <= 2 | PASS (`0`) |
| contract_valid = 100/100 | PASS (`100/100`) |
| green_lane = PASS | PASS (`pass`) |
| source_key_v2_collision = 0 | PASS (`0`) |
| binding_source_key_collision = 0 | PASS (`0`) |
| CB_GENELGE = 4/4 | PASS (`4/4`) |
| UY >= 9/10 | PASS (`10/10`) |
| MULGA >= 3/5 | PASS (`3/5`) |
| YONETMELIK >= 6/10 | PASS (`6/10`) |
| wrong_family <= 10 | PASS (`10`) |
| wrong_document <= 9 | PASS (`9`) |
| hallucinated_identifier <= 11 | PASS (`9`) |

## Productization / Fine-Tuning

- Productization remains closed.
- Fine-tuning remains closed.
- Reason: family slices still contain source/document/span blockers and missing/partial grounding remains 95/100.
