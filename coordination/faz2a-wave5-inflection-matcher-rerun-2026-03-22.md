# FAZ 2A Wave 5: Inflection-Aware Matcher Rerun

Date: 2026-03-22
Owner: Codex
Scope: `tmk_cross_law` diagnostic slice (`v3-170`)

## Objective

Wave 4 sonunda iki kritik cluster acik kaldi:

- `TMK-CL-022` bagislama / edinilmis mallara katilma / tasfiye
- `TMK-CL-025` nafaka / zamanaasimi

Bu iki soruda concept-anchor kurallari tanimli olmasina ragmen `forced_article_refs` trace'e hic dusmuyordu.
Kok neden, Turkce cekimli bicimlerin (`katilma rejiminin`, `zamanaasimina`, `denklestirmeye`) tam-kelime matcher tarafinda kacirilmasiydi.

## Code Changes

- `api-gateway/src/routers/chat.py`
  - `_contains_query_term` artik son token icin kontrollu sonek toleransi veriyor.
  - False-positive guard korunuyor; kisa tokenlar (ornegin `cek`) icin kokten eslesme acilmiyor.
  - `kefalet + es rizasi` concept anchor'i yeniden daraltildi; TMK force-include yalniz `aile birligi / korunmasi ilkesi` cizgisine baglandi.
- `api-gateway/src/rag/orchestrator.py`
  - Partial-priority mismatch durumunda dar source-lock fallback korunuyor.
- Test coverage:
  - inflected Turkish phrase matching
  - short-token false-positive guard
  - cross-law retrieval / source-lock smoke kapsami

## Verification

- `python3 -m py_compile ...` PASS
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py api-gateway/tests/test_llm_client.py api-gateway/tests/test_orchestrator_smoke.py -q` PASS

## Smoke Evidence

Fresh smoke lane: `127.0.0.1:8034`

### TMK-CL-022 family

- `forced_article_refs`: `TMK m.229`, `TMK m.220`, `TBK m.285`
- retrieved top refs basina exact include girdi
- fallback cited answer: `TMK m.229`, `TMK m.220`

### TMK-CL-025 family

- `forced_article_refs`: `TMK m.182`, `TBK m.125`, `TBK m.131`
- retrieved top refs basina exact include girdi
- fallback cited answer: `TMK m.182`, `TBK m.125`

## Fresh Reruns

### Wave 4 reference

- baseline: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_182242.json`
  - citation `100.0%`
  - correct source `55.3%`
  - hallucination `10.0%`
- candidate: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_182237.json`
  - citation `100.0%`
  - correct source `54.2%`
  - hallucination `10.0%`

### Wave 5 final

- baseline: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_184143.json`
  - citation `100.0%`
  - correct source `59.4%`
  - hallucination `3.3%`
  - refusal `100.0%`
- candidate: `evaluation/reports/eval_diagnostic_faz2a_tmk_cross_law_20260322_185613.json`
  - citation `100.0%`
  - correct source `62.8%`
  - hallucination `0.0%`
  - refusal `100.0%`

## Key Deltas

- Matcher fix, `022/025` cluster'ini her iki lane'de de hallucination sinifindan cikardi.
- Candidate lane wave4 -> wave5:
  - correct source `54.2% -> 62.8%`
  - hallucination `10.0% -> 0.0%`
- Baseline lane wave4 -> wave5:
  - correct source `55.3% -> 59.4%`
  - hallucination `10.0% -> 3.3%`

Question-level candidate deltas:

- `TMK-CL-022`: `0.0 / hall` -> `0.6667 / no-hall`
- `TMK-CL-025`: `0.0 / hall` -> `0.6667 / no-hall`
- `TMK-CL-026`: `0.6667 / no-hall` korundu
- `TMK-CL-021`: `0.6667 / no-hall` korundu
- `TMK-CL-027`: hala `0.25`, dominant acik soru

## Decision

Wave 5 faydali ve kalici:

- hallucination problem'i `tmk_cross_law` slice'inda fiilen kapandi
- candidate tekrar baseline ustune cikti (`62.8 > 59.4`)

Ancak FAZ 2A henuz kapanmadi:

- candidate `correct_source_rate = 62.8%`
- gate `>= 70%`

## Next Action

Siradaki dar dalga retrieval degil, source coverage:

- anchored cross-law sorularda source-lock fallback citation count'ini query-aware sekilde `3-4` kaynaga cikarmak
- ozellikle `TMK-CL-021/022/025/026/027` ve benzer 3+ expected source cluster'larinda eksik ucuncu/dorduncu kaynagi kilitlemek
