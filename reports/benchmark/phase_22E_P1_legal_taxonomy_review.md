# Phase 22E-D P1 Legal Taxonomy Review

Input artifacts:

- Phase 22D P1 audit: `reports/benchmark/phase_22D_P1_remediation_audit.csv`
- Phase 22D full run: `reports/benchmark/runs/20260501T062248Z_phase22D_full_clean`

Runtime behavior was not changed. No family relabeling was applied.

## Decision Summary

| QID | Issue | Safe Action |
| --- | --- | --- |
| CBY-04 | CB_YONETMELIK vs CB_KARARNAME taxonomy boundary. | Manual legal review required. |
| KANUN-12 | KANUN expected, technical regulation selected. | Defer until expected primary law is legally identified. |
| KKY-01 | Relevant regulation selected, but family is generic YONETMELIK while benchmark expects KKY. | Manual taxonomy review required; do not relabel at runtime. |
| KKY-03 | Wrong technical regulation selected through KKY/YONETMELIK bridge. | Defer until expected document is identified. |
| TUZUK-05 | TUZUK family correct, but selected article-zero/wrong source area. | Corpus/materialization or manual review required. |
| YON-04 | Correct broad family, wrong domain regulation selected. | Manual review before any source identity patch. |

## Findings

`CBY-04` is not a runtime relabeling problem. The selected source is expressly a Cumhurbaşkanlığı Kararnamesi. Relabeling it as CB_YONETMELIK would corrupt legal source taxonomy.

`KANUN-12` and `KKY-03` are wrong-document cases. They should not be patched by broad source-family preference changes because that would increase cross-family/source drift.

`KKY-01` is close to a taxonomy/scoring boundary: the selected banking regulation is relevant and body-bearing, but the source family is represented as generic YONETMELIK. This needs a legal taxonomy rule for when institution-specific regulations are KKY, not a runtime answer-contract relabel.

`TUZUK-05` needs corpus/span review. The selected family is correct, but article-zero selection and wrong source area prevent confident answer synthesis.

`YON-04` needs document identity review. Prior audit identifies the target area as personal data deletion/anonymization; the runtime selects a nuclear safety regulation. A broad title/domain boost is unsafe without manual review and regression guards.

## Phase 22E-D Decision

- No runtime family relabel is safe.
- No broad document identity patch is safe.
- P1 rows remain productization risk register items, not Phase 22E runtime patch targets.

CSV: `reports/benchmark/phase_22E_P1_legal_taxonomy_review.csv`

