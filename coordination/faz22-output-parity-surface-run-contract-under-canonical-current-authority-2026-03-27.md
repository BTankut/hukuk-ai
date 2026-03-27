# FAZ22 Output Parity Surface Run Contract Under Canonical Current Authority

## Fixed Runtime Rules

- first-run is authoritative
- error-rerun is allowed only for rows with real `runtime_error`
- error-rerun never overwrites first-run rows
- if `runtime_error_count = 0`, rerun is forbidden
- gate calculations are taken from effective view only

## Forbidden Actions

- clean rerun
- second run without runtime error
- patching rc-g, rc-j or rc-m
- changing answer path or evaluator path
