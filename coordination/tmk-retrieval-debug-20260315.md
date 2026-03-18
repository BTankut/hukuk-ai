# TMK Retrieval Debug Report

**Date:** 2026-03-15  
**Status:** COMPLETE — Root cause identified  
**Session:** hukuk-ai-p1-tmk-debug  
**Diagnostic by:** Subagent (diagnosis only, no code changes)

---

## Executive Summary

TMK questions (TBK-047 through TBK-050) show 0% correct_source and 0% citation in Wave 4 eval. The root cause is **NOT** a retrieval failure. TMK chunks exist in the shadow collection (3390 total after Wave 4 ingest). The failure is a **hard-coded, pre-retrieval keyword refusal in the chat router** that fires before the retriever is ever called. All 4 pure-TMK questions are intercepted and returned as out-of-scope refusals.

**One secondary issue also exists:** the Phase B shadow reindex (which produced the baseline) only ingested TBK (651 articles, 1307 chunks), not TMK. TMK was added by the Wave 4 commit (`3be5f47`). The eval was run against the Wave 4 shadow collection (3390 chunks), but the refusal intercept made retrieval irrelevant for TMK questions.

---

## TMK Questions in Test Set

| ID | Category | expected_sources | refusal_expected |
|----|----------|-----------------|-----------------|
| TBK-020 | tbk_genel | TBK m.237, **TMK m.706** | False |
| TBK-047 | tmk_esya | TMK m.940 | True |
| TBK-048 | tmk_genel | TMK m.3 | True |
| TBK-049 | tmk_aile | TMK m.166 | True |
| TBK-050 | tmk_genel | TMK m.506 | True |

**TBK-020** (cross-law query): retrieved correctly — has TBK signal, refusal does not fire. `correct_source_rate=1.0`.  
**TBK-047 to TBK-050** (pure TMK): all 4 produce refusals. `correct_source_rate=0.0`, `citation_rate=0.0`.

---

## Wave 4 Eval Results — TMK Categories

| Category | count | citation_rate | correct_source_rate | avg_kw_coverage |
|----------|-------|--------------|---------------------|-----------------|
| tmk_esya | 1 | 0.0 | 0.0 | 0.0 |
| tmk_genel | 2 | 0.0 | 0.0 | 0.0 |
| tmk_aile | 1 | 0.0 | 0.0 | 0.0 |

All TMK questions: `is_refusal=True`, `refusal_correct=True` (eval marks this as correct because `refusal_expected=True`). But the actual LLM answer confirms hardcoded refusal, not retrieval-based refusal.

**Answer pattern on all 4 TMK questions:**
> "Bu soru TBK kapsamı dışı bir konuya giriyor (Türk Medeni Kanunu (TMK)). Elimdeki TBK kaynaklarıyla bu soruya yanıt veremiyorum."

---

## Root Cause Analysis

### Root Cause #1 — CONFIRMED PRIMARY (likelihood: CERTAIN)

**Hard-coded keyword refusal in `api-gateway/src/routers/chat.py`**  
Function: `_detect_scope_refusal_reason()` (lines ~60-90)

This function fires **before retrieval** and returns a TMK out-of-scope refusal string for questions matching these patterns:
- `tmk_signal` (`"tmk"` or `"medeni kanun"` in query) AND no TBK signal
- OR any of these terms in query AND no TBK signal:
  - `"anlaşmalı boşanma"`, `"boşanma"`, `"saklı pay"`, `"mirasbırakan"`, `"altsoy"`, `"taşınır rehni"`, `"teslimsiz rehin"`, `"iyiniyet karinesi"`

Simulation results confirm:
```
TBK-047: reason='Türk Medeni Kanunu (TMK)'   # 'taşınır rehni' + 'teslimsiz rehin' match
TBK-048: reason='Türk Medeni Kanunu (TMK)'   # 'tmk' + 'iyiniyet karinesi' match
TBK-049: reason='Türk Medeni Kanunu (TMK)'   # 'tmk' + 'anlaşmalı boşanma' match
TBK-050: reason='Türk Medeni Kanunu (TMK)'   # 'saklı pay' + 'mirasbırakan' + 'altsoy' match
TBK-020: reason=None                          # has TBK signal, refusal does NOT fire ✓
```

The refusal was designed when the system was TBK-only. After Wave 4 TMK data was ingested, the refusal logic was NOT updated to allow TMK questions through.

**This is the ONLY reason TMK retrieval fails. The retriever is never reached.**

---

### Root Cause #2 — SECONDARY (likelihood: HIGH, historical)

**Phase B shadow reindex omitted TMK** (`scripts/run_ingest.py` default: `--law tbk`)

