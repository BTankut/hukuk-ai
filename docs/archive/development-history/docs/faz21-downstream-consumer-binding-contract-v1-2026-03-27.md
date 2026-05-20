# FAZ21 Downstream Consumer Binding Contract v1

## Binding Order

1. `canonical_current_authority_ref`
2. `historical_archive_ref`

## Binding Rules

- current decisions are taken from `canonical_current_authority_ref`
- historical rows are visible only in `diagnostic_only` channel
- `surface_breach_from_history_reintroduced = false` must hold for every consumer
- authoritative comparison order is fixed:
  `current_canonical -> historical_archive`
