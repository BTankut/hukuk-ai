# Phase 22F-S7 TEB Targeted Smoke Report

Generated: 2026-05-02T17:50:00Z

## Runtime

- API URL: `http://127.0.0.1:8027/v1`
- Lane: `phase22f_s7_shadow`
- Model: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Vector dimension: `1024`
- Live `8000` untouched: `True`
- Guardrails: `disabled`
- Verification: `disabled`
- Git SHA: `2163451f462b3ddbf996b691b84dfc574288bda5`

Run directory:

`reports/benchmark/runs/20260502T1745Z_phase22F_S7_teb_targeted_smoke`

Commands:

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8027/v1 --model hukuk-ai-poc --qids TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08 --out-dir reports/benchmark/runs/20260502T1745Z_phase22F_S7_teb_targeted_smoke --timeout 420 --retries 0 --sleep 0.2
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260502T1745Z_phase22F_S7_teb_targeted_smoke/candidate_answers.csv --out-dir reports/benchmark/runs/20260502T1745Z_phase22F_S7_teb_targeted_smoke
```

## Summary

- Total: `8`
- Answered: `8`
- Refused or empty: `0`
- Errors: `0`
- Missing trace: `0`
- Contract valid: `8`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Source-key collision: `0`
- Source-key-v2 collision: `0`
- Binding source-key collision: `0`
- Proxy pass: `7/8`
- Average proxy score: `7.61`
- TEBLIGLER family match: `8/8`

## Row Results

| qid | proxy | score | claimed source | metadata lookup |
| --- | --- | ---: | --- | --- |
| TEB-01 | PASS | 8.80 | `13354 m.78` / KAMU İHALE GENEL TEBLİĞİ | `normalized_title_lookup` |
| TEB-02 | PASS | 9.10 | `11990 m.1` / TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ | `exact_identifier_lookup` |
| TEB-03 | PASS | 8.00 | `33905 m.0` / VERGİ USUL KANUNU GENEL TEBLİĞİ (SIRA NO: 509) | `exact_identifier_lookup` |
| TEB-04 | FAIL | 0.00 | `19631 m.0` / KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ | `teb_kdv_source_identity_lookup` |
| TEB-05 | PASS | 8.99 | `18477 m.2` / SERMAYE PİYASASINDA FİNANSAL RAPORLAMAYA İLİŞKİN ESASLAR TEBLİĞİ | none |
| TEB-06 | PASS | 8.90 | `23093 m.1` / ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ | `normalized_title_lookup` |
| TEB-07 | PASS | 7.52 | `unknown` / MUHASEBAT GENEL MÜDÜRLÜĞÜ GENEL TEBLİĞİ (SIRA NO: 81) | `exact_identifier_lookup` |
| TEB-08 | PASS | 9.55 | `39511 m.1` / POSTA VE HIZLI KARGO YOLUYLA TAŞINAN EŞYANIN GÜMRÜK İŞLEMLERİNE İLİŞKİN TEBLİĞ | `title_ngram_family_lookup` |

## TEB-04 Source Identity

S7 target succeeded for source identity:

- `metadata_lookup_hit=True`
- `metadata_lookup_source=teb_kdv_source_identity_lookup`
- `selected_source_keys=["19631"]`
- `teb_kdv_signal_detected=True`
- `teb_kdv_candidate_injected=True`
- `teb_kdv_candidate_source_key=19631`
- `teb_kdv_candidate_injection_reason=kdv_teblig_operational_signal_bundle`
- `source_identifier_claimed=19631 m.0`
- `source_title_claimed=KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ`
- `selected_document_rank_after_identity_rerank=1`

The remaining `TEB-04` proxy failure is `auto_fail_triggered | missing_required_content_signal | partial_grounding_only`. That is not a source-selection failure anymore; it belongs to grounding/content/rubric handling after the correct KDV teblig source is selected.

## Acceptance

- `TEB-04` source identity improved to `19631`: `PASS`
- `TEBLIGLER >= 7/8`: `PASS`
- `TEB-06` remains PASS: `PASS`
- No adjacent TEB row drifted to `19631`: `PASS`
- `unsupported_confident_answer=0`: `PASS`
- `answer_contract_invalid=0`: `PASS`
- source-key collision and binding collision remain `0`: `PASS`

S7 targeted smoke gate passed. Combined guard may proceed after the independent S7M MULGA targeted gate passes.
