# Phase 18 Recovery A1.5 Environment/Data Parity Report

## Scope

This report executes `hukuk_ai_phase18_recovery_A1_5_environment_data_parity_brief.md`.

Phase 18 code ablation remains stopped. The objective was to determine whether the Phase 17F regression reproduces because of code changes or because the current runtime/data/index/catalog environment no longer matches the original Phase 17F behavior.

## Artifacts Produced

- `scripts/benchmark/run_hukuk_ai_100.py`: now writes `runtime_provenance.json` and `runtime_provenance.md` for every benchmark run.
- `scripts/benchmark/validate_hukuk_ai_100_run.py`: now supports `--require-provenance`.
- `scripts/benchmark/compare_run_traces.py`: row-level run comparison tool.
- `scripts/benchmark/audit_runtime_parity.py`: current gateway/model/Milvus/embedding/runtime audit tool.
- `scripts/benchmark/audit_source_catalog_parity.py`: current checkout vs Phase 17F checkout source/catalog/config hash audit tool.
- `reports/benchmark/phase_18_recovery_phase17f_vs_currentenv_trace_diff.md`
- `reports/benchmark/phase_18_recovery_phase17f_vs_currentenv_trace_diff.csv`
- `reports/benchmark/phase_18_recovery_runtime_parity.md`
- `reports/benchmark/phase_18_recovery_runtime_parity.json`
- `reports/benchmark/phase_18_recovery_source_catalog_parity.md`
- `reports/benchmark/phase_18_recovery_source_catalog_parity.csv`

Smoke proof for provenance writing was run at:

- `reports/benchmark/runs/20260425T_phase18_recovery_A1_5_provenance_smoke`

The smoke run is under the ignored benchmark runs directory and was not committed.

## Runtime Binding Finding

The active `hukuk-ai-poc` endpoint is currently bound to the fine-tuned merged DGX runtime, not baseline:

- Gateway API: `http://127.0.0.1:8000/v1`
- Gateway model id: `hukuk-ai-poc`
- DGX base URL: `http://192.168.12.243:30000/v1`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- DGX `/models` response includes: `/models/merged_model_fabric_stage_20260321`
- Guardrails: `false`
- Presidio: `false`
- Embedding backend: `remote`
- Embedding base URL: `http://127.0.0.1:8081/v1`
- Milvus collection: `mevzuat_e5_shadow`
- Milvus entity count: `12923`

Conclusion: this is not currently a baseline-vs-merged model binding mistake. The model lane is the expected fine-tuned merged lane.

Note: runtime provenance records `dirty_worktree=True`. The report intentionally does not stage unrelated existing dirty files; the dirty state is recorded as evidence, not normalized away.

## Row-Level Regression Finding

The trace diff compares the same 20 QIDs:

- Left: original Phase 17F full run artifact, subset to the 20 A0 QIDs.
- Right: Phase 17F code re-run in the current environment.

Results:

| Metric | Original Phase 17F Answers | Phase 17F Code Current Env |
|---|---:|---:|
| Compared subset score | `141.18 / 200` | `88.77 / 200` |
| Compared subset pass | `14 / 20` | `6 / 20` |
| Degraded rows | - | `14 / 20` |

Highest drift fields:

- `selected_document_id`: changed in `18/20`
- `source_title_claimed`: changed in `18/20`
- `source_identifier_claimed`: changed in `17/20`
- `source_family_claimed`: changed in `11/20`
- `document_match_score`: changed in `15/20`
- `pass_fail_proxy`: changed in `12/20`

Representative regressions:

- `KANUN-01`: `İŞ KANUNU / IK m.18` became `HUKUK MUHAKEMELERİ KANUNU / HMK m.452`.
- `MULGA-02`: expected repealed/security investigation source became `HUKUK MUHAKEMELERİ KANUNU`.
- `CBKAR-01`: expected `İTHALAT REJİMİ KARARINA EK KARAR (1362)` became no selected document.
- `TEB-01`: expected `KAMU İHALE GENEL TEBLİĞİ` became no selected document.
- `YON-03`: expected regulation source became `TÜRK TİCARET KANUNU / TTK m.1445`.

