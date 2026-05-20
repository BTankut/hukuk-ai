# FAZ7 Latency Budget

Tarih: 2026-03-24

Referans smoke:
- `runtime_logs/faz7_release_smoke_rc_g_wp4.json`

Candidate smoke:
- `runtime_logs/faz7_release_smoke_rc_h_wp4.json`

Recovery proof:
- `runtime_logs/faz7_rc_h_supervision.json`

Özet:
- `RC-G` smoke latencies: `9069.32ms`, `3017.87ms`, `224.90ms`
- `RC-H` smoke latencies: `8993.19ms`, `3056.54ms`, `12.57ms`
- reference `p95 = 8464.178ms`
- candidate `p95 = 8399.524ms`
- regression percent = `-0.764%`
- auto recovery = `true`

Karar:
- `latency budget pass = true`
- `operational regression gate = PASS`

Detay artefact:
- `evaluation/reports/faz7-operational-regression-gate-2026-03-24.md`
- `evaluation/reports/faz7-operational-regression-gate-2026-03-24.json`
