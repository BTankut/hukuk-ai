# FAZ23 RC-M Summary Truth Reconciliation Schema v1

- reference_pack_integrity_pass: bool
- reference_pack_contradiction_count: int
- historical_summary_mismatch_count: int
- current_summary_mismatch_count: int
- historical_surface_breach_count: int
- current_surface_breach_count: int
- historical_frontier_candidate_count: int
- current_frontier_candidate_count: int
- reconciliation_stage: R0|R1|R2|R3|R4
- primary_reason: string
- root_cause_class: fixed enum
- current_summary_truth_adopted: bool
- historical_summary_archive_reclassified: bool
- surface_breach_from_history_reintroduced: bool
- historical_summary_channel: string
- unexplained_count: int
