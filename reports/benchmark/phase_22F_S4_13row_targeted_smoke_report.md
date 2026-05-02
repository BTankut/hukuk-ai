# Phase 22F-S4 13-Row Targeted Smoke Report

Date: 2026-05-02

## Scope

Implemented and smoke-tested the split temporal claim policy from `hukuk_ai_phase22F_S4_split_temporal_claim_implementation_brief.md`.

This run only used the shadow gateway on `127.0.0.1:8018`. The live `8000` serving lane was not changed.

## Runtime

- Run dir: `reports/benchmark/runs/20260502T0620Z_phase22F_S4_13row_targeted_smoke`
- API URL: `http://127.0.0.1:8018/v1`
- Model: `hukuk-ai-poc`
- Git SHA: `9e9eb812f4de4b714c0d643f12a6bf0a990c5210`
- Branch: `bt/hukuk-ai-100-benchmark-hardening`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Milvus entity count: `349403`
- Vector dimension: `1024`
- Guardrails: `disabled`
- Verification: `disabled`
- Live 8000 untouched: `True`
- Runtime provenance dirty_worktree: `True` due pre-existing unrelated local/untracked workspace state; committed S4 code SHA is recorded above.

## Commands

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8018/v1 \
  --model hukuk-ai-poc \
  --out-dir reports/benchmark/runs/20260502T0620Z_phase22F_S4_13row_targeted_smoke \
  --qids KANUN-05 KANUN-10 KANUN-14 KHK-03 TEB-03 TEB-04 TUZUK-03 UY-01 MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 \
  --timeout 180 --retries 1 --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260502T0620Z_phase22F_S4_13row_targeted_smoke/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260502T0620Z_phase22F_S4_13row_targeted_smoke
```

## Result

- Total: `13`
- Answered: `13`
- Errors: `0`
- Missing trace: `0`
- Missing contract fields: `0`
- Contract valid: `13`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Repealed as active: `0`
- Source key v2 collision: `0`
- Binding collision: `0`
- Proxy pass/fail: `10 PASS / 3 FAIL`
- Average proxy score: `7.15 / 10`

## S4 Policy Gate

S4-C gate status: `PASS`.

- Active non-MULGA rows did not claim MULGA: `8/8`.
- Active non-MULGA expected family surface preserved: `7/8`; residual `UY-01` remains a family identity issue, not a MULGA temporal-claim regression.
- MULGA rows retained historical surface path: `5/5`.
- MULGA proxy pass: `4/5`; residual `MULGA-05` is wrong-article/span selection, not loss of historical surface.
- `TEB-04` remained proxy fail due `auto_fail_triggered` / grounding completeness, not S4 temporal policy.

## Row-Level Policy Buckets

| QID | Proxy | Claimed family | State | S4 bucket | Historical surface |
| --- | --- | --- | --- | --- | --- |
| KANUN-05 | PASS | KANUN | active | active_non_mulga_preserve_family | False |
| KANUN-10 | PASS | KANUN | active | active_non_mulga_preserve_family | False |
| KANUN-14 | PASS | KANUN | active | active_non_mulga_preserve_family | False |
| KHK-03 | PASS | KHK | active | active_non_mulga_preserve_family | False |
| TEB-03 | PASS | TEBLIGLER | active | active_non_mulga_preserve_family | False |
| TEB-04 | FAIL | TEBLIGLER | active | active_non_mulga_preserve_family | False |
| TUZUK-03 | PASS | TUZUK | active | active_non_mulga_preserve_family | False |
| UY-01 | FAIL | YONETMELIK | active | not_applicable | False |
| MULGA-01 | PASS | MULGA | repealed | relation_chain_historical_three_part_claim | True |
| MULGA-02 | PASS | MULGA | repealed | legacy_mulga_historical_surface_without_relation_chain | True |
| MULGA-03 | PASS | MULGA | repealed | legacy_mulga_historical_surface_without_relation_chain | True |
| MULGA-04 | PASS | MULGA | repealed | legacy_mulga_historical_surface_without_relation_chain | True |
| MULGA-05 | FAIL | MULGA | repealed | legacy_mulga_historical_surface_without_relation_chain | True |

## Implementation Notes

- `active_non_mulga_preserve_family` blocks active KANUN/KHK/TEBLIG/TUZUK answers from being surfaced as MULGA when no relation chain exists.
- `relation_chain_historical_three_part_claim` allows controlled historical/current-basis composition only when the relation chain is complete.
- `legacy_mulga_historical_surface_without_relation_chain` preserves explicitly historical MULGA surface without claiming current applicability.
- Public answer contracts now always expose split temporal policy fields, even when the policy is not applicable. This keeps trace/schema inspection deterministic without changing retrieval or answer selection.

## Residuals

The S4-C residuals are outside the split temporal claim policy:

- `TEB-04`: answer/grounding completeness and auto-fail.
- `UY-01`: family identity mismatch (`YONETMELIK` vs expected UY surface).
- `MULGA-05`: wrong article/span selection while still retaining MULGA historical surface.

## Decision

Proceed to Phase 22F-S4-D P0/TEB guard smoke.
