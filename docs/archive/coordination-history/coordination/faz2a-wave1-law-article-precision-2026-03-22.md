# FAZ 2A Wave 1 — Law/Article Precision

**Date:** 2026-03-22  
**Decision:** start FAZ 2A with low-risk query parsing and retrieval precision hardening before touching verifier/source-locking logic

## Why This Wave First

Frozen FAZ 2A evidence showed:

- `tmk_cross_law` is the largest concentrated failure slice
- many TBK critical failures still carry explicit law/article intent in the question
- current live router already contains low-risk retrieval hooks:
  - explicit article force-include
  - retrieval query expansion
  - top-k boost

This makes a router-level precision wave lower risk than a deeper source-locking rewrite.

## Implemented

### 1. Stronger law/article parsing

- explicit article parsing now expands:
  - ranges such as `TBK m.397-398`
  - multi-article lists such as `TBK m.181, m.182 ve m.183`
- explicit law mention parsing now supports:
  - short codes such as `TBK`, `TMK`
  - full names such as `Türk Borçlar Kanunu`, `Türk Medeni Kanunu`

### 2. Cross-law candidate generation

- when the question carries multiple law signals and looks like a joint-scope query, the router now:
  - keeps the global semantic retrieval
  - adds per-law retrieval buckets
  - merges them before rerank/answer

Intent:

- reduce single-law dominance in `tmk_cross_law`
- preserve recall without forcing a single `law_filter`

### 3. Targeted retrieval expansions

Low-risk lexical/article boosts were added for:

- `aile konutu`
- `taşınmaz satış / resmi şekil / tapu / tescil`
- `paylı mülkiyet / önalım`
- `kira sözleşmesinin devri`
- `malik olmayan kişinin kiraya vermesi`
- `mal rejimi / ödünç / borç vermesi`
- `ceza şartı / cayma akçesi`
- `kefalet`
- `vekalet`
- `rekabet yasağı`
- `ihbar süresi / fesih bildirimi`
- `yıllık ücretli izin / hafta tatili`

### 4. Diagnostic subset runner

Repo-native focus runner added:

- `scripts/faz2a/run_focus_subset_eval.sh`

This runner:

- uses the FAZ 2A focus subsets
- preserves `eval_family=v3-170`
- emits `report_role=diagnostic`
- forces `--include-trace`

## Verification

- `python3 -m py_compile api-gateway/src/routers/chat.py`
- `api-gateway/.venv/bin/pytest tests/test_chat_router.py -q`
- `api-gateway/.venv/bin/pytest tests/test_eval_runner.py -q`
- `bash -n scripts/faz2a/run_focus_subset_eval.sh`
- `bash scripts/faz2a/run_focus_subset_eval.sh tmk-cross-law`

## What Is Still Open

- no live diagnostic rerun yet in this wave
- local gateways were down at execution time, so only code/test/dry-run verification was available
- source-locking and assembly hardening are intentionally deferred to the next wave unless this wave under-delivers

## Next Expected Step

When baseline/candidate lanes are available again:

1. run `tmk-cross-law` diagnostic with trace
2. run `tbk-critical` diagnostic with trace
3. classify whether the remaining failures are:
   - retrieval selection
   - context contamination
   - source-locking / answer assembly
