# Phase 24HU-E Focused Non-Live Smoke Report

## Run

Endpoint:

```text
http://127.0.0.1:8043/v1
```

Run directory:

```text
reports/benchmark/runs/phase_24HU_focused_non_live_candidate_smoke
```

Command:

```text
python3 scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8043/v1 --model hukuk-ai-poc --out-dir reports/benchmark/runs/phase_24HU_focused_non_live_candidate_smoke --qids KANUN-08 TEB-04 TUZUK-05 YON-05 MULGA-01 MULGA-05 TEB-06 CBY-06 KANUN-12 YON-04 TUZUK-04 CBG-01 CBKAR-08
python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/phase_24HU_focused_non_live_candidate_smoke/candidate_answers.csv --out-dir reports/benchmark/runs/phase_24HU_focused_non_live_candidate_smoke/score
```

## Summary

```text
total=13
raw_score_proxy=104.83 / 130
average_score_0_10_proxy=8.06
pass_proxy=11
fail_proxy=2
contract_invalid=0
unsupported_confident_answer=0
answer_contract_missing=0
source_key_v2_collision=0
binding_source_key_collision=0
legacy_source_key_collision=1
```

The legacy `source_key_collision` is unchanged from Phase 24HT on `CBKAR-08` and is not a Phase 24HU regression. `source_key_v2_collision` and `binding_source_key_collision` stayed zero.

## Delta vs Phase 24HT Focused Smoke

| QID | Phase 24HT | Phase 24HU | Delta | Result |
| --- | ---: | ---: | ---: | --- |
| KANUN-08 | 3.93 FAIL | 8.22 PASS | +4.29 | recovered |
| TEB-04 | 8.15 PASS | 8.15 PASS | +0.00 | stable |
| TUZUK-05 | 10.00 PASS | 10.00 PASS | +0.00 | stable |
| YON-05 | 7.55 PASS | 7.55 PASS | +0.00 | stable |
| MULGA-01 | 8.37 PASS | 8.37 PASS | +0.00 | stable |
| MULGA-05 | 7.10 PASS | 7.10 PASS | +0.00 | stable |
| TEB-06 | 8.90 PASS | 8.90 PASS | +0.00 | stable |
| CBY-06 | 6.80 FAIL | 6.80 FAIL | +0.00 | stable residual |
| KANUN-12 | 8.99 PASS | 8.99 PASS | +0.00 | stable |
| YON-04 | 8.22 PASS | 8.22 PASS | +0.00 | stable |
| TUZUK-04 | 4.63 FAIL | 4.63 FAIL | +0.00 | stable residual |
| CBG-01 | 8.65 PASS | 8.65 PASS | +0.00 | stable |
| CBKAR-08 | 9.25 PASS | 9.25 PASS | +0.00 | stable |

Focused-set aggregate changed from `100.54` to `104.83`, with pass count improving from `10/13` to `11/13`.

## KANUN-08 Recovery

Phase 24HU kept the primary source on:

```text
selected_document_id=TÜKETİCİNİN KORUNMASI HAKKINDA KANUN
selected_main_span_id=TKHK m.18/f.0
source_family_claimed=KANUN
```

Supporting secondary-family evidence appeared in the selected support chain:

```text
20237 m.12/f.0
20444 m.8/f.0
20444 m.9/f.0
TKHK m.43/f.0
```

The exception/supporting path no longer fills from the prior unrelated TBK/private-law span.

Observed trace:

```text
pre_filter_family_set=yonetmelik | kanun | cb_yonetmelik | khk
reranked_family_set=yonetmelik | kanun | cb_yonetmelik | khk
exception_slot_role=supporting_source
```

## Acceptance

Accepted for targeted recovery:

- `KANUN-08` materially improved and passed.
- Primary `KANUN` identity did not regress away from TKHK.
- Supporting `YONETMELIK` evidence entered the bundle.
- No unsupported confident answers.
- No invalid answer contracts.
- No source-key-v2 collision.
- No binding collision.
- Guard rows stayed score-identical to Phase 24HT.

Residual:

- `KANUN-08` still has proxy failure classes `missing_required_content_signal | partial_grounding_only`; the row passes but exact supporting-span precision is not fully closed.
- `CBY-06` and `TUZUK-04` remain unrelated residual fails and did not regress in this phase.

