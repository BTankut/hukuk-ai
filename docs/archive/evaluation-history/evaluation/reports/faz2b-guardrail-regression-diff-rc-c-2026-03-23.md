# FAZ 2B Guardrail Regression Diff

- generated_at: `2026-03-23T16:40:53.405772+00:00`
- total_regressions: `80`
- false_refusal_after_guardrail: `30`

## By Family

- `faz1-50`: `14`
- `v2-95`: `21`
- `v3-170`: `45`

## By Class

- `excerpt_match_false_negative`: `2`
- `false_refusal_after_guardrail`: `30`
- `scope_parser_false_positive`: `1`
- `true_guardrail_block`: `47`

## Sample Rows

| family | question_id | rc_a_mode | rc_b_mode | gate | regression_class |
| --- | --- | --- | --- | --- | --- |
| faz1-50 | TBK-002 | answer | answer | answer | true_guardrail_block |
| faz1-50 | TBK-003 | answer | refusal | law_scope_mismatch | scope_parser_false_positive |
| faz1-50 | TBK-011 | answer | refusal | insufficient_supported_evidence | false_refusal_after_guardrail |
| faz1-50 | TBK-012 | answer | answer | answer | true_guardrail_block |
| faz1-50 | TBK-018 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-019 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-020 | answer | answer | answer | true_guardrail_block |
| faz1-50 | TBK-035 | answer | partial | partial | false_refusal_after_guardrail |
| faz1-50 | TBK-039 | answer | refusal | insufficient_supported_evidence | false_refusal_after_guardrail |
| faz1-50 | TBK-040 | answer | partial | partial | false_refusal_after_guardrail |
| faz1-50 | TBK-047 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-048 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-049 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| faz1-50 | TBK-050 | refusal | refusal | insufficient_supported_evidence | true_guardrail_block |
| v2-95 | TBK-058 | answer | partial | partial | false_refusal_after_guardrail |
| v2-95 | TBK-063 | answer | partial | partial | false_refusal_after_guardrail |
| v2-95 | TBK-070 | answer | partial | partial | false_refusal_after_guardrail |
| v2-95 | TBK-079 | answer | partial | partial | false_refusal_after_guardrail |
| v2-95 | TBK-082 | answer | refusal | claim_support_missing | excerpt_match_false_negative |
| v2-95 | TBK-094 | answer | answer | answer | true_guardrail_block |
| v2-95 | TBK-096 | answer | answer | answer | true_guardrail_block |
| v2-95 | TBK-097 | answer | answer | answer | true_guardrail_block |
| v2-95 | TBK-098 | answer | partial | partial | false_refusal_after_guardrail |
| v2-95 | TBK-099 | answer | partial | partial | false_refusal_after_guardrail |
| v2-95 | TBK-100 | answer | partial | partial | false_refusal_after_guardrail |
