# FAZ7 Auth Acceptance

Tarih: 2026-03-24

Scope:
- hedef lane: `rc_h`
- protected surfaces: `/v1/chat/completions`, `/v1/models`, `/v1/sessions/*`, `/v1/alerts`, `/v1/metrics`

Komut / kanıt:
- `python3 scripts/faz7/run_release_smoke_suite.py --base-url http://127.0.0.1:8005 --api-key faz7-internal-key --output-path runtime_logs/faz7_release_smoke_rc_h.json`
- `curl -D runtime_logs/faz7_rc_h_models_headers.txt -H 'X-API-Key: faz7-internal-key' http://127.0.0.1:8005/v1/models -o runtime_logs/faz7_rc_h_models_body.json`

Gözlem:
- anonymous chat çağrısı `401`
- authorized smoke çağrısı `200`
- `/v1/models` auth ile `200`

Fresh evidence:
- `evaluation/reports/faz7-release-smoke-acceptance-2026-03-24.json`
- `runtime_logs/faz7_rc_h_models_headers.txt`
- `runtime_logs/faz7_rc_h_models_body.json`

Sonuç:
- `PASS`
