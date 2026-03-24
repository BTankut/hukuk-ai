# FAZ7 API Versioning Acceptance

Tarih: 2026-03-24

Scope:
- response header versioning
- lane exposure
- models payload contract

Komut / kanıt:
- `curl -D runtime_logs/faz7_rc_h_models_headers.txt -H 'X-API-Key: faz7-internal-key' http://127.0.0.1:8005/v1/models -o runtime_logs/faz7_rc_h_models_body.json`
- `evaluation/reports/faz7-release-smoke-acceptance-2026-03-24.json`

Gözlem:
- header `X-Hukuk-AI-API-Version = 2026-03-24-rc-h`
- header `X-Hukuk-AI-Lane = rc_h`
- header `X-Request-ID` mevcut
- `/v1/models` body içinde `api_version` ve `lane` sabit
- `/v1/health` body içinde `lane` ve `api_version` sabit

Fresh evidence:
- `runtime_logs/faz7_rc_h_models_headers.txt`
- `runtime_logs/faz7_rc_h_models_body.json`
- `evaluation/reports/faz7-release-smoke-acceptance-2026-03-24.json`

Sonuç:
- `PASS`
