# Phase 24HR Non-Live Residual Smoke

- generated_at_utc: `2026-05-06T13:45:18.273742+00:00`
- status: `PASS`
- row_count: `9`
- pass_count: `9`
- fail_count: `0`
- live_8000_modified: `false`
- milvus_modified: `false`
- model_inference_called: `false`

| qid | check | status | expected | observed |
|---|---|---|---|---|
| `TEB-04` | `teb_source_identity_selects_kdv_gut` | `PASS` | 19631 | 19631 |
| `TEB-04` | `teb_required_locators_materialized` | `PASS` | I/C-2.1.3\|I/C-2.1.5.2.1\|I/C-2.1.5.2.2\|I/C-2.1.5.3 | I/C-2.1.3\|I/C-2.1.5.2.1\|I/C-2.1.5.2.2\|I/C-2.1.5.3 |
| `TEB-04` | `teb_span_recall_kismi_tevkifat` | `PASS` | I/C-2.1.3 | I/C-2.1.5.2.2\|I/C-2.1.3.1\|I/C-2.1.3.2\|I/C-2.1.3.2.5.2\|I/C-2.1.3.4 |
| `TEB-04` | `teb_span_recall_mahsuben_iade` | `PASS` | I/C-2.1.5.2.1 | I/C-2.1.5.2.1\|I/C-2.1.5.1\|I/C-2.1.5.3\|I/C-2.1.3.4.3.2\|I/C-2.1.5.2.2 |
| `TEB-04` | `teb_span_recall_nakden_iade` | `PASS` | I/C-2.1.5.2.2 | I/C-2.1.5.2.2\|I/C-2.1.5.1\|I/C-2.1.5.3\|I/C-2.1.3.4.3.2\|I/C-2.1.3.1 |
| `TEB-04` | `teb_span_recall_diger_hususlar` | `PASS` | I/C-2.1.5.3 | I/C-2.1.5.3\|I/C-2.1.3.4.3.2\|I/C-2.1.5.2.1\|I/C-2.1.5.2.2\|I/C-2.1.3.2.14 |
| `TUZUK-05` | `tuzuk_runtime_priority_selects_general_hierarchy_chunk` | `PASS` | genel-hiyerarsi tüzük | genel-hiyerarsi tüzük |
| `TUZUK-05` | `tuzuk_scorer_accepts_abstract_hierarchy_policy` | `PASS` | document_match_score=1.00 without wrong_document | document_match_score=1.00 failure_classes= |
| `TUZUK-05` | `tuzuk_scorer_rejects_irrelevant_concrete_tuzuk_title` | `PASS` | document_match_score=0.00 with wrong_document | document_match_score=0.00 failure_classes=missing_gold_document_signal \| wrong_document \| hallucinated_identifier \| unsupported_confident_claim |

## Gate Impact

- This smoke closes artifact-level non-live validation for TEB-04 span selection and TUZUK-05 hierarchy policy behavior.
- It does not create a shadow collection, serving candidate, internal eval opening, or productization decision.
- Productization remains blocked by full benchmark stability, other residual rows, live guardrails/verification/privacy/audit controls, and rollback rehearsal.
