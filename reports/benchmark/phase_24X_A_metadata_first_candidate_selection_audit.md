# Phase 24X-A Metadata-First Candidate Selection Audit

## Scope
- Rows: `KANUN-08`, `YON-05`.
- Inputs: existing Phase23R-E and Phase24U trace-on BASE traces. No new scoring, no benchmark answer key use, no live `8000` change.

## Required Answers
- `KANUN-08`: expected Phase23R-E source (`TBK m.255` / `6098`) is not present in current metadata lookup candidates, dense/pre-rerank list, or rerank list. Wrong source wins through `normalized_title_lookup` on generic consumer-regulation title terms.
- `YON-05`: expected Phase23R-E source (`Planlı Alanlar İmar Yönetmeliği` / `23722`) is present in current metadata lookup candidates, but it is not selected into the dense/pre-rerank list or final rerank list. Wrong source wins because `3194` is treated as an exact primary identifier despite the query saying only 3194 is insufficient and asking for the regulation.
- Family/domain compatibility gate would likely block or demote both wrong primary promotions: `KANUN-08` as domain-incompatible title-only promotion, `YON-05` as support-law identifier overriding a regulation-seeking query.

## CSV
- `reports/benchmark/phase_24X_A_metadata_first_candidate_selection_audit.csv`

## Audit Table
| qid | metadata_expected_present | dense_expected_present | rerank_expected_present | selected_source_reason | safe_recovery_candidate |
|---|---|---|---|---|---|
| KANUN-08 | no | no | no | metadata_lookup=normalized_title_lookup conf=0.99 family_gate=locked_preferred_family rerank_reason=metadata_first_match, family_match, family_mapping_bridge_match, title_overlap:1, metadata_lane_supported | Gate metadata-first title candidates by domain specificity; title-only generic consumer terms cannot become primary unless source title domain terms are also query-supported. If gate filters all metadata candidates, fall back to non-metadata source-family/dense selection. |
| YON-05 | yes | no | no | metadata_lookup=exact_identifier_lookup conf=0.95 family_gate=locked_preferred_family rerank_reason=metadata_first_match, family_match, title_overlap:1, dual_lane_confirmation | Detect relation/support context around explicit identifiers (yalnız/sadece X eksik, hangi yönetmelik de devreye) and demote exact identifier law candidates to supporting-source role when regulation family evidence is explicit. |

## Next
- Phase24X-B should inspect the source identity rerank scores for the wrong candidates, then Phase24X-C should design a systemic family/domain compatibility gate.
