# Hukuk-AI Phase 18 Recovery A1.8-E Strong-Family Regression Guard

## Decision

A1.8-E is accepted for the targeted strong-family guard. Live `8000` remains untouched and no cutover is recommended from this step alone.

The guard objective was not to solve every historical weak row. It was to ensure that the strong-family rows previously passing in Phase17F did not regress after the YONETMELIK, MULGA, and KANUN remediation work.

Result:

| Run | Scope | Pass | Raw | Notes |
|---|---:|---:|---:|---|
| `20260425T_phase18_recovery_A1_8_strong_family_smoke_v1` | 8 QIDs | 0/8 | 34.99/80 | Pre-fix regression baseline |
| `20260425T_phase18_recovery_A1_8_strong_family_smoke_v2` | 8 QIDs | 2/8 | 50.76/80 | UY-07 and KKY-10 recovered |
| `20260425T_phase18_recovery_A1_8_uy08_probe_after_hierarchy_window` | UY-08 | 1/1 | 8.80/10 | Hierarchy/conflict article arbitration recovered |
| `20260425T_phase18_recovery_A1_8_strong_family_smoke_v3` | 8 QIDs | 3/8 | 52.76/80 | Final guard run |

Final v3 preserved all Phase17F PASS rows in this watch set:

| QID | Family | Phase17F | A1.8-E v3 | Status |
|---|---|---:|---:|---|
| `UY-07` | UY | 8.36 PASS | 8.36 PASS | preserved |
| `UY-08` | UY | 8.80 PASS | 8.80 PASS | preserved |
| `KKY-10` | KKY | 7.89 PASS | 8.99 PASS | improved |

Historical Phase17F FAIL rows remain mixed, but the guard did not create a new pass loss in the prior passing subset.

## Runtime Provenance

Final run:

- run_dir: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_strong_family_smoke_v3`
- timestamp_utc: `2026-04-25T19:05:52.075281+00:00`
- git_sha_at_run: `7e8f0f8a88b02967422ba903baa59566099e6c00`
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
- canonical_source_catalog_csv_sha256: `3e1a906ca1c0daaffc839b8757c6bdac25228d8f4e60f5001c2534a00fa309b2`
- source_supplements_py_sha256: `11d0c2f29d399957095958fd894c87f1d7cabc6fda1f1719a269a07cd30196ce`

## Final v3 Row Results

| QID | Phase17F | A1.8-E v3 | Selected family | Expected family | Selected document | Article | Main residual |
|---|---:|---:|---|---|---|---|---|
| `UY-07` | 8.36 PASS | 8.36 PASS | UY | UY | `KAFKAS UNIVERSITESI SARIKAMIS BEDEN EGITIMI VE SPOR YUKSEKOKULU GIRIS SINAVI, KAYIT, EGITIM - OGRETIM VE SINAV YONETMELIGI` | 24 | partial grounding |
| `UY-08` | 8.80 PASS | 8.80 PASS | UY | UY | `YENI YUZYIL UNIVERSITESI CIFT ANADAL VE YANDAL YONETMELIGI` | 17 | partial grounding |
| `KKY-10` | 7.89 PASS | 8.99 PASS | KKY | KKY | `TARIFE YONETMELIGI` | 4 | partial grounding |
| `KHK-06` | 6.80 FAIL | 6.80 FAIL | KHK | KHK | `ENDUSTRIYEL TASARIMLARIN KORUNMASI HAKKINDA KANUN HUKMUNDE KARARNAME` | 3 | historical fail preserved |
| `KKY-01` | 6.20 FAIL | 6.20 FAIL | YONETMELIK | KKY | `BANKALARIN BILGI SISTEMLERI VE ELEKTRONIK BANKACILIK HIZMETLERI HAKKINDA YONETMELIK` | 1 | KKY/YONETMELIK label bridge |
| `KKY-04` | 6.85 FAIL | 3.25 FAIL | KKY | KKY | `TARIM ISLETMELERI GENEL MUDURLUGU ANA STATUSU HAKKINDA KARAR (KARAR SAYISI: 5141)` | 13 | wrong document |
| `TUZUK-04` | 4.63 FAIL | 6.43 FAIL | TUZUK | TUZUK | `GIDA MADDELERININ VE UMUMI SAGLIGI ILGILENDIREN ESYA VE LEVAZIMIN HUSUSI VASIFLARINI GOSTEREN TUZUK` | 699 | historical fail improved |
| `TUZUK-05` | 3.25 FAIL | 3.93 FAIL | TUZUK | TUZUK | `TURK MEDENI KANUNUN VELAYET, VESAYET VE MIRAS HUKUMLERININ UYGULANMASINA DAIR TUZUK` | 1 | wrong document |

Final v3 summary:

- answer_contract_invalid_count: `0`
- unsupported_confident_answer_count: `0`
- hallucinated_source_count: `2`
- wrong_family: `1`
- wrong_document: `2`
- canonical_span_materialized_count: `8/8`
- corpus_materialization_required_count: `0`
- selector_exact_article_hit_rate: `0.75`
- selected_article_equals_claimed_article_rate: `0.75`

## Systemic Changes

No QID-specific rule was added.

Implemented systemic guard classes:

- Added hard-policy treatment for `kky`, `tuzuk`, and `khk` so these strong families are not overridden by softer generic family candidates.
- Added UY domain expansion for university exam rights, single-course exams, make-up exams, double-major/minor, and central/local higher-education conflict language.
- Added KKY domain expansion for banking supervision, SGK workplace-registration style questions, and BTK/mobile subscription tariff/cancellation questions.
- Added TUZUK handling so named legacy non-law document types such as old tüzük references are not misclassified as `mulga_kanun`.
- Added hierarchy/conflict article arbitration so questions asking which rule prevails do not select only generic scope/application articles when a conflict-resolution span is present in the same locked document.

## Verification

Commands:

```text
cd api-gateway
.venv/bin/python -m py_compile src/routers/chat.py src/source_family_resolver.py
.venv/bin/python -m pytest tests/test_chat_router.py -k "university_exam_rights or banking_supervision or telecom_subscription or old_tuzuk_risk or civil_mediation or rent_mediation" -q
```

Result:

```text
6 passed
```

## Residual Risks

- `KKY-04` remains unresolved and is worse than Phase17F on score. It was already a Phase17F FAIL, but should be tracked in the full A1.8 rerun because it is still a true wrong-document case.
- `KKY-01` still reports selected family as `YONETMELIK` while selecting the correct banking regulation document. This is a catalog/family-label bridge issue rather than a complete retrieval miss.
- `KHK-06` remains at the Phase17F score and still needs historical/current relation completeness work, but no new regression was introduced.
- `TUZUK-04` and `TUZUK-05` remain FAIL rows, but both are above their Phase17F scores and no longer show the original broad family collapse from v1.

## Next Step

Proceed to A1.8-F candidate full rerun on `8018` with `mevzuat_faz1_shadow_20260418_compat1024`.

Acceptance remains:

| Metric | Target |
|---|---:|
| raw_score_proxy | `>= 735` |
| pass_proxy | `>= 73` |
| wrong_family | `<= 15` |
| wrong_document | `<= 15` |
| hallucinated_identifier | `<= 23` |
| unsupported_confident_claim | `<= 8` |
| contract_valid | `100/100` |
| green_lane | `PASS` |
| corpus_materialization_required_count | `<= 6` |
| canonical_span_materialized_count | `>= 90` |

No live cutover should be performed before the full candidate rerun passes and then separate live smoke/full confirmation succeeds.
