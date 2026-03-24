# FAZ7 Release Smoke Acceptance

Tarih: 2026-03-24

Scope:
- one-command smoke suite
- auth, cited answer, refusal, session continuity, audit advance, alerts

Komut:
- `python3 scripts/faz7/run_release_smoke_suite.py --base-url http://127.0.0.1:8005 --api-key faz7-internal-key --output-path runtime_logs/faz7_release_smoke_rc_h.json`

Gözlem:
- `auth_enforced = true`
- `cited_smoke_pass = true`
- `refusal_smoke_pass = true`
- `session_continuity_pass = true`
- `audit_advancing = true`
- `alerts_surface_present = true`

Fresh evidence:
- `evaluation/reports/faz7-release-smoke-acceptance-2026-03-24.json`

Sonuç:
- `PASS`