Conclusion: this is source/document selection drift, not scorer drift.

## Milvus Content Finding

The active collection is reachable and has a valid schema:

- fields: `id`, `text`, `embedding`, `metadata`
- embedding dimension: `1024`
- index: `embedding`
- queried rows in audit: `12875`
- entity count from stats: `12923`

However, the collection content does not represent the full 100-question mevzuat source universe. Top family/short-name distribution in the current collection:

- `TTK`: `5139`
- `TMK`: `2093`
- `CMK`: `1547`
- `HMK`: `1506`
- `TCK`: `1392`
- `İİK`: `1198`

The audit did not find the mandatory drift-target sources in the active collection:

| QID | Expected Source Class | Visible In Current Milvus |
|---|---|---:|
| `MULGA-02` | `MULGA` | `False` |
| `CBKAR-01` | `CB_KARAR` | `False` |
| `YON-01` | `YONETMELIK` | `False` |
| `KANUN-01` | `KANUN / İş Kanunu` | `False` |
| `TEB-01` | `TEBLIGLER` | `False` |
| `CBG-01` | `CB_GENELGE` | `False` |
| `CBG-02` | `CB_GENELGE` | `False` |

The current collection also has:

- `canonical_source_key_v2_present_count`: `0`
- `canonical_article_id_present_count`: `12875`
- `body_text_present_count`: `12875`

Conclusion: the primary blocker is `milvus_collection_or_content_drift`. The current serving collection is effectively a narrow primary-law collection, not the full mevzuat benchmark collection needed for the Phase 17F behavior.

## Source Catalog / Supplement Finding

Current checkout vs Phase 17F checkout source/catalog parity:

- Compared files: `31`
- Match: `24`
- Hash diff: `5`
- Presence diff: `2`

Stable areas:

- `primary_source_text`: `12/12` matched.
- `benchmark_catalog_reports`: `8/8` matched.

Changed/missing areas:

- `api-gateway/src/rag/source_catalog.py`: hash diff.
- `api-gateway/src/source_family_resolver.py`: hash diff.
- `api-gateway/src/rag/source_supplements.py`: hash diff.
- `api-gateway/src/rag/required_slot_matrix.py`: current-only.
- `api-gateway/src/rag/required_slot_matrix.json`: current-only.
- `scripts/benchmark/run_hukuk_ai_100.py`: hash diff, expected because A1.5 provenance was added.
- `scripts/benchmark/score_hukuk_ai_100.py`: hash diff.

Conclusion: source/catalog code drift exists, but the stronger immediate failure is that expected full-mevzuat families and documents are absent from the active Milvus collection.

## Root Cause Assignment

Primary category:

- `milvus_collection_or_content_drift`

Secondary categories:

- `source_catalog_drift`
- `source_supplement_drift`
- `runtime_config_drift` only in the sense that the current runtime is bound to a collection that is not complete for the 100-question benchmark.

Rejected as primary causes:

- `scorer_drift`: rejected by A0 rescore.
- `baseline_model_binding`: rejected by current runtime provenance.
- `guardrail_blocking`: rejected for current benchmark lane because guardrails are disabled.

## Decision

Do not resume Phase 18 ablation yet.

The next corrective step is to restore or rebuild an authoritative full-mevzuat Milvus collection that includes the benchmark families and documents, with canonical source-key metadata coverage. After that, re-run the Phase 17F-code 20-QID smoke in the same current merged model lane.

Minimum gate before returning to Phase 18 ablation:

- 20-QID smoke score: `>= 130 / 200`
- pass: `>= 12 / 20`
- wrong family: `<= 2`
- wrong document: `<= 5`

Until that gate is met, further Phase 18 code cherry-picks would be measuring the wrong collection, not the intended application behavior.
