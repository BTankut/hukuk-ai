# FAZ 3 Guardrail Blocker Rerun

- total_questions: `77`
- false_refusal_after_guardrail: `4`
- true_guardrail_block: `12`
- answer_count: `20`
- partial_count: `36`
- refusal_count: `21`
- whitelist_violation_leak_count: `0`
- temporal_answer_leak_count: `0`
- law_scope_answer_leak_count: `0`
- claim_binding_answer_leak_count: `0`
- overall_pass: `true`

## Sample Rows

| family | question_id | before | rc_d_mode | rc_d_reason | residual |
| --- | --- | --- | --- | --- | --- |
| faz1-50 | TBK-002 | true_guardrail_block | answer | None | None |
| faz1-50 | TBK-011 | false_refusal_after_guardrail | refusal | insufficient_supported_evidence | false_refusal_after_guardrail |
| faz1-50 | TBK-012 | true_guardrail_block | partial | None | None |
| faz1-50 | TBK-018 | true_guardrail_block | refusal | insufficient_supported_evidence | None |
| faz1-50 | TBK-019 | true_guardrail_block | refusal | insufficient_supported_evidence | None |
| faz1-50 | TBK-020 | true_guardrail_block | answer | None | true_guardrail_block |
| faz1-50 | TBK-035 | false_refusal_after_guardrail | answer | None | true_guardrail_block |
| faz1-50 | TBK-039 | false_refusal_after_guardrail | refusal | insufficient_supported_evidence | false_refusal_after_guardrail |
| faz1-50 | TBK-040 | false_refusal_after_guardrail | answer | None | None |
| faz1-50 | TBK-047 | true_guardrail_block | refusal | insufficient_supported_evidence | None |
| faz1-50 | TBK-048 | true_guardrail_block | refusal | insufficient_supported_evidence | None |
| faz1-50 | TBK-049 | true_guardrail_block | refusal | insufficient_supported_evidence | None |
| faz1-50 | TBK-050 | true_guardrail_block | refusal | insufficient_supported_evidence | None |
| v2-95 | TBK-058 | false_refusal_after_guardrail | answer | None | None |
| v2-95 | TBK-063 | false_refusal_after_guardrail | answer | None | true_guardrail_block |
| v2-95 | TBK-070 | false_refusal_after_guardrail | partial | None | None |
| v2-95 | TBK-079 | false_refusal_after_guardrail | answer | None | true_guardrail_block |
| v2-95 | TBK-094 | true_guardrail_block | partial | None | None |
| v2-95 | TBK-096 | true_guardrail_block | partial | None | None |
| v2-95 | TBK-097 | true_guardrail_block | partial | None | None |
| v2-95 | TBK-098 | false_refusal_after_guardrail | answer | None | None |
| v2-95 | TBK-099 | false_refusal_after_guardrail | partial | None | None |
| v2-95 | TBK-100 | false_refusal_after_guardrail | answer | None | None |
| v2-95 | TBK-101 | true_guardrail_block | partial | None | None |
| v2-95 | TBK-102 | true_guardrail_block | partial | None | None |
