# FAZ42 RC-R Process-Isolated Perimeter Placement Matrix

- mandatory_auth_placement = `external_transport_gateway_process_only`
- immutable_audit_logging_placement = `detached_async_outbox_process_only`
- redis_session_persistence_placement = `external_session_sidecar_process_only`
- persisted_pii_redaction_placement = `persistence_and_audit_views_only`
- tokenizer_backed_accounting_placement = `detached_post_response_accounting_process_only`
- observability_alerting_placement = `passive_tap_or_metrics_export_only`
- api_versioning_placement = `transport_boundary_only`
- process_supervision_placement = `host_or_process_boundary_only`
- backup_restore_placement = `offline_operational_boundary_only`
- one_command_release_smoke_placement = `external_blackbox_harness_only`
- same_process_release_controls_allowed = `false`
- shared_memory_or_live_object_between_release_controls_and_serving_process_allowed = `false`
- frozen_snapshot_id_only_cross_boundary = `true`
- serving_process_role = `rc_g_pure_answer_lane_only`
- release_controls_process_role = `detached_perimeter_only`
