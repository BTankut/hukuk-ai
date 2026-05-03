# Phase 24B Legal / Scorer Review Packet

Generated: 2026-05-03T10:35:00Z

Scope: closed-ended legal/scorer review packet for residual rows requiring taxonomy, rubric, or legal framing review. This packet does not change runtime behavior and does not authorize QID-specific rules.

Input evidence:

- `reports/benchmark/phase_24A_residual_triage.csv`
- `reports/benchmark/runs/20260503T091350Z_phase23R_E6_stability_full/candidate_answers.csv`
- `reports/benchmark/runs/20260503T091350Z_phase23R_E6_stability_full/scored.csv`

Output CSV: `reports/benchmark/phase_24B_legal_scorer_review_packet.csv`

## Review Rows

| QID | Claimed Family | Claimed Identifier | Selected Source | Expected Decision Enum | Runtime Patch Allowed |
|---|---|---|---|---|---|
| CBY-04 | CB_KARARNAME | 11 m.10 | DEVLET ARŞİVLERİ BAŞKANLIĞI HAKKINDA CBK / 11 m.10/f.0 | legal_taxonomy_confirmed | false |
| CBY-06 | CB_YONETMELIK | 20046801 m.14 | KAMU KURUM VE KURULUŞLARI PERSONEL SERVİS HİZMET YÖNETMELİĞİ / 20046801 m.14/f.0 | scorer_rubric_mismatch | false |
| KKY-01 | YONETMELIK | 34360 m.1 | BANKALARIN BİLGİ SİSTEMLERİ VE ELEKTRONİK BANKACILIK HİZMETLERİ HAKKINDA YÖNETMELİK / 34360 m.1/f.0 | benchmark_item_ambiguous | false |
| TEB-04 | TEBLIGLER | 19631 m.0 | KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ / 19631 m.0/f.0 | scorer_rubric_mismatch | false |
| TUZUK-04 | TUZUK | 859727 m.4 | RADYASYON GÜVENLİĞİ TÜZÜĞÜ / 859727 m.4/f.0 | needs_more_review | false |

## Closed Questions

| QID | Legal Question | Scorer Question |
|---|---|---|
| CBY-04 | Should the primary source for archive retention/selection/transfer/destruction workflow be a CB yönetmelik with CBK 11 only as institutional basis? | Should this item score CBK 11 as supporting source only, and fail if the primary regulation is not selected? |
| CBY-06 | Which amended provision after April 2026 controls transportation of personnel children in public personnel service vehicles? | Is the current scorer expecting a different article/span or additional fact slots for the 2026 amendment? |
| KKY-01 | Should this banking regulation be legally classified under KKY for benchmark taxonomy, or is YONETMELIK acceptable? | Should family scoring treat KKY/YONETMELIK as compatible for institution-specific regulations? |
| TEB-04 | For KDV tevkifat/iade questions, is the consolidated KDV Genel Uygulama Tebliği the required main source? | Is auto-fail caused by article-0 appendix materialization/rubric mismatch rather than wrong source selection? |
| TUZUK-04 | Is Radyasyon Güvenliği Tüzüğü a legally sufficient example for the risk of relying on old tüzük sources in 2026 occupational safety advice? | Should the item require explicit comparison with 6331/current regulations rather than accepting a tüzük-only answer? |

## Rules Applied

| Rule | Status |
|---|---|
| Do not change runtime | followed |
| Do not use private answer key | followed |
| Do not write QID-specific rules | followed |
| Review packet only | followed |

## Decision

Phase 24B packet status: ready for legal/scorer review.

No runtime implementation is allowed from this packet alone. Any later change must be systemic, separately approved, and validated against non-QID-specific gates.
