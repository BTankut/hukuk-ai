# Phase 24HY-A Source-Selection Replacement Failure Audit

Generated: 2026-05-08

## Inputs

- `reports/benchmark/phase_24HX_A_regression_slice_audit.csv`
- `reports/benchmark/phase_24HX_E_family_slice_validation_smoke.csv`
- `reports/benchmark/runs/phase_24HX_E_family_slice_validation_smoke`
- `reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z` for base-selected source comparison.

## Summary

- audited_rows: `29`
- source_replaced_rows: `1`
- wrong_document_after_replacement_rows: `13`
- hallucinated_identifier_after_replacement_rows: `17`
- safe_replacement_should_have_been_blocked_rows: `1`

## Classification Counts

| classification | count |
| --- | ---: |
| `safe_replacement` | 12 |
| `unsafe_replacement` | 0 |
| `supporting_only_should_not_replace` | 0 |
| `no_replacement_but_claim_surface_drift` | 17 |
| `trace_insufficient` | 0 |

## Failure Pattern

The dominant failure is not a clean source replacement that can be accepted as stronger than base. The failing rows show either direct primary source replacement into a wrong document, or unchanged selected-document surface with claimed family/identifier/article drift. Both patterns require a fail-closed guard before answer-contract synthesis.

A candidate should be allowed to replace the base primary source only when metadata identity lock, family/domain compatibility, role compatibility, and article/span support are all stronger or at least preserved. Otherwise the base source must be retained and the candidate may only be added as role-compatible supporting evidence.

## High-Risk Rows

| qid | family | classification | base source | candidate source | candidate id | article | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `YON-05` | `target` | `no_replacement_but_claim_surface_drift` | İMAR KANUNU | İMAR KANUNU | `3194 m.18` | `madde:18` | disabled |
| `KANUN-08` | `target` | `no_replacement_but_claim_surface_drift` | ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN TÜKETİCİ HAKLARI YÖNETMELİĞİ | ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN TÜKETİCİ HAKLARI YÖNETMELİĞİ | `` | `madde:12` | disabled |
| `CBY-01` | `CBY` | `no_replacement_but_claim_surface_drift` | ELEKTRONİK İMZA KANUNUNUN UYGULANMASINA İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK | ELEKTRONİK İMZA KANUNUNUN UYGULANMASINA İLİŞKİN USUL VE ESASLAR HAKKINDA YÖNETMELİK | `7224` | `madde:1` | disabled |
| `CBY-02` | `CBY` | `no_replacement_but_claim_surface_drift` | KAMU İHALE KURUMU TEŞKİLATI VE PERSONELİNİN ÇALIŞMA USUL VE ESASLARI HAKKINDA YÖNETMELİK | KAMU İHALE KURUMU TEŞKİLATI VE PERSONELİNİN ÇALIŞMA USUL VE ESASLARI HAKKINDA YÖNETMELİK | `200915611 m.17` | `madde:17` | disabled |
| `CBY-04` | `CBY` | `no_replacement_but_claim_surface_drift` | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CUMHURBAŞKANLIĞI KARARNAMESİ (KARARNAME NUMARASI: 11) | `11` | `madde:10` | disabled |
| `KANUN-04` | `KANUN` | `no_replacement_but_claim_surface_drift` | KİŞİSEL VERİLERİN KORUNMASI KANUNU | KİŞİSEL VERİLERİN KORUNMASI KANUNU | `KVKK m.6` | `madde:6` | disabled |
| `KANUN-05` | `KANUN` | `no_replacement_but_claim_surface_drift` | KİŞİSEL VERİLERİN KORUNMASI KANUNU | KİŞİSEL VERİLERİN KORUNMASI KANUNU | `KVKK m.6` | `madde:6` | disabled |
| `KANUN-06` | `KANUN` | `no_replacement_but_claim_surface_drift` | TÜRK TİCARET KANUNU | TÜRK TİCARET KANUNU | `TTK m.595` | `madde:595` | disabled |
| `KANUN-11` | `KANUN` | `no_replacement_but_claim_surface_drift` | BELEDİYE KANUNU | BELEDİYE KANUNU | `5393 m.47` | `madde:47` | disabled |
| `KANUN-14` | `KANUN` | `no_replacement_but_claim_surface_drift` | TÜRK BORÇLAR KANUNU | TÜRK BORÇLAR KANUNU | `TBK m.227` | `madde:227` | disabled |
| `KANUN-16` | `KANUN` | `no_replacement_but_claim_surface_drift` | TÜRK TİCARET KANUNU | TÜRK TİCARET KANUNU | `TTK m.4` | `madde:4` | disabled |
| `KANUN-17` | `KANUN` | `no_replacement_but_claim_surface_drift` | İCRA VE İFLAS KANUNU | İCRA VE İFLAS KANUNU | `İİK m.290` | `madde:290` | disabled |
| `KANUN-18` | `KANUN` | `no_replacement_but_claim_surface_drift` | İŞ KANUNU | İŞ KANUNU | `IK m.56` | `madde:56` | disabled |
| `KANUN-20` | `KANUN` | `no_replacement_but_claim_surface_drift` | TÜRK MEDENİ KANUNU | TÜRK MEDENİ KANUNU | `TMK m.571` | `madde:571` | disabled |
| `KKY-11` | `KKY` | `no_replacement_but_claim_surface_drift` | JANDARMA GENEL KOMUTANLIĞI VE SAHİL GÜVENLİKKOMUTANLIĞI KURUM KİMLİK KARTI YÖNETMELİĞİ | JANDARMA GENEL KOMUTANLIĞI VE SAHİL GÜVENLİKKOMUTANLIĞI KURUM KİMLİK KARTI YÖNETMELİĞİ | `31039 m.6` | `madde:6` | disabled |
| `UY-07` | `UY` | `no_replacement_but_claim_surface_drift` | DİCLE ÜNİVERSİTESİ DİŞ HEKİMLİĞİ FAKÜLTESİ EĞİTİM-ÖĞRETİM SINAV VE KLİNİK DERS YÜKÜ PRATİK... | DİCLE ÜNİVERSİTESİ DİŞ HEKİMLİĞİ FAKÜLTESİ EĞİTİM-ÖĞRETİM SINAV VE KLİNİK DERS YÜKÜ PRATİK... | `18872 m.20` | `madde:20` | disabled |
| `TUZUK-04` | `guard` | `no_replacement_but_claim_surface_drift` | RADYASYON GÜVENLİĞİ TÜZÜĞÜ | RADYASYON GÜVENLİĞİ TÜZÜĞÜ | `859727 m.4` | `madde:4` | disabled |

## Required Guard Implications

- Replacement must be attempted-aware: candidate-vs-base primary source keys should be compared before rerank/focus output becomes the answer-contract source.
- Supporting/current-law/historical evidence must not mutate claimed primary family, identifier, or article when the selected primary source is unchanged.
- Weak metadata title/domain hits must not become primary source locks; they should be discarded or retained only as supporting evidence.
- KANUN same-family replacements require positive domain and identity improvement, not merely family match.
- TEBLIGLER active sources must not be rewritten by historical or repealed material.
- Ambiguous TUZUK hierarchy queries must not force an arbitrary concrete tüzük identity.

Detailed CSV: `reports/benchmark/phase_24HY_A_source_selection_replacement_failure_audit.csv`
