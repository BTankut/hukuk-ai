# Mevzuat Controlled Cutover Upstream Baglanti Denetimi 2026-04-18

## Official Audit
- `upstream_endpoint = ssh btankut@192.168.12.236 -> 127.0.0.1:30000 (/v1/models)`
- `dns_resolution_pass = true`
- `tcp_connect_pass = false`
- `application_health_pass = false`
- `timeout_or_host_down_seen = true`
- `connectivity_blocker_found = true`

## Evidence
- configured baseline launcher `REMOTE_HOST = btankut@192.168.12.236`
- `192.168.12.236:22` = host down
- `192.168.12.236:30000` = host down / timeout
- direct HTTP `http://192.168.12.236:30000/v1/models` = timeout
- alternate endpoint `192.168.12.243:30000` cevap veriyor ancak live served model id `/models/merged_model_fabric_stage_20260321`
- alternate endpoint configured baseline model contract ile birebir ayni olarak teyit edilmedigi icin remediation closure icin adopt edilmedi

## Decisive Conclusion
- configured upstream endpoint serving akisi icin saglikli degil
- application-level readiness kapanmadigi icin upstream connectivity `READY` verilemez