The Phase B reindex command (no `--law` argument) used the default `--law tbk`, producing 651 articles / 1307 chunks. TMK was added in Wave 4 commit `3be5f47` with `--law all` (1032 TMK articles → 2083 chunks → total 3390). The eval (`eval_wave4_tmk_expansion_20260315.json`) ran against the 3390-chunk shadow collection, so TMK data **was present** during Wave 4 eval. But it was irrelevant because Root Cause #1 prevented retrieval.

The Phase 3 plan's "3390 chunks" figure is correct for the shadow collection at eval time.

---

### Root Cause #3 — NOT A FACTOR (confirmed absent)

**Embedding query prefix bias toward TBK**: No evidence. The BGE-M3 embedder uses no law-specific instruction prefix. Embed path is symmetric.

**Namespace / law filtering in retriever**: No automatic law filter applied unless `law_filter` param is passed. MetadataFilter is None by default.

**Metadata field mismatch (TMK vs TBK)**: TMK chunks store `law_short_name="TMK"` and `law_no="4721"`. The retriever citation property correctly uses `law_short_name`. No metadata structural difference that would cause retrieval degradation.

**Token budget dropping TMK chunks**: Irrelevant — retrieval is never invoked.

---

## Files Requiring Changes

### MUST FIX — `api-gateway/src/routers/chat.py`

**Function:** `_detect_scope_refusal_reason()` (~line 62-90)

The TMK branch of this function must be removed or conditioned on whether TMK data is available in the collection. Since TMK is now in the index (3390 chunks), the refusal keyword list for TMK terms is stale.

**Also in the same file:** The `tmk_domain_terms` list hardcodes domain knowledge that belongs to the retriever's ranking, not the router's gating logic. The system prompt already instructs the LLM to refusal when no relevant chunks are found — the router should not preempt that.

**Specific change needed:** Remove or gate the TMK refusal block. The `test_questions.json` marks TBK-047 to TBK-050 as `refusal_expected=True` — but the correct behavior is: **retriever retrieves TMK chunks → LLM answers citing TMK sources**. The `refusal_expected` field in test questions appears to be a historical artifact from when TMK data was not yet indexed. These should be changed to `refusal_expected=False` after the router fix, and the expected sources should be verified against actual answers.

### SECONDARY — `configs/evaluation/test_questions.json`

Questions TBK-047 to TBK-050 have `refusal_expected=True`. This was set when TMK data was not in the system (Faz 1 scope). After the router fix + TMK data is confirmed retrievable:
- Change `refusal_expected` to `false`
- Verify `expected_keywords` and `expected_answer_contains` are accurate for these questions

### INFORMATIONAL — `scripts/run_ingest.py`

Default `--law tbk` should probably be changed to `--law all` or documented clearly. Any future reindex without `--law all` will silently drop TMK data again.

---

## Concrete Fix Recommendations

### Fix 1 (High Priority): Remove TMK keyword refusal from chat.py

In `_detect_scope_refusal_reason()`, remove or comment out the TMK block:

```python
# REMOVE THIS BLOCK (or condition on collection content):
# tmk_signal = ("tmk" in q) or ("medeni kanun" in q)
# tmk_domain_terms = [...]
# if (tmk_signal and not has_tbk_signal) or (...):
#     return "Türk Medeni Kanunu (TMK)"
```

The LLM + system prompt already handles out-of-domain questions gracefully via the `REFUSAL` rule in `SYSTEM_PROMPT_STRICT`. No keyword gating needed.

### Fix 2 (Medium Priority): Update test_questions.json

After Fix 1 is deployed and verified:
- Set `refusal_expected: false` for TBK-047, TBK-048, TBK-049, TBK-050
- Verify expected answers against actual retrieval

### Fix 3 (Low Priority): Document/change run_ingest.py default

Change default `--law tbk` to `--law all` or add a prominent warning in the script output when TMK is not ingested.

---

## VERDICT

**The most likely root cause is: Hard-coded keyword refusal in `api-gateway/src/routers/chat.py` (`_detect_scope_refusal_reason` function) intercepts all TMK questions before they reach the retriever.**

The retriever, embedder, collection data, and metadata are all correct. TMK chunks exist in the shadow collection (2083 chunks, correctly indexed with `law_short_name="TMK"`). The BGE-M3 embedding has no TMK bias. The failure is 100% a router-level policy gate that was appropriate when the system was TBK-only but was not updated after Wave 4 TMK data ingestion.

Expected impact of Fix 1: TMK `correct_source_rate` should jump from 0% to approximately 70-90% (subject to retrieval quality), adding roughly **+3 to +5pp** to the overall `correct_source_rate` (currently 81.9%, target 85-87%).
