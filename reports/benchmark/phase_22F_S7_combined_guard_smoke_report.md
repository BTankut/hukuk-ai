# Phase 22F-S7 Combined Guard Smoke Report

## Scope

Combined guard smoke was run after both targeted gates passed:

- S7 TEB targeted gate: PASS
- S7M MULGA targeted gate: PASS

The run used only the shadow runtime. Live `8000` and live/base Milvus collections were not modified.

## Runtime

- run_dir: `reports/benchmark/runs/20260502T1831Z_phase22F_S7_combined_guard_smoke`
- api_url: `http://127.0.0.1:8028/v1`
- model: `hukuk-ai-poc`
- lane: `phase22f_s7m_shadow`
- runtime_provenance_git_sha: `9ca4e116f7a59921c2223d327a6d5e0243c467dd`
- runtime code SHA: `35ebca8b73d4964c8eb1d10f342c1d240863dd6e` plus report-only commits after runtime start
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- milvus_entity_count: `349403`
- vector_dimension: `1024`
- guardrails: `disabled`
- verification: `disabled`
- live_8000_untouched: `True`

## Commands

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8028/v1 \
  --model hukuk-ai-poc \
  --qids MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 \
    TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08 \
    CBG-01 CBG-02 CBG-03 CBG-04 \
    CBKAR-01 CBKAR-02 CBKAR-03 CBKAR-04 CBKAR-05 CBKAR-06 CBKAR-07 CBKAR-08 \
    YON-01 YON-02 YON-03 YON-04 YON-05 YON-06 YON-07 YON-08 YON-09 YON-10 \
    UY-07 UY-08 \
    KANUN-03 KANUN-04 KANUN-19 \
  --out-dir reports/benchmark/runs/20260502T1831Z_phase22F_S7_combined_guard_smoke \
  --timeout 420 --retries 0 --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260502T1831Z_phase22F_S7_combined_guard_smoke/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260502T1831Z_phase22F_S7_combined_guard_smoke
```

## Result

- total: `40`
- answered: `40`
- refused_or_empty: `0`
- errors: `0`
- contract_valid: `40/40`
- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- repealed_as_active_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- pass_proxy: `38/40`
- raw_score_proxy: `322.64 / 400`
- average_score_0_10_proxy: `8.07`

## Family Gates

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| MULGA | `>= 4/5` | `5/5` | PASS |
| TEBLIGLER | preferred `>= 7/8`, minimum `>= 6/8` | `7/8` | PASS |
| TEB-06 | PASS | PASS, `8.90` | PASS |
| CB_GENELGE | `4/4` | `4/4` | PASS |
| CB_KARAR | preferred `8/8`, minimum `>= 7/8` | `8/8` | PASS |
| YONETMELIK | preferred `9/10`, minimum `>= 7/10` | `9/10` | PASS |
| UY focused | no regression | `2/2` | PASS |
| KANUN relation | no regression | `3/3` | PASS |
| unsupported_confident_answer | `0` | `0` | PASS |
| answer_contract_invalid | `0` | `0` | PASS |
| source_key_v2_collision | `0` | `0` | PASS |
| binding_collision | `0` | `0` | PASS |
| repealed_as_active_count | `0` | `0` | PASS |

## Residual Proxy Fails

| QID | Family | Score | Claimed source | Failure classes |
| --- | --- | ---: | --- | --- |
| `TEB-04` | TEBLIGLER | 0.00 | `19631 m.0 / madde:0` | `auto_fail_triggered`, `missing_required_content_signal`, `partial_grounding_only` |
| `YON-04` | YONETMELIK | 3.25 | `madde:23` | `missing_gold_document_signal`, `missing_required_content_signal`, `wrong_document`, `partial_grounding_only` |

## Decision

Combined guard smoke passed the brief acceptance criteria. Full shadow benchmark may proceed.
