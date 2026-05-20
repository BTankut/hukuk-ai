# FAZ7 Token Accounting Acceptance

Tarih: 2026-03-24

Scope:
- strict lane approximate fallback kapalı
- upstream usage varsa korunacak
- yoksa tokenizer-backed accounting devreye girecek

Env / signature:
- `TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=false`
- `TOKEN_ACCOUNTING_TOKENIZER_PATH=<local Qwen tokenizer snapshot>`

Gözlem:
- live audit içinde hem `upstream` hem `tokenizer` kaynaklı usage görüldü
- refusal smoke kaydı tokenizer ile `prompt=2 completion=0 total=2`
- cited / continuity path upstream usage’ı koruyor
- metrics yüzeyinde `hukuk_ai_usage_source_total{source="tokenizer"}` ve `{source="upstream"}` artıyor

Fresh evidence:
- `runtime_logs/rc_h_audit_faz7_acceptance.jsonl`
- `evaluation/reports/faz7-rc-h-metrics-excerpt-2026-03-24.txt`

Sonuç:
- `PASS`
