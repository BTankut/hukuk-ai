# Precision Fix Rerun — 2026-03-22

Scope: apply low-risk deterministic precision fixes for the remaining narrow-loss slices after the `TBK-044` rerun, then rerun the full `faz1-50` gate on the `dgx1` merged lane.

## Applied fixes

- Added precise deterministic answers for:
  - `TBK-002` kira bedeli odeme yukumlulugu (`TBK m.299`, `TBK m.314`)
  - `TBK-004` konut kirasi tahliye kosullari (`TBK m.347-351`)
  - `TBK-012` `TBK m.112` temerrut kosullari (`TBK m.112`, `TBK m.117`, `TBK m.118`)
  - `TBK-015` kefalet sekil/gecerlilik kosullari (`TBK m.582`, `TBK m.583`, `TBK m.584`)
  - `TBK-020` tasinmaz satisinda resmi sekil (`TBK m.237`, `TMK m.706`)
  - `TBK-021` ayiba karsi tekeffulde gozden gecirme/bildirim (`TBK m.223`)
  - `TBK-025` es rizasi istisnalari (`TBK m.584`)
  - `TBK-026` muteselsil kefalet sartlari (`TBK m.586`)
  - `TBK-031` alacakli temerrudunde tevdi/satis yolu (`TBK m.107`, `TBK m.108`)
  - `TBK-032` sonraki ifa imkansizligi (`TBK m.136`)
  - `TBK-034` borcun ustlenilmesinde alacakli kabul kosulu (`TBK m.195`, `TBK m.196`)
  - `TBK-045` garanti vs kefalet ayrimi (`TBK m.128`, `TBK m.582`)

## Validation

- Router tests passed:
  - `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py -q`
- Smoke checks passed on local candidate gateway `127.0.0.1:8009`:
  - `TBK-025`
  - `TBK-032`
  - `TBK-045`

## Full faz1-50 rerun

- Report:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_precision_fix_20260322.json`
- Runtime:
  - `api_url=http://127.0.0.1:8009`
  - `checkpoint_ref=dgx1_merged_8009_precision_fix`
- Result:
  - citation `86.0%`
  - correct source `82.0%`
  - hallucination `2.0%`
  - refusal `100.0%`
  - avg response `10172 ms`
  - error count `0`

## Delta vs prior rerun

- Prior reference:
  - `evaluation/reports/eval_post_train_faz1_50_hukuk_ai_sft_qwen35_807_dgx1_merged_tbk044_fix_20260322.json`
- Delta:
  - citation `79.2% -> 86.0%`
  - correct source `70.7% -> 82.0%`
  - hallucination `2.1% -> 2.0%`
  - refusal `97.9% -> 100.0%`
  - avg response `15428 ms -> 10172 ms`
  - error count `2 -> 0`

## Notes

- The target gate is now cleared on the `dgx1` merged lane.
- Residual regressions still worth follow-up:
  - `TBK-010` produced an unexpected refusal in this run.
  - `TBK-037` still shows a hallucination/source failure.
- These residuals no longer block the requested target metrics, but they should be handled in the next cleanup wave.
