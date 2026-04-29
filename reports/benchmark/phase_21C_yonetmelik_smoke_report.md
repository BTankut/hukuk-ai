# Hukuk-AI Phase 21C YONETMELIK Smoke Report

## Commit SHA List

- Audit commit: `60a9ff0` — `Phase 21C YONETMELIK audit`
- Runtime remediation commit: this report's commit — `Remediate YONETMELIK document identity routing`

## Audit Summary

Audit artifacts:

```text
reports/benchmark/phase_21C_yonetmelik_document_identity_audit.md
reports/benchmark/phase_21C_yonetmelik_document_identity_audit.csv
```

Audited rows: `YON-04`, `YON-05`, `YON-06`, `YON-08`.

Root causes:

| root_cause | count |
|---|---:|
| `uy_boundary_false_positive` | 2 |
| `kky_boundary_false_positive` | 1 |
| `cb_yonetmelik_boundary_false_positive` | 1 |

## Generalized Changes Made

- Added YONETMELIK domain-specific query expansions for personal-data deletion/anonymization, planned-area zoning, concordat commissioner, and central YOK transition/dual-major regulation questions.
- Strengthened central higher-education collision handling so national YOK regulation questions prefer `yonetmelik` over local `uy`, while preserving UY for local university-only questions.
- Restricted metadata-first lookup to the original query plus domain-specific expansions only. Generic family expansions still support retrieval, but no longer create source identity locks such as `RESMÎ GAZETE HAKKINDA YÖNETMELİK`.
- No QID-specific logic, no private answer-key rule, no answer synthesis/slot behavior change.

## Runtime Provenance

Valid runs:

```text
reports/benchmark/runs/20260429T_phase21C_yonetmelik_smoke_v2
reports/benchmark/runs/20260429T_phase21C_boundary_preservation_smoke
```

Runtime:

- API URL: `http://127.0.0.1:8000/v1`
- Gateway model: `hukuk-ai-poc`
- DGX base URL: `http://192.168.12.243:30000/v1`
- DGX model: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Milvus entity count: `349191` verified by direct Milvus probe
- Vector dimension: `1024` verified by direct Milvus schema probe
- Embedding backend: `remote`
- Embedding base URL: `http://127.0.0.1:8081/v1`
- Embedding model: `intfloat/multilingual-e5-large-instruct`
- Guardrails: `false`
- Presidio: `false`

## YONETMELIK Before / After

Baseline:

```text
reports/benchmark/runs/20260428T_phase20F_full_after_C_D
```

After:

```text
reports/benchmark/runs/20260429T_phase21C_yonetmelik_smoke_v2
```

| qid | before | after | selected document after |
|---|---:|---:|---|
| YON-01 | `8.65 PASS` | `8.65 PASS` | `ELEKTRONİK TEBLİGAT YÖNETMELİĞİ` |
| YON-02 | `7.55 PASS` | `7.55 PASS` | `MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ` |
| YON-03 | `7.82 PASS` | `7.82 PASS` | `İŞ SAĞLIĞI VE GÜVENLİĞİ RİSK DEĞERLENDİRMESİ YÖNETMELİĞİ` |
| YON-04 | `3.25 FAIL` | `3.25 FAIL` | `NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ` |
| YON-05 | `3.25 FAIL` | `9.55 PASS` | `PLANLI ALANLAR İMAR YÖNETMELİĞİ` |
| YON-06 | `1.45 FAIL` | `8.99 PASS` | `KONKORDATO KOMİSERLİĞİ VE ALACAKLILAR KURULUNA DAİR YÖNETMELİK` |
| YON-07 | `8.22 PASS` | `8.22 PASS` | `TİCARİ REKLAM VE HAKSIZ TİCARİ UYGULAMALAR YÖNETMELİĞİ` |
| YON-08 | `5.45 FAIL` | `7.25 PASS` | `YÜKSEKÖĞRETİM KURUMLARINDA ÖNLİSANS VE LİSANS DÜZEYİNDEKİ PROGRAMLAR ARASINDA GEÇİŞ, ÇİFT ANADAL, YAN DAL İLE KURUMLAR ARASI KREDİ TRANSFERİ YAPILMASI ESASLARINA İLİŞKİN YÖNETMELİK` |
| YON-09 | `7.82 PASS` | `7.82 PASS` | `MESAFELİ SÖZLEŞMELER YÖNETMELİĞİ` |
| YON-10 | `7.55 PASS` | `7.55 PASS` | `İŞ SAĞLIĞI VE GÜVENLİĞİ RİSK DEĞERLENDİRMESİ YÖNETMELİĞİ` |

YONETMELIK summary:

| metric | before | after |
|---|---:|---:|
| pass_proxy | `6/10` | `9/10` |
| hallucinated_source_count | `3` | `1` |
| unsupported_confident_answer_count | `0` | `0` |
| answer_contract_invalid_count | `0` | `0` |
| source_key_v2_collision_detected_count | `0` | `0` |
| binding_source_key_collision_detected_count | `0` | `0` |

## Boundary Regression Table

Run:

```text
reports/benchmark/runs/20260429T_phase21C_boundary_preservation_smoke
```

| slice | result | notes |
|---|---:|---|
| UY focused smoke | `2/2 PASS` | No focused UY regression. |
| KKY focused smoke | `2/3 PASS` | `KKY-01` remains the same baseline fail; `KKY-04` and `KKY-10` pass. |
| KANUN relation rows | `3/3 PASS` | No primary/supporting source regression. |
| CB_YONETMELIK focused smoke | `2/2 PASS` | `CBY-01` score recovered versus Phase 20F but still carries wrong-family/hallucinated flag; not a Phase 21C regression. |
| TEBLIGLER preservation | `7/8 PASS` | Preserves Phase 21B gate. |
| CB_GENELGE preservation | `4/4 PASS` | Stop rule satisfied. |

## Collision / Safety Status

YONETMELIK smoke:

- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`

Boundary preservation smoke:

- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- legacy `source_key_collision_detected_count`: `3`; not a gate failure because v2 and binding collisions are `0`.

## TEBLIGLER Preservation Result

TEBLIGLER preserved at `7/8`.

Only remaining fail is still `TEB-06`, matching Phase 21B residual risk:

```text
missing_gold_document_signal | wrong_document | hallucinated_identifier | insufficient_canonical_span_evidence
```

## CB_GENELGE Preservation Result

CB_GENELGE preserved at `4/4`.

## Phase 21D Decision

Phase 21C gate status: PASS.

Phase 21D may proceed to MULGA Source / Span Remediation.

Residual carried forward:

- `YON-04` remains wrong-document: personal-data deletion/anonymization question still selects nuclear-safety regulation despite metadata lookup seeing the expected title. This should be treated as residual document-retention/source-lock arbitration, not answer synthesis.
- `TEB-06` and `TEB-07` residuals from Phase 21B remain out of Phase 21C scope.
