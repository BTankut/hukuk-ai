# RC-S Narrow Controlled Primary-Source Expansion Contract 2026-04-01

## Allowed Source Classes

- `TMK core corpus`
- `TCK`
- `HMK`
- `CMK`
- `TTK`
- `İK`

## Excluded Source Classes

- `Yargıtay İçtihat Merkezi (YİM)`
- `customer/private documents`
- `external internet-derived ad hoc content`

## Hard Governance Rules

- no customer/private data = `true`
- no YIM = `true`
- no external ad hoc internet data = `true`
- no actual ingest in this phase = `true`
- no embedding generation in this phase = `true`
- no index build in this phase = `true`
- no vector DB write in this phase = `true`
- no model change in this phase = `true`
- no prompt change in this phase = `true`
- no retrieval contract change in this phase = `true`
- no guardrail change in this phase = `true`
- no release-controls topology change in this phase = `true`

## Transition Rule

- readiness_closed = `true`
- actual_expansion_started = `false`
- next_official_work_if_closed = `rc-s narrow controlled primary-source expansion gate under canonical current authority`
