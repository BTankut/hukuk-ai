# Mevzuat Controlled Cutover Upstream Baglanti Denetimi 2026-04-18

## Official Audit
- `upstream_endpoint = ssh btankut@192.168.12.236 -> 127.0.0.1:30000 -> local tunnel (/v1/models, /v1/chat/completions)`
- `dns_resolution_pass = true`
- `tcp_connect_pass = true`
- `application_health_pass = true`
- `timeout_or_host_down_seen = false`
- `connectivity_blocker_found = false`

## Evidence
- configured baseline launcher `REMOTE_HOST = btankut@192.168.12.236`
- DGX node tekrar ayaga kalkti ve `vllm-base` container `Qwen/Qwen3.5-35B-A3B-FP8` ile calisiyor
- remote-local health `http://127.0.0.1:30000/v1/models` = `200`
- configured SSH tunnel path uzerinden `GET /v1/models` = `200`
- configured SSH tunnel path uzerinden `POST /v1/chat/completions` = `200`
- served model kimligi configured baseline contract ile birebir uyumlu: `Qwen/Qwen3.5-35B-A3B-FP8`

## Decisive Conclusion
- configured upstream endpoint serving akisi icin yeniden saglikli
- upstream LLM connectivity blocker'i bu remediation turunda kapanmis kabul edilir
