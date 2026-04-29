# Phase 21C YONETMELIK Document Identity Audit

Source run:

```text
reports/benchmark/runs/20260428T_phase20F_full_after_C_D
```

This is an audit-only report. No runtime behavior is changed by this artifact.

## Summary

- audited_rows: `4`
- wrong_family_rows: `2`
- wrong_document_rows: `3`
- hallucinated_identifier_rows: `3`

## Root Cause Counts

| root_cause | count |
|---|---:|
| `cb_yonetmelik_boundary_false_positive` | 1 |
| `kky_boundary_false_positive` | 1 |
| `uy_boundary_false_positive` | 2 |

## Row Audit

| qid | selected_document | expected_document | failures | root_cause | recommended_fix_type |
|---|---|---|---|---|---|
| YON-04 | NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ | Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hale Getirilmesi Hakkında... | missing_gold_document_signal / missing_required_content_signal / wrong_document... | `kky_boundary_false_positive` | source_identity: prevent KKY bridge from displacing exact/strong YONETMELIK identity |
| YON-05 | ONDOKUZ MAYIS ÜNİVERSİTESİ TAŞINMAZLARININ İDARESİ HAKKINDA YÖNETMELİK | Planlı Alanlar İmar Yönetmeliği / 3194 sayılı İmar Kanunu | missing_gold_document_signal / missing_required_content_signal / wrong_document... | `uy_boundary_false_positive` | source_identity/source_family_resolver: require specific local university signal before U... |
| YON-06 | CEZA İNFAZ KURUMLARININ YÖNETİMİ İLE CEZA VE GÜVENLİK TEDBİRLERİNİN İNFAZI HAKK... | Konkordato Komiserliği Yönetmeliği / 2004 sayılı İcra ve İflas Kanunu | missing_gold_document_signal / missing_required_content_signal / wrong_family /... | `cb_yonetmelik_boundary_false_positive` | source_identity: require explicit CB authority signal before CB_YONETMELIK promotion |
| YON-08 | IŞIK ÜNİVERSİTESİ YATAY GEÇİŞ, ÇİFT ANADAL, YAN DAL VE KREDİ TRANSFERİ YÖNETMEL... | Yükseköğretim Kurumlarında Ön Lisans ve Lisans Düzeyindeki Programlar Arasında... | missing_required_content_signal / wrong_family / hallucinated_identifier / part... | `uy_boundary_false_positive` | source_identity/source_family_resolver: require specific local university signal before U... |

## Observations

- `YON-04` is a KKY/document collision: the selected nuclear-safety regulation is retained through family bridge despite the personal-data deletion/anonymization target.
- `YON-05` is a UY boundary false positive: a local university real-estate regulation is selected for a general imar/planned-area regulation question.
- `YON-06` is a CB_YONETMELIK boundary false positive: correction requires explicit CB authority gating and stronger Konkordato Komiserliği title/domain identity.
- `YON-08` is a UY boundary false positive: the local university regulation is selected while the question asks for both the national YOK regulation and local regulation.

## Recommended Phase 21C Runtime Fix Direction

- Strengthen general YONETMELIK document identity for strong title/domain phrases, without using QID-specific rules.
- Suppress UY displacement unless the query contains a specific local university signal or clearly asks for only local university rules.
- Suppress CB_YONETMELIK promotion unless explicit Cumhurbaşkanı/Cumhurbaşkanlığı authority signal exists.
- Prevent KKY bridge from retaining a wrong KKY document where a stronger YONETMELIK title/domain identity is available.
