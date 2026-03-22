# FAZ 2A Wave 6: Source-Lock Coverage Rerun

Date: 2026-03-22
Owner: Codex
Scope: `tmk_cross_law` diagnostic slice (`v3-170`)

## Objective

Wave 5 sonunda `tmk_cross_law` slice'i artik hallucination tarafinda buyuk olcude toparlanmisti, ancak candidate lane hala `correct_source_rate = 62.8%` ile gate altindaydi.

Kalan baskin pattern, retrieval miss degildi:

- exact/forced article family dogru kuruluyor
- top priority chunk'lar dogru geliyor
- ama yanit bu priority set'in eksik alt kumesini cite edip source-lock fallback'i kaciriyordu

Wave 6 hedefi bu coverage boslugunu kapatmakti.

## Code Changes

- `api-gateway/src/routers/chat.py`
  - `source_lock_target_citations` artik explicit + forced article ref sayisindan turetiliyor.
  - `mal rejimi / borc verme` concept anchor'i daraltildi; generic `borc` sinyali yerine gercek `esler arasi odunc / diger ese borc vermesi` hattina baglandi.
  - `hayatta kalan es / katilma alacagi / sebepsiz zenginlesme` family'i artik `TMK-CL-027` gibi sorularda yalniz dogru expansion'i uretiyor.
- `api-gateway/src/rag/orchestrator.py`
  - source-lock fallback, query-aware citation count ile `2-4` priority chunk'a kadar cikiyor.
  - yeni `incomplete priority coverage` kuralı eklendi:
    - `3+` expected-source sorularda model dogru priority set'in yalniz eksik alt kumesini verirse fallback zorlanir.
- Test coverage
  - cross-law death-regime anchor collision regression
  - 3-source source-lock expansion
  - incomplete-priority subset recovery

## Verification

- `python3 -m py_compile api-gateway/src/rag/orchestrator.py api-gateway/src/routers/chat.py api-gateway/tests/test_orchestrator_smoke.py api-gateway/tests/test_chat_router.py` PASS
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_orchestrator_smoke.py api-gateway/tests/test_chat_router.py api-gateway/tests/test_llm_client.py -q` PASS

## Live Smoke Evidence

Fresh candidate lanes:

- `127.0.0.1:8038`
- `127.0.0.1:8040`

Key smoke outcomes:

- `TMK-CL-027` family:
  - source collision temizlendi
  - citations: `TBK m.77`, `TMK m.226`, `TMK m.240`, `TMK m.499`
  - `applied_expansions` yalniz dogru olum/katilma alacagi family'ini tasidi
- `TMK-CL-028` family:
  - incomplete-coverage fallback duzeldi
  - citations: `TBK m.19`, `TBK m.285`, `TMK m.561`
- `TMK-CL-013` family:
  - family-home cluster artik 4-source fallback verebiliyor
  - citations: `TBK m.349`, `TMK m.194`, `TMK m.169`, `TMK m.197`

## Fresh Reruns

### Wave 5 reference

- baseline: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_184143.json`
  - citation `100.0%`
  - correct source `59.4%`
  - hallucination `3.3%`
- candidate: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_185613.json`
  - citation `100.0%`
  - correct source `62.8%`
  - hallucination `0.0%`

### Wave 6 interim

- baseline: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_baseline_wave6_20260322_1930.json`
  - citation `100.0%`
  - correct source `73.6%`
  - hallucination `3.3%`
- candidate: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_candidate_wave6_20260322_1930.json`
  - citation `100.0%`
  - correct source `69.7%`
  - hallucination `3.3%`

Interim conclusion:

- broad source-lock expansion dogru yone itti
- ama candidate hala `0.3pp` ile gate altinda kaldi
- remaining low-cost gap, anchored questions'da eksik subset cite pattern'iydi

### Wave 6 final matched rerun

- baseline: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_baseline_wave6d_20260322_1946.json`
  - citation `100.0%`
  - correct source `74.7%`
  - hallucination `3.3%`
  - refusal `96.7%`
- candidate: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_candidate_wave6d_20260322_1946.json`
  - citation `100.0%`
  - correct source `74.7%`
  - hallucination `3.3%`
  - refusal `100.0%`

## Key Deltas

- candidate wave5 -> wave6 final:
  - correct source `62.8% -> 74.7%`
  - hallucination `0.0% -> 3.3%`
- baseline wave5 -> wave6 final:
  - correct source `59.4% -> 74.7%`
  - hallucination `3.3% -> 3.3%`

Question-level high-signal gains on candidate:

- `TMK-CL-027`: `0.25 -> 1.00`
- `TMK-CL-028`: `0.3333 -> 1.00`
- `TMK-CL-022`: `0.6667 -> 1.00`
- `TMK-CL-025`: `0.6667 -> 1.00`
- `TMK-CL-026`: `0.6667 -> 1.00`

Residual shared weak points remain:

- `TMK-CL-015`
- `TMK-CL-021`
- `TMK-CL-030`

But these no longer block requalification.

## Decision

Wave 6 succeeded.

`tmk_cross_law` is now requalified on a fresh matched baseline/candidate pair:

- both lanes satisfy `citation >= 80%`
- both lanes satisfy `correct_source_rate >= 70%`
- both lanes satisfy `hallucination <= 10%`
- both lanes satisfy refusal gate

FAZ 2A should now move off `tmk_cross_law` and continue with the next focus slice.

## Next Action

Shift the active FAZ 2A lane from `tmk_cross_law` to `tbk_critical`:

- keep current source-lock coverage logic
- reuse trace-enabled matched rerun method
- freeze a new failure pack / delta note only if the next slice stalls below gate
