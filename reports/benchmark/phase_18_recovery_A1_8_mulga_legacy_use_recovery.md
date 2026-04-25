# Hukuk-AI Phase 18 Recovery A1.8-G MULGA Legacy-Use Recovery

## Decision

MULGA targeted recovery is accepted for rerun entry.

This change is systemic, not QID-specific. It fixes the class where a question asks whether an old dated source, temporary rule, or still-relied-upon historical source can be used for a current answer. Those queries must enter the `mulga_kanun` historical/repealed path even when the named document type is a regulation, tüzük, KHK, or university regulation.

Live `8000` was not touched. Candidate `8018` was restarted with the updated code.

## Runtime

- run_dir: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_mulga_smoke_after_legacy_use_fix`
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

## Smoke Result

| Metric | Result | Target |
|---|---:|---:|
| pass_proxy | 3/5 | >= 3/5 |
| raw_score_proxy | 26.25/50 | informational |
| wrong_family | 0 | no increase |
| repealed_as_active_count | 0 | 0 |
| unsupported_confident_answer_count | 0 | 0 |
| answer_contract_invalid_count | 0 | 0 |
| expected_family_prior_counts.mulga_kanun | 5/5 | 5/5 |

Per row:

| QID | Score | Status | Selected family | Selected document/article | Residual |
|---|---:|---|---|---|---|
| MULGA-01 | 0.00 | FAIL | MULGA | Askeri Yuksek Idare Mahkemesi repealed provisions, m.28 | wrong article / insufficient canonical span |
| MULGA-02 | 8.65 | PASS | MULGA | Devlet Arsiv Hizmetleri Hakkinda Yonetmelik, m.32 | partial grounding |
| MULGA-03 | 7.55 | PASS | MULGA | Turk Kanunu Medenisi repealed provisions, m.924 | partial grounding |
| MULGA-04 | 7.55 | PASS | MULGA | Markalarin Korunmasi Hakkinda KHK, m.42 | partial grounding |
| MULGA-05 | 2.50 | FAIL | MULGA | Gayrimenkul Kiralari repealed provisions, gec1 | wrong document/article |

## Code Change

The resolver now distinguishes two cases:

- Direct legacy-source application risk: old dated source, still relying on a source, temporary rule auto-application, or explicit old source used as current authority.
- Generic family coverage question: for example scanning old tüzük materials for compliance context, which should remain in the tüzük family rather than being forced to MULGA.

The fix also keeps active-current questions stable. Example: a current rent-increase question asking for the current TBK rule remains `kanun`, while a question asking why the temporary 25 percent cap is still auto-applied becomes `mulga_kanun`.

## Verification

Commands:

```text
cd api-gateway
.venv/bin/python -m py_compile src/source_family_resolver.py
.venv/bin/python -m pytest tests/test_chat_router.py -k "historical_scope_for_legacy_tuzuk or still_relying_on_old_regulation or named_regulation_still_reliance or old_dated_regulation_application or temporary_limit_auto_application or current_answer_over_temporary_limit or old_tuzuk_risk or university_exam_rights or banking_supervision or telecom_subscription or civil_mediation or rent_mediation" -q
```

Result:

```text
12 passed
```

Resolver sanity checks:

- named higher-education disciplinary regulation still-reliance risk -> `mulga_kanun`
- 1988 archive regulation application risk -> `mulga_kanun`
- 1994 Tapu Sicili Tüzüğü direct-use risk -> `mulga_kanun`
- explicit old 551/554/555/556 KHK use risk -> `mulga_kanun`
- temporary 25 percent cap auto-application risk -> `mulga_kanun`
- KHK-06 current KHK temporal-validity question without explicit old-source wording -> `khk`
- TUZUK-04 generic old-tüzük coverage question -> `tuzuk`
- current TBK rent-increase answer question -> `kanun`

## Next Step

Run the full 100 candidate gate again after committing this fix. Expected effect:

- `MULGA >= 3/5`
- `wrong_family` should drop below the `<= 15` hard gate if no other regression appears
- no live cutover until the full rerun and green lane both pass
