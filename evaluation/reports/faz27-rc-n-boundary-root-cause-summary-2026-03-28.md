# FAZ27 RC-N Boundary Root Cause Summary

- first_break_control = `mandatory auth`
- first_break_step = `B1`
- first_break_stage = `preprojection_hash`
- first_break_count = `146`
- dominant_control = `Redis session persistence`
- dominant_stage = `preprojection_hash`
- effective_control_set = `mandatory auth, immutable audit logging, Redis session persistence`
- single_control_root_cause_found = `false`
- interaction_root_cause_found = `true`
- root_cause_class = `multi_control_interaction_runtime_mutation`
- primary_reason = `single-control additive runs do not isolate the RC-N boundary truth; pairwise and subtractive comparisons keep the breach inside the auth/audit/session interaction surface, with session removal producing the sharpest collapse.`
- unexplained_count = `0`
