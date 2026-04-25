# Phase 18 Recovery A1.8-C — MULGA Smoke

## Scope

- Instruction: `hukuk_ai_phase18_recovery_A1_8_targeted_family_document_remediation_brief.md`
- Step: A1.8-C `MULGA` active/repealed arbitration recovery
- Candidate gateway: `http://127.0.0.1:8018/v1`
- Live gateway: `8000` untouched
- Model: `hukuk-ai-poc`
- DGX base URL: `http://192.168.12.243:30000/v1`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Collection: `mevzuat_faz1_shadow_20260418_compat1024`

## Runtime Changes

- Added marker-preserving title n-grams for metadata lookup so titles containing `hakkinda`, `iliskin`, or `dair` are not collapsed into generic suffix matches.
- Added a historical title bridge for `MULGA` questions where preferred `mulga_kanun` chunks are absent but a strong non-law title match exists.
- Added legacy repeal-clause contract normalization: if a historical/repealed query with `MULGA` prior selects an active current source whose evidence span explicitly says the queried historical source was repealed, the answer contract claims `MULGA/repealed` instead of treating that active repeal source as the target source state.

No QID-specific rule was added.

## Verification

Commands:

```bash
api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/answer_contract_v2.py
scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8018/v1 --model hukuk-ai-poc --qids MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 --top-k 20 --max-tokens 1200 --timeout 180 --out-dir reports/benchmark/runs/20260425T_phase18_recovery_A1_8_mulga_smoke_v3
scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260425T_phase18_recovery_A1_8_mulga_smoke_v3/candidate_answers.csv --out-dir reports/benchmark/runs/20260425T_phase18_recovery_A1_8_mulga_smoke_v3
```

## Result

| Metric | A1.8-C Result | Target |
|---|---:|---:|
| MULGA pass_proxy | 3/5 | >=3/5 |
| repealed_as_active_count | 0 | 0 |
| wrong_family | 0 | no increase |
| raw_score_proxy | 26.25 / 50 | directional |

Per-row outcome:

| QID | Score | Pass | Selected Document | Contract Family/State |
|---|---:|---|---|---|
| MULGA-01 | 0.00 | FAIL | MİLLİ EĞİTİM BAKANLIĞININ TEŞKİLAT VE GÖREVLERİ HAKKINDA KANUN | MULGA / repealed |
| MULGA-02 | 8.65 | PASS | DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK, `33899 m.32` | MULGA / repealed |
| MULGA-03 | 7.55 | PASS | TÜRK KANUNU MEDENİSİNİN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ | MULGA / repealed |
| MULGA-04 | 7.55 | PASS | MARKALARIN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME | MULGA / repealed |
| MULGA-05 | 2.50 | FAIL | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ | MULGA / repealed |

## Decision

A1.8-C local acceptance passed. Continue to A1.8-D KANUN primary/supporting arbitration.

