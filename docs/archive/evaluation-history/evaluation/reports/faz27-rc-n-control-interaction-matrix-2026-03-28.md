# FAZ27 RC-N Control Interaction Matrix

- effective_control_set = `mandatory auth, immutable audit logging, Redis session persistence`
- pairwise_interaction_only_for_effective_controls = `true`
- root_cause_class = `multi_control_interaction_runtime_mutation`
- primary_reason = `single-control additive runs do not isolate the RC-N boundary truth; pairwise and subtractive comparisons keep the breach inside the auth/audit/session interaction surface, with session removal producing the sharpest collapse.`
- unexplained_count = `0`

| control_pair | preprojection | raw_answer | response_envelope | runtime_error |
| --- | --- | --- | --- | --- |
| mandatory auth + immutable audit logging | 148 | 148 | 87 | 0 |
| mandatory auth + Redis session persistence | 158 | 158 | 102 | 0 |
| immutable audit logging + Redis session persistence | 157 | 157 | 93 | 0 |
