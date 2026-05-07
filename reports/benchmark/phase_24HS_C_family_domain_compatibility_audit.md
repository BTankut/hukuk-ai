# Phase 24HS-C - Family / Domain Compatibility Audit

## Scope

- Target failures: `KANUN-08`, `YON-05`.
- Baseline run: `reports/benchmark/runs/phase_24HR_option_C_targeted_candidate_smoke`.
- Candidate run: `reports/benchmark/runs/phase_24HS_focused_non_live_candidate_smoke_final_v6`.
- Non-live endpoint: `http://127.0.0.1:8041/v1`.
- Live `8000`: not modified.

## Baseline vs Candidate

| QID | Baseline source | Baseline score | Candidate source | Candidate score | Result |
| --- | --- | ---: | --- | ---: | --- |
| `KANUN-08` | `YONETMELIK`, Elektronik Haberleşme tüketici hakları yönetmeliği | `1.45 FAIL` | `KANUN`, Türk Borçlar Kanunu `TBK m.255` | `3.25 FAIL` | family improved, domain/document still wrong |
| `YON-05` | `KANUN`, İmar Kanunu `3194 m.18` | `5.75 FAIL` | `YONETMELIK`, Planlı Alanlar İmar Yönetmeliği `23722 m.5` | `7.55 PASS` | source identity improved |

## Implementation Summary

Implemented in `api-gateway/src/source_family_resolver.py` and `api-gateway/src/rag/source_identity.py`:

- Added a supporting-law/regulation distinction for queries that explicitly ask a yönetmelik/procedural source while also mentioning statutory basis or why a law alone is insufficient.
- Preserved the rule that supporting sources may appear in evidence, but cannot overwrite the primary selected source unless the query explicitly asks for statutory basis.
- Exposed `ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE` as an alias for the family-domain compatibility gate so this phase can be enabled independently in the non-live candidate.

## Audit Findings

`YON-05` is the successful family/domain case. The baseline let `KANUN` overwrite a yönetmelik/procedural primary. The candidate locks to `PLANLI ALANLAR İMAR YÖNETMELİĞİ` and keeps the source family as `YONETMELIK`.

`KANUN-08` remains residual. The candidate no longer selects a regulation family, but it chooses the wrong same-family law (`TÜRK BORÇLAR KANUNU`). That means the remaining issue is no longer a pure family compatibility failure. It is a same-family source/domain identity problem: the family gate cannot safely filter a wrong `KANUN` when the expected source is also a `KANUN`.

## Decision

Phase 24HS-C is partially accepted:

- Accepted for the cross-family overwrite pattern demonstrated by `YON-05`.
- Residual blocker remains for `KANUN-08`: same-family legal-domain source identity needs a later systemic recovery phase.

CSV audit: `reports/benchmark/phase_24HS_C_family_domain_compatibility_audit.csv`.
