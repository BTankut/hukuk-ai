# Phase 22F-S7M MULGA Targeted Smoke Report

## Scope

Phase 22F-S7M targeted smoke was run only against the shadow runtime. Live `8000` and live/base Milvus collections were not modified.

## Runtime

- run_dir: `reports/benchmark/runs/20260502T1827Z_phase22F_S7M_mulga_targeted_smoke`
- api_url: `http://127.0.0.1:8028/v1`
- model: `hukuk-ai-poc`
- lane: `phase22f_s7m_shadow`
- git_sha: `35ebca8b73d4964c8eb1d10f342c1d240863dd6e`
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
  --out-dir reports/benchmark/runs/20260502T1827Z_phase22F_S7M_mulga_targeted_smoke \
  --timeout 420 --retries 0 --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260502T1827Z_phase22F_S7M_mulga_targeted_smoke/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260502T1827Z_phase22F_S7M_mulga_targeted_smoke
```

## Result

- answered: `5/5`
- refused_or_empty: `0`
- errors: `0`
- contract_valid: `5/5`
- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- repealed_as_active_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- pass_proxy: `5/5`
- raw_score_proxy: `40.77 / 50`
- average_score_0_10_proxy: `8.15`

## Row Outcomes

| QID | Proxy | Score | Claimed family | Claimed identifier | Claimed article | Effective state | Guard |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `MULGA-01` | PASS | 8.37 | MULGA | `2547 m.54` | `madde:54` | repealed | `relation_chain_controlled_historical_claim` |
| `MULGA-02` | PASS | 9.10 | MULGA | `33899` | `madde:32` | repealed | `mulga_historical_repeal_proof_guard` |
| `MULGA-03` | PASS | 8.65 | MULGA | `20135150 m.90` | `madde:90` | repealed | `mulga_historical_repeal_proof_guard` |
| `MULGA-04` | PASS | 7.55 | MULGA | `555` | `madde:18` | repealed | `mulga_historical_repeal_proof_guard` |
| `MULGA-05` | PASS | 7.10 | MULGA | `6570 m.gec1` | `madde:344` | repealed | `mulga_dual_role_current_law_basis_guard` |

## Acceptance

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| MULGA pass count | `>= 4/5` | `5/5` | PASS |
| MULGA-05 improves or PASS | improve or PASS | PASS | PASS |
| repealed_as_active_count | `0` | `0` | PASS |
| unsupported_confident_answer | `0` | `0` | PASS |
| answer_contract_invalid | `0` | `0` | PASS |
| source_key_v2_collision | `0` | `0` | PASS |
| binding_collision | `0` | `0` | PASS |

## Notes

The accepted S7M behavior is role-separated, not QID-specific:

- `MULGA-02/03/04` use a title/identifier/query-matched historical repeal proof guard for active repeal or legacy evidence that otherwise surfaced as active primary law.
- `MULGA-05` keeps the primary historical family as `MULGA`, keeps `6570 m.gec1` as the historical identifier, and exposes `TBK m.344` as the separate current-law basis.
- The answer surface avoids exposing internal proof-reason diagnostics; those remain in trace/contract fields.

## Decision

Phase 22F-S7M targeted smoke gate passed. Combined guard smoke may proceed because both S7 and S7M targeted gates have passed.
