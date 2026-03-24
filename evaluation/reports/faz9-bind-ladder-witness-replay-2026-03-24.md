# FAZ9 Bind Ladder Replay

- question_id = `TBK-005`
- first_divergence_level = `L2`
- first_divergence_stage = `auth_enriched_request`
- primary_reason = `auth_visibility_leak`

| ladder_level | parity_match | first_divergence_stage | primary_reason | unexplained_count |
| --- | --- | --- | --- | --- |
| L0 | true | none | none | 0 |
| L1 | true | none | none | 0 |
| L2 | false | auth_enriched_request | auth_visibility_leak | 0 |
