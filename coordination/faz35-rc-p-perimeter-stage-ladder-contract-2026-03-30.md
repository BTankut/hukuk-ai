# FAZ35 RC-P Perimeter Stage Ladder Contract

- P0 = `transport_gateway_boundary`
- P1 = `auth_identity_token_boundary`
- P2 = `frozen_snapshot_async_outbox_boundary`
- P3 = `sidecar_session_state_boundary`
- P4 = `persistence_and_audit_view_boundary`
- P5 = `post_response_accounting_snapshot_boundary`
- P6 = `passive_observability_tap_boundary`
- P7 = `api_version_transport_boundary`
- P8 = `host_process_supervision_boundary`
- P9 = `offline_backup_restore_boundary`
- P10 = `non_serving_release_smoke_boundary`
- P11 = `preprojection_hash`
- P12 = `raw_answer_hash`
- P13 = `response_envelope_hash`
- dominant_stage_must_be = `P11`
