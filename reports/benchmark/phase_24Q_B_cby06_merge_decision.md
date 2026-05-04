# Phase 24Q-B CBY-06 Merge / No-Merge Decision

## Decision

```text
selected_option = Option B - Keep CBY span but require selector scoping and matched rerun
live_cutover = no
collection_merge = no
diagnostic_value = keep
```

CBY-06 targeted smoke passed and the CBY-06 full-run row improved from 6.80 to 8.58. The new CBY span is therefore locally useful.

The Phase24P-R full shadow still failed the gate:

```text
Phase23R-E raw_score_proxy = 816.86
Phase24P-R raw_score_proxy = 806.87
Phase23R-E pass_proxy = 91
Phase24P-R pass_proxy = 90
```

The Phase24Q-A audit did not find direct CBY span interference in unrelated pass-to-fail rows. The five pass-to-fail rows had no new CBY evidence. `CBY-05` saw the new CBY span but stayed `PASS` with unchanged score, so it is benign same-family neighbor visibility.

## Why Not Merge

The comparison is not a clean same-runtime A/B test:

```text
Phase23R-E api_url = http://127.0.0.1:8000/v1
Phase23R-E git_sha = b34ed1c8c72cd9c1108282eda50d53dd4d35c032
Phase24P-R api_url = http://127.0.0.1:8034/v1
Phase24P-R git_sha = 100c6238fb6ea1dd609e36da88ce4d549cdb4436
```

Gateway and selector-related code changed between those SHAs. Because the full-run drop is confounded by runtime provenance mismatch and existing residual shift, merging the CBY-only collection would be premature.

## Required Before Reconsidering Merge

```text
1. Run matched same-runtime base-vs-CBY full benchmark.
2. Keep model, prompt, top-k, scoring, and gateway code identical between both lanes.
3. Verify no pass-to-fail row contains the new CBY span or CBY-biased source selection.
4. Verify full gate meets or exceeds Phase23R-E minimums.
5. Keep live 8000 unchanged until the matched gate passes.
```

## Safe Action

Keep the CBY-06 span and collection as a diagnostic/shadow artifact only. Do not cut over `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06` to live.
