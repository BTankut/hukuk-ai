# Phase 24HU-F Full Candidate Not Run

The optional full 100-question candidate benchmark was not run in Phase 24HU.

Reason:

- Phase 24HU was scoped to source-role retrieval recovery for the KANUN-08 residual.
- The focused non-live smoke recovered KANUN-08 and showed zero score regressions across guard rows.
- Live `8000` must remain untouched.
- Full-run traces are large and should be opened under a separate controlled validation brief rather than bundled into this targeted recovery phase.

Current evidence supports a next controlled full-candidate validation, not live cutover.

Required next full-run gates remain:

```text
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
green_lane = PASS
raw_score_proxy >= current trace-on base
pass_proxy >= current trace-on base
wrong_document <= current trace-on base
hallucinated_identifier <= current trace-on base
```

