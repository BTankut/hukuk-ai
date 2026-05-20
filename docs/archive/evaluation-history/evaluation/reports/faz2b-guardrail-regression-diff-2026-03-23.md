# FAZ 2B Guardrail Regression Diff

- generated_at: `2026-03-23T14:39:54.177225+00:00`
- total_regressions: `109`
- false_refusal_after_guardrail: `6`

## By Family

- `faz1-50`: `17`
- `v2-95`: `33`
- `v3-170`: `59`

## By Class

- `claim_binding_block`: `1`
- `excerpt_match_false_negative`: `68`
- `false_refusal_after_guardrail`: `6`
- `scope_parser_false_positive`: `11`
- `true_guardrail_block`: `23`

## Sample Rows

| family | question_id | rc_a_mode | rc_b_mode | gate | regression_class |
| --- | --- | --- | --- | --- | --- |
| faz1-50 | TBK-003 | answer | blocked | law_scope_mismatch | scope_parser_false_positive |
| faz1-50 | TBK-007 | answer | blocked | law_scope_mismatch | scope_parser_false_positive |
| faz1-50 | TBK-009 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| faz1-50 | TBK-011 | answer | refusal | insufficient_supported_evidence | false_refusal_after_guardrail |
| faz1-50 | TBK-018 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-019 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-020 | answer | blocked | law_scope_mismatch | scope_parser_false_positive |
| faz1-50 | TBK-029 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| faz1-50 | TBK-033 | answer | answer | answer | true_guardrail_block |
| faz1-50 | TBK-035 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| faz1-50 | TBK-039 | answer | refusal | insufficient_supported_evidence | false_refusal_after_guardrail |
| faz1-50 | TBK-040 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| faz1-50 | TBK-045 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| faz1-50 | TBK-047 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-048 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-049 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-050 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| v2-95 | TBK-051 | answer | blocked | claim_support_missing | claim_binding_block |
| v2-95 | TBK-054 | answer | blocked | law_scope_mismatch | scope_parser_false_positive |
| v2-95 | TBK-057 | answer | blocked | law_scope_mismatch | scope_parser_false_positive |
| v2-95 | TBK-058 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| v2-95 | TBK-061 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| v2-95 | TBK-062 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| v2-95 | TBK-063 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
| v2-95 | TBK-064 | answer | blocked | claim_support_missing | excerpt_match_false_negative |
