# Mevzuat Pre-Switch vs Post-Switch Divergence Denetimi 2026-04-18

| smoke_case_id | pre_switch_result | post_switch_result | result_delta | first_divergence_stage | root_cause_hypothesis |
| --- | --- | --- | --- | --- | --- |
| KANUN-A | PASS | FAIL | FAIL -> PASS | upstream_chat_request_after_switch | post_switch_upstream_readiness_transient |
| YONETMELIK-A | PASS | FAIL | FAIL -> PASS | runtime_collection_binding_after_switch | stale_legacy_candidate_collection_binding |
| CBK-A | PASS | FAIL | FAIL -> PASS | runtime_collection_binding_after_switch | stale_legacy_candidate_collection_binding |
| CB-YONETMELIK-A | PASS | FAIL | FAIL -> PASS | runtime_collection_binding_after_switch | stale_legacy_candidate_collection_binding |
| MULGA-A | PASS | FAIL | FAIL -> PASS | runtime_collection_binding_after_switch | stale_legacy_candidate_collection_binding |
| TEBLIG-A | PASS | FAIL | FAIL -> PASS | runtime_collection_binding_after_switch | stale_legacy_candidate_collection_binding |
| LIVE-KANUN-A | PASS | FAIL | FAIL -> PASS | runtime_collection_binding_after_switch | stale_legacy_candidate_collection_binding |
