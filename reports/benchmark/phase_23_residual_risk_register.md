# Phase 23 Residual Risk Register

Generated: 2026-05-02T20:21:54Z

Scope: controlled cutover readiness only. This register records residual Phase 22F-S7 fail rows and does not change runtime behavior.

## Acceptance Summary

- Fail rows classified: 9/9.
- Preferred gate miss recorded: `wrong_family = 6`, while preferred target was `wrong_family <= 5`.
- Minimum shadow gate was passed: `pass_proxy = 91/100`, `unsupported_confident_answer = 0`, `contract_valid = 100/100`, `source_key_v2_collision = 0`, `binding_collision = 0`.
- Acceptance is limited to benchmark/internal evaluation cutover readiness. It is not public serving or productization acceptance.

## Register

| QID | Family | Score | Failure Classes | Risk Type | Severity | Accepted For Cutover | Reason |
|---|---|---:|---|---|---|---|---|
| CBY-04 | CB_YONETMELIK | 6.85 | missing_required_content_signal; wrong_family; hallucinated_identifier; partial_grounding_only | legal_taxonomy_residual | medium | true | Exact document/article evidence was selected, but source family surfaced as CB_KARARNAME instead of CB_YONETMELIK. |
| CBY-06 | CB_YONETMELIK | 6.80 | missing_required_content_signal; partial_grounding_only | answer_completeness_residual | medium | true | Family is correct and partial document evidence exists; fail is mainly missing required content coverage. |
| KANUN-12 | KANUN | 1.45 | missing_gold_document_signal; missing_required_content_signal; wrong_family; wrong_document; partial_grounding_only | document_identity_residual | high | true | Selected KKY/YON evidence instead of expected KANUN source. |
| KKY-01 | KKY | 6.65 | missing_required_content_signal; wrong_family; hallucinated_identifier; partial_grounding_only | legal_taxonomy_residual | medium | true | Selected underlying YONETMELIK family for KKY expected family with partial correct document signal. |
| KKY-03 | KKY | 1.45 | missing_gold_document_signal; missing_required_content_signal; wrong_family; wrong_document; partial_grounding_only | document_identity_residual | high | true | Selected unrelated YONETMELIK evidence for expected KKY question. |
| TEB-04 | TEBLIGLER | 0.00 | auto_fail_triggered; missing_required_content_signal; partial_grounding_only | scorer_rubric_residual | medium | true | Family and document are correct, but auto-fail remains on required temporal/content signal coverage. |
| TUZUK-04 | TUZUK | 6.43 | missing_required_content_signal; partial_grounding_only | answer_completeness_residual | medium | true | Family is correct and document evidence is partial. |
| TUZUK-05 | TUZUK | 3.25 | missing_gold_document_signal; missing_required_content_signal; wrong_document; partial_grounding_only | document_identity_residual | high | true | Family is correct but selected document/span does not match expected gold document. |
| YON-04 | YONETMELIK | 3.25 | missing_gold_document_signal; missing_required_content_signal; wrong_document; partial_grounding_only | document_identity_residual | high | true | Family is correct but selected document is wrong. |

## Cutover Interpretation

These residuals are accepted only for a controlled benchmark/internal evaluation lane because the candidate passes the minimum shadow gate and does not emit unsupported confident answers. They remain blockers for productization/public serving until reviewed through residual remediation, legal review, or scorer audit.

No Phase 23 runtime behavior change was made while creating this register.
