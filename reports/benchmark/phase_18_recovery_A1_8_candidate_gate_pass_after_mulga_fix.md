# Hukuk-AI Phase 18 Recovery A1.8 Candidate Gate Pass After MULGA Fix

## Decision

Candidate gate: `PASS`.

Live cutover: `NOT PERFORMED`.

The candidate on `8018` now satisfies the A1.8 full benchmark gate and the additional watch metrics. Controlled cutover can be reconsidered, but it still requires a separate live 20-QID smoke and then live full 100 confirmation before changing production serving.

Live `8000` remained untouched during this work.

## Run

- run_dir: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_full_candidate_rerun_after_mulga_fix`
- green_lane_dir: `reports/benchmark/green_lane/20260425T_phase18_recovery_A1_8_full_candidate_after_mulga_fix`
- timestamp_utc: `2026-04-25T20:19:48.403259+00:00`
- git_sha: `38046d6dd7003731ee936f36200f5c798fda64da`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- dirty_worktree: `True`
- api_url: `http://127.0.0.1:8018/v1`
- gateway_model_name: `hukuk-ai-poc`
- dgx_base_url: `http://192.168.12.243:30000/v1`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails_enabled: `false`
- presidio_enabled: `false`
- live_8000_untouched: `True`
- live_8000_collection: `mevzuat_e5_shadow`
- source_catalog_py_sha256: `f04dc600f306f5724c8e795fcf462bf601083e62250505686c3da55fb2a9016e`
- source_supplements_py_sha256: `11d0c2f29d399957095958fd894c87f1d7cabc6fda1f1719a269a07cd30196ce`

## Gate Result

| Metric | A1.7 | After Step E | After MULGA Fix | Target | Status |
|---|---:|---:|---:|---:|---|
| raw_score_proxy | 729.10 | 757.14 | 766.48 | >= 735 | PASS |
| pass_proxy | 71 | 77 | 80 | >= 73 | PASS |
| wrong_family | 17 | 16 | 11 | <= 15 | PASS |
| wrong_document | 17 | 12 | 12 | <= 15 | PASS |
| hallucinated_identifier | 24 | 20 | 16 | <= 23 | PASS |
| unsupported_confident_claim | 0 | 0 | 0 | <= 8 | PASS |
| contract_valid | 100/100 | 100/100 | 100/100 | 100/100 | PASS |
| green_lane | pass | pass | pass | PASS | PASS |
| corpus_materialization_required_count | 1 | 1 | 2 | <= 6 | PASS |
| canonical_span_materialized_count | 99 | 99 | 98 | >= 90 | PASS |

Operational counters:

- answer_contract_invalid_count: `0`
- unsupported_confident_answer_count: `0`
- repealed_as_active_count: `0`
- hallucinated_source_count: `12`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`

## Family Results

| Family | Pass | Count | Avg |
|---|---:|---:|---:|
| CB_GENELGE | 4 | 4 | 8.80 |
| CB_KARAR | 6 | 8 | 7.92 |
| CB_KARARNAME | 6 | 6 | 9.16 |
| CB_YONETMELIK | 4 | 6 | 6.82 |
| KANUN | 20 | 21 | 8.01 |
| KHK | 5 | 6 | 8.78 |
| KKY | 7 | 11 | 6.79 |
| MULGA | 3 | 5 | 5.25 |
| TEBLIGLER | 6 | 8 | 7.12 |
| TUZUK | 3 | 5 | 7.72 |
| UY | 10 | 10 | 9.19 |
| YONETMELIK | 6 | 10 | 6.27 |

Additional watch:

- `YONETMELIK pass >= 6/10`: PASS
- `MULGA pass >= 3/5`: PASS
- strong-family regressions absent for preserved Step E rows: PASS

## Critical Watch Rows

| QID | Score | Status | Family | Selected source |
|---|---:|---|---|---|
| UY-07 | 8.36 | PASS | UY | Kafkas University exam regulation, m.24 |
| UY-08 | 8.80 | PASS | UY | Yeni Yuzyil University double major/minor regulation, m.17 |
| KKY-10 | 8.99 | PASS | KKY | Tarife Yonetmeligi, m.4 |
| KANUN-21 | 7.89 | PASS | KANUN | HUAK, m.18 |
| KHK-06 | 6.80 | FAIL | KHK | Industrial designs KHK, m.3 |
| TUZUK-04 | 6.43 | FAIL | TUZUK | Food/public health qualities tüzük, m.699 |
| TUZUK-05 | 3.93 | FAIL | TUZUK | TMK velayet/vesayet/miras tüzük, m.1 |
| MULGA-02 | 8.65 | PASS | MULGA | Devlet Arsiv Hizmetleri Yonetmeligi, m.32 |
| MULGA-03 | 7.55 | PASS | MULGA | Turk Kanunu Medenisi repealed provisions, m.924 |
| MULGA-04 | 7.55 | PASS | MULGA | Markalarin Korunmasi Hakkinda KHK, m.42 |

## Residual Failures

The candidate still has 20 deterministic-proxy FAIL rows. These do not block the A1.8 cutover gate, but they remain the next quality backlog.

Dominant residual classes:

- KKY/YONETMELIK document identity: `KKY-02`, `KKY-03`, `KKY-04`, `YON-03`, `YON-04`, `YON-06`, `YON-08`
- CB authority/document selection: `CBY-03`, `CBY-04`, `CBKAR-03`, `CBKAR-08`
- KANUN/TEBLIG drift: `KANUN-12`, `TEB-06`, `TEB-07`
- remaining MULGA document/article precision: `MULGA-01`, `MULGA-05`
- known strong-family partial rows: `KHK-06`, `TUZUK-04`, `TUZUK-05`

## Interpretation

A1.8 recovered the candidate from `NO_CUTOVER` to candidate-gate pass:

- raw score improved by `+37.38` over A1.7
- pass count improved by `+9` over A1.7
- wrong_family improved by `-6` over A1.7
- wrong_document improved by `-5` over A1.7
- hallucinated_identifier improved by `-8` over A1.7
- MULGA recovered from `0/5` after Step E to `3/5`
- repealed-as-active dropped from `3` after Step E to `0`

The main blocker is now operational cutover validation, not candidate benchmark acceptance.

## Required Next Step

Do not switch live automatically.

Next controlled-cutover sequence:

1. Start a cutover candidate binding plan that maps live serving from `mevzuat_e5_shadow` to `mevzuat_faz1_shadow_20260418_compat1024`.
2. Before changing live, run a live-equivalent 20-QID smoke plan against the candidate configuration.
3. If the 20-QID smoke passes, perform controlled live switch.
4. Immediately run live 20-QID smoke on `8000`.
5. Then run live full 100 confirmation on `8000`.
6. Roll back if live metrics fail the same hard gate or if runtime provenance diverges from the candidate configuration.
