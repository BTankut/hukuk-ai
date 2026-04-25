# Hukuk-AI Phase 18 Recovery A1.8-F Full Candidate Rerun After Step E

## Decision

`NO_CUTOVER`.

A1.8-F shows a large recovery over A1.7, but the candidate still does not fully satisfy the cutover gate. Live `8000` must remain unchanged.

The primary hard gate misses by one metric:

- `wrong_family = 16`, target `<= 15`

The additional watch also fails:

- `MULGA = 0/5`, target `>= 3/5`

Everything else in the hard gate is green.

## Run

- run_dir: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_full_candidate_rerun_after_stepE`
- green_lane_dir: `reports/benchmark/green_lane/20260425T_phase18_recovery_A1_8_full_candidate_after_stepE`
- timestamp_utc: `2026-04-25T19:12:43.081787+00:00`
- git_sha: `7be251dc63066b80638c34c92f0ea74a40333ba3`
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
- embedding_model: `intfloat/multilingual-e5-large-instruct`
- guardrails_enabled: `false`
- presidio_enabled: `false`
- live_8000_untouched: `True`
- live_8000_collection: `mevzuat_e5_shadow`
- source_catalog_py_sha256: `f04dc600f306f5724c8e795fcf462bf601083e62250505686c3da55fb2a9016e`
- source_supplements_py_sha256: `11d0c2f29d399957095958fd894c87f1d7cabc6fda1f1719a269a07cd30196ce`

## Gate

| Metric | A1.7 | A1.8-F | Target | Status |
|---|---:|---:|---:|---|
| raw_score_proxy | 729.10 | 757.14 | >= 735 | PASS |
| pass_proxy | 71 | 77 | >= 73 | PASS |
| wrong_family | 17 | 16 | <= 15 | FAIL |
| wrong_document | 17 | 12 | <= 15 | PASS |
| hallucinated_identifier | 24 | 20 | <= 23 | PASS |
| unsupported_confident_claim | 0 | 0 | <= 8 | PASS |
| contract_valid | 100/100 | 100/100 | 100/100 | PASS |
| green_lane | pass | pass | PASS | PASS |
| corpus_materialization_required_count | 1 | 1 | <= 6 | PASS |
| canonical_span_materialized_count | 99 | 99 | >= 90 | PASS |

Operational quality:

- answer_contract_invalid_count: `0`
- unsupported_confident_answer_count: `0`
- hallucinated_source_count: `12`
- repealed_as_active_count: `3`
- score average: `7.57/10`
- pass/fail: `77/23`

## Family Results

| Family | Pass | Count | Avg |
|---|---:|---:|---:|
| CB_GENELGE | 4 | 4 | 8.80 |
| CB_KARAR | 6 | 8 | 7.92 |
| CB_KARARNAME | 6 | 6 | 9.16 |
| CB_YONETMELIK | 4 | 6 | 6.72 |
| KANUN | 20 | 21 | 8.01 |
| KHK | 5 | 6 | 8.78 |
| KKY | 7 | 11 | 6.79 |
| MULGA | 0 | 5 | 3.49 |
| TEBLIGLER | 6 | 8 | 7.12 |
| TUZUK | 3 | 5 | 7.72 |
| UY | 10 | 10 | 9.19 |
| YONETMELIK | 6 | 10 | 6.27 |

Additional watch:

- `YONETMELIK pass >= 6/10`: PASS
- `MULGA pass >= 3/5`: FAIL
- strong-family regressions absent for the preserved Step E rows: PASS

## Strong-Family Watch

| QID | Score | Status | Selected family | Selected document/article |
|---|---:|---|---|---|
| UY-07 | 8.36 | PASS | UY | Kafkas University exam regulation, m.24 |
| UY-08 | 8.80 | PASS | UY | Yeni Yuzyil University double major/minor regulation, m.17 |
| KKY-10 | 8.99 | PASS | KKY | Tarife Yonetmeligi, m.4 |
| KKY-01 | 6.20 | FAIL | YONETMELIK | Banking information systems/e-banking regulation, m.1 |
| KKY-04 | 3.25 | FAIL | KKY | TIGEM ana statu karar, m.13 |
| KHK-06 | 6.80 | FAIL | KHK | Industrial designs KHK, m.3 |
| TUZUK-04 | 6.43 | FAIL | TUZUK | Food/public health qualities tüzük, m.699 |
| TUZUK-05 | 3.93 | FAIL | TUZUK | TMK velayet/vesayet/miras tüzük, m.1 |

KANUN relation fixes remained stable:

- `KANUN-02`: 7.55 PASS, selected Is Kanunu m.41.
- `KANUN-19`: 8.65 PASS, selected Tebligat Kanunu m.1.
- `KANUN-21`: 7.89 PASS, selected HUAK m.18.

## Main Remaining Failures

The hard gate now fails narrowly on `wrong_family`, but the dominant legal risk is still `MULGA`.

MULGA rows:

| QID | Score | Selected family | Issue |
|---|---:|---|---|
| MULGA-01 | 4.17 | UY | repealed source used as active |
| MULGA-02 | 0.00 | YONETMELIK | repealed source used as active, auto fail |
| MULGA-03 | 6.85 | TUZUK | wrong family but partial evidence |
| MULGA-04 | 5.75 | KHK | wrong family but partial evidence |
| MULGA-05 | 0.70 | KANUN | wrong document/article, repealed source used as active |

Wrong-family rows are concentrated in:

- all `MULGA` rows: 5 rows
- KKY/YONETMELIK boundary: `KKY-01`, `KKY-02`, `KKY-03`, `KKY-07`, `YON-03`, `YON-08`
- CB authority boundary: `CBY-01`, `CBY-04`, `CBKAR-05`
- supporting law/teblig drift: `KANUN-12`, `TEB-07`

## Interpretation

A1.8 remediation moved the candidate above the main score/pass thresholds:

- raw score improved by `+28.04`
- pass count improved by `+6`
- wrong_document improved by `-5`
- hallucinated_identifier improved by `-4`
- KANUN improved to `20/21`
- UY reached `10/10`
- YONETMELIK reached the explicit `6/10` watch target

The remaining blocker is not broad corpus materialization. It is source-state/family arbitration around repealed or historical materials, plus a small number of boundary-label cases.

## Recommendation

Do not cut over.

Next remediation should be systemic and narrow:

- Fix `MULGA` first because it alone can clear the additional watch and likely reduce `wrong_family` below the hard gate.
- Treat `repealed_source_used_as_active` as a hard arbitration defect when historical/repealed intent is detected.
- Strengthen `mulga_kanun` internal identity so repealed-law aliases are not scored or served as active KANUN/YONETMELIK/UY/KHK/TUZUK families.
- After MULGA recovery, rerun the full candidate gate before touching live `8000`.

No live cutover should be considered until:

- `wrong_family <= 15`
- `MULGA >= 3/5`
- green lane remains pass
- full 100 rerun stays above all hard thresholds
