# v2 Full Eval — Failure Analysis & Fix Plan

**Date:** 2026-03-15  
**Eval:** `evaluation/reports/eval_v2_full_20260315.json`  
**Questions:** 95 | **Retrieval profile:** shadow  
**Status:** ❌ FAZ 1 KRİTERLERİ KARŞILANMADI  

| Metric | Threshold | Actual | Status |
|--------|-----------|--------|--------|
| citation_rate | ≥80% | 81.1% | ✅ |
| correct_source_rate | ≥70% | 66.3% | ❌ (-3.7pp) |
| hallucination_rate | ≤10% | 9.5% | ✅ (marginal) |
| refusal_accuracy | ≥80% | 75.8% | ❌ (-4.2pp) |

Wave 4 baseline (50q): correct_src=81.9%, citation=88%, hal=4%, refusal=100%  
v2 regression is primarily from the **4 new failing categories** added in v2.

---

## Category Overview

| Category | n | correct_src | hal | refusal_acc | Status |
|----------|---|------------|-----|-------------|--------|
| out_of_scope | 10 | 100% | 0% | **30%** | ❌ refusal detection broken |
| hal_prone | 10 | 33% | 30% | **40%** | ❌ over-refusal + retrieval gap |
| tmk_cross_law | 10 | 40% | **40%** | 100% | ❌ cross-law retrieval fails |
| tbk_hizmet | 9 | 57% | 11% | 78% | ⚠️ low candidate count |
| tbk_genel | 15 | 70% | 7% | 93% | ⚠️ borderline |
| tbk_kira | 8 | 81% | 0% | 100% | ✅ |
| tbk_haksiz_fiil | 5 | 90% | 0% | 80% | ✅ |
| tbk_satis | 5 | 100% | 0% | 100% | ✅ |

---

## Category 1: out_of_scope (n=10) — refusal_accuracy=30%

### Observed behavior
- 3/10 correct: OOS-003 (TTK), OOS-007 (TTK), OOS-008 (HMK)
- 7/10 failed: TCK × 3, İİK × 3, HMK × 1

All 7 failing cases: model DID produce a refusal-like statement. The detector simply **failed to recognize it**.

### Root cause analysis

**Cause A — Pattern gap: `yanıtlayamam` (not covered)**  
The model frequently outputs `"...yanıtlayamam"` (I cannot answer), but `REFUSAL_PATTERNS` only covers:
- `yanıtlanamaz` (passive form)
- `yanıt veremiyorum` (present tense, different conjugation)

NOT covered: `yanıtlayamam` (aorist negative), `cevaplayamam`, `bilgi veremem`, etc.

Affects: OOS-001, OOS-004, OOS-005, OOS-009 confirmed from answer text.

**Cause B — Markdown formatting breaks pattern**  
LLM wraps words in bold: `"bilgi **bulunmamaktadır**"` and `"hükümleri **bulunmamaktadır**"`.  
The regex `bilgi\s+bulunmamaktadır` does not match because `\s+` cannot span `**`.

Affects: OOS-006, OOS-010.

**Cause C — Partial refusal (genuine behavior issue)**  
OOS-002 (İİK itiraz süresi) and OOS-010 (tasarrufun iptali): Model says "İİK hükümleri bulunmamaktadır" but then lists TMK/TBK articles that contain related (but wrong-law) terms (e.g., "itiraz süresi" appearing in TMK m.435 for guardianship). The model correctly identifies the law is out of scope but leaks tangentially-related content. This is genuine model behavior that needs system prompt attention.

### System prompt assessment
`SYSTEM_PROMPT_STRICT` rule 3 says: _"Eğer sağlanan kaynaklarda soruyu yanıtlayacak bilgi yoksa: 'Bu soruyu mevcut belgeler kapsamında yanıtlayamıyorum.' de."_

- This exact phrase is NOT in REFUSAL_PATTERNS! The phrase is `"yanıtlayamıyorum"` in the prompt but pattern covers `"yanıt veremiyorum"` — close but not identical.
- The partial-refusal problem (Cause C) is because the prompt says "if there's no info → refuse" but doesn't explicitly say "do NOT list unrelated articles from other laws."

### Fix recommendations (ranked)

| # | Fix | Type | Impact |
|---|-----|------|--------|
| 1 | Add `yanıtlayamam`, `yanıtlayamıyorum`, `cevaplayamam`, `bilgi\s+veremiyorum` to `REFUSAL_PATTERNS` | **Eval code** | +3-4 OOS questions → +3-4pp refusal_acc |
| 2 | Strip markdown before regex matching: `re.sub(r'\*+', '', normalized)` in `detect_refusal()` | **Eval code** | +2 OOS questions → +2pp refusal_acc |
| 3 | Add phrase from system prompt itself: `r"bu\s+soruyu\s+mevcut\s+belgeler\s+kapsamında\s+yanıtlayamıyorum"` | **Eval code** | +1-2pp |
| 4 | System prompt: add explicit instruction "Kapsam dışı sorularda, kısmen ilgili görünse de başka kanun maddelerini listeleme." | **Prompt engineering** | Fix Cause C → +1-2pp refusal_acc |
| 5 | Router `_detect_scope_refusal_reason()`: add TCK/İİK keyword detection (currently only İş Kanunu/TTK covered) | **Code** | Deterministic catch for TCK/İİK → +4pp refusal_acc maximum |

**Expected total impact of fixes 1-3:** +5-7pp refusal_acc (75.8% → 81-83%) ✅ passes threshold  
**Fix 5 (router deterministic)** is highest-certainty but requires maintaining keyword lists.

---

## Category 2: hal_prone (n=10) — hal=30%, correct_src=33%, refusal_acc=40%

### Observed behavior
These questions are designed to trap hallucination: cross-article interactions, false logical claims, nonexistent articles.

Breakdown:
- **True hallucination (3/10):** HAL-002, HAL-004, HAL-008
- **False refusal / over-refusal (6/10):** HAL-001, HAL-003, HAL-004, HAL-005, HAL-008, HAL-010
- **Correct (4/10):** HAL-006, HAL-007, HAL-009 (no-answer trap), HAL-010 partial

refusal_accuracy=40% is INVERTED for this category: all 10 have `refusal_expected=False` so model SHOULD answer. Model refusing = wrong.

### Root cause analysis

**Cause A — Over-refusal on cross-article questions**  
Questions explicitly mention 2 article numbers (e.g., "TBK m.136 ve TBK m.49"). When retrieval returns chunks for one article but NOT the other, the model refuses entirely ("m.49 kaynaklarda bulunmamaktadır"). Expected behavior: answer with what IS available, explicitly noting the other article wasn't retrieved.

HAL-005 is the clearest case: cited the right sources (m.512, m.27), answered correctly, but added one hedging line that triggered refusal detection. Score: penalized for being too cautious in wording.

**Cause B — Adjacent article hallucination from retrieval gap**  
HAL-002: Expected m.583+m.584, got m.27 (the retrieved context didn't have m.583/m.584 and model filled with general contract invalidity)  
HAL-004: Expected m.136+m.49, got m.112+m.182 (retrieved imkansızlık neighborhood, not haksiz_fiil)  
HAL-008: Expected m.475+m.219+m.227, got m.476+m.478 (adjacent eser maddeleri)

Pattern: **when the exact article isn't retrieved, the LLM cites the nearest semantic neighbor from what IS in context.** This is citation drift, not pure invention.

**Cause C — HAL-001: TBK m.344 stored as Geçici Madde**  
HAL-001 expected m.344 but got m.G1, m.G2 (Geçici Maddeler 1 & 2). The kira artış sınırlaması rules are in Geçici Maddeler of TBK, not m.344 itself. This may be:
- A data/indexing issue (Geçici maddeler indexed as m.G1/m.G2 but eval expects m.344 citation)
- OR an eval-data error (expected_sources should include m.G1/m.G2)

**Cause D — Partial answer triggers false refusal detection (TBK-096 analog in HAL)**  
HAL-005: answered correctly but the hedging phrase was detected as refusal. The `detect_refusal()` function has no concept of "partial refusal" — any match anywhere in the answer = full refusal.

### Fix recommendations (ranked)

| # | Fix | Type | Impact |
|---|-----|------|--------|
| 1 | System prompt: add rule "Eğer soruda belirtilen maddelerden biri kaynaklarda yoksa, bulduklarınla yanıtla ve hangi maddeyi bulamadığını belirt. Tamamen reddetme." | **Prompt engineering** | Reduces over-refusal → +2-3pp correct_src, +3-4pp refusal_acc |
| 2 | `detect_refusal()`: consider position/proportion — if refusal phrase is only in last 20% of answer and citations exist, treat as partial-answer not full-refusal | **Eval code** | Fixes HAL-005, TBK-096 false-refusal → +1-2pp refusal_acc |
| 3 | HAL-001 eval data: verify whether `expected_sources=['TBK m.344', 'TBK m.72']` is correct; if Geçici Maddeler (m.G1/m.G2) are the actual relevant hükümler for kira artış, update expected_sources | **Eval data** | +1 question |
| 4 | Retrieval: for queries mentioning specific article numbers explicitly (detected by `query_parser`), boost retrieval to include those specific articles even if semantic score is low | **Code** | Fixes citation drift (Cause B) → +2-3 HAL questions |
| 5 | HAL-004, HAL-008: verify TBK m.49, m.136, m.475 are actually in Milvus index; if missing, re-ingest | **Data/infra** | May fix 2 hallucinations |

**Expected total impact:** +4-6pp correct_src for hal_prone (33% → 37-39%), +4-5pp refusal_acc (40% → 44-45%)  
Note: hal_prone is a hard adversarial category by design; 60-70% is a realistic ceiling without fine-tuning.

---

## Category 3: tmk_cross_law (n=10) — hal=40%, correct_src=40%

### Observed behavior
refusal_accuracy=100% ✅ (model correctly answers all — no false refusals)  
Problem: answers cite WRONG articles despite full retrieval (20 candidates).

Breakdown:
- correct_src=1.00: 2/10 (TMK-CL-001, TMK-CL-007)
- correct_src=0.67: 1/10 (TMK-CL-003)  
- correct_src=0.50: 3/10 (TMK-CL-002, TMK-CL-004, TMK-CL-009... wait TMK-CL-009 is hal)
- is_hallucination=True: 4/10 (TMK-CL-005, TMK-CL-008, TMK-CL-009, TMK-CL-010)

### Root cause analysis

**Cause A — Semantic neighborhood mismatch for cross-law queries**  
Each question asks about concepts spanning TBK + TMK. The embedding retrieval returns semantically similar chunks but from the wrong article numbers:

- TMK-CL-008: Query is about önalım (preemption). Expected TBK m.207 + TMK m.732. Cited TBK m.240-242 (ön alım tarife in satis context) + TMK m.734. The retrieval is finding "alım" articles broadly, not specifically önalım hakkı.
- TMK-CL-010: Query is about eşler arası ödünç + mal rejimi. Expected TBK m.386 + TMK m.202, m.223. Cited TMK m.217, m.270, m.268, m.273 — completely wrong section of TMK (edinilmiş mallara katılma instead of mal ortaklığı/ayrılığı).
- TMK-CL-009: Query about kira devri in divorce. Expected TBK m.323 + TMK m.194. Cited only TBK m.349 (kiracının ölümü feshi) — retrieval confused "boşanma + kira sözleşmesi devri" with "kira sözleşmesinin sona ermesi".
- TMK-CL-005: Expected TBK m.299 + TMK m.683. Cited TBK m.308, m.310, TMK m.865, m.844 — retrieval found kiralamanın sona ermesi articles instead of kira sözleşmesinin kurulması.

**The core pattern:** The query's semantic anchor is a legal concept (boşanma, ödünç, önalım), and the embedding space clusters related-but-wrong articles. The retrieval system doesn't know it needs EXACTLY m.323 + m.194, it retrieves the 20 most similar chunks.

**Cause B — Missing TBK anchor article in cross-law retrieval**  
TMK-CL-004: Expected TBK m.237 (taşınmaz satışı şekil) + TMK m.706. Cited only TMK m.706. The TBK side of the cross-law question was not retrieved. This suggests TBK m.237 has low semantic similarity to "taşınmaz satış sözleşmesi resmi şekil" query — likely because m.237 is a short/dense article and the query contains "TMK bakımından" which steers embedding toward TMK clusters.

**Cause C — TMK mal rejimi articles are semantically adjacent**  
TMK-CL-010 and TMK-CL-002 show retrieval finding "close but wrong" TMK articles in the same section (aile hukuku, mal rejimi). TMK m.202 (yasal mal rejimi) vs m.217 (edinilmiş mallar), m.223 (kişisel mallar) — these are semantically very close. Without article-level precision, the model cites the semantic neighborhood, not the specific article.

**Cause D — Eval data quality check**  
TMK-CL-009: "Boşanma sürecindeki eşlerden biri tarafından aile konutu kira sözleşmesinin devri". Expected TBK m.323 (kiracının kira sözleşmesini devretme hakkı). But the question specifically mentions "boşanma" + "aile konutu" which might also involve TBK m.349 (aile konutu kirasının sona erdirilmesi). Expected sources might be incomplete.

### Fix recommendations (ranked)

| # | Fix | Type | Impact |
|---|-----|------|--------|
| 1 | Query rewriting: for cross-law queries detected by `query_classifier` (LawScope.CROSS_LAW), issue 2 parallel retrieval queries — one TBK-focused, one TMK-focused — then merge top-k | **Code** | +3-4pp correct_src → ~54-60% for tmk_cross_law |
| 2 | Article-ID boosting: when query_parser detects explicit article references (e.g., "TBK m.323"), force-include that article in retrieved context regardless of semantic score | **Code** | Fixes TMK-CL-004, CL-009 → +1-2 questions |
| 3 | System prompt: add "Cross-law sorularda her iki kanundan da kaynak göster; yalnızca bir kanundan atıf yeterli değildir." | **Prompt engineering** | +1-2pp (citation completeness) |
| 4 | Eval data review: TMK-CL-009 (TBK m.323 vs m.349), TMK-CL-005 (TBK m.299 vs m.308-310) — verify expected_sources completeness with legal domain expert | **Eval data** | +1-2 questions if expected_sources corrected |
| 5 | Adjacent-expansion tuning: for TMK mal rejimi questions, limit adjacent expansion to ±3 articles (currently may pull in wrong section) | **Code** | +1pp, prevents CL-010 type errors |

**Expected total impact of fix 1+2:** tmk_cross_law correct_src: 40% → 55-65%  
System-wide impact: +1.5-2.5pp correct_source_rate  
Note: Fix 1 requires architecture change in retrieval pipeline (parallel queries + merge).

---

## Category 4: tbk_hizmet (n=9) — correct_src=57%, hal=11% (lower priority)

### Root cause analysis

**Cause A — Low candidate count (only 3 vs. expected 20) for TBK-094, TBK-096, TBK-097, TBK-098**  
Retrieval returns only 3 candidates. This means hizmet sözleşmesi articles (m.393-m.447 range) may be:
- Under-indexed (fewer chunks in Milvus for this section)
- Low embedding scores (hizmet articles are highly domain-specific labor law vocabulary)
- Adjacent expansion not triggering for this article range

TBK-094: Got m.396, m.395, m.397 (correct articles!) but model said their content was insufficient to answer about "coğrafi kapsam, süre ve alan sınırları" — the articles are there but don't have the detail the question asks for.

**Cause B — False refusal detection (TBK-096)**  
Model answered fully with TBK m.432 (correct), but added "m.433 hakkında bilgi bulunmamaktadır" in the closing. The `detect_refusal()` function marked the entire answer as refusal. Expected: partial-answer should not count as full refusal when the primary question is answered.

**Cause C — Off-by-one citation (TBK-097)**  
Expected TBK m.401 + m.408, cited TBK m.402 + m.400 — adjacent article numbers. Retrieval likely didn't include m.401 (ücretin ödenmesi borcu itself) in the 3-candidate set; only got neighboring articles.

### Fix recommendations (ranked)

| # | Fix | Type | Impact |
|---|-----|------|--------|
| 1 | `detect_refusal()` context-aware: if >2 citations exist and refusal phrase is in subordinate clause/footnote, don't flag as full refusal | **Eval code** | Fixes TBK-096 false-refusal → +1pp |
| 2 | Investigate why hizmet section returns only 3 candidates: check Milvus embedding density for TBK m.393-m.447 range; re-embed if sparse | **Infra/data** | May fix TBK-094, TBK-097, TBK-098 → +2pp |
| 3 | Query expansion for hizmet queries: add "hizmet sözleşmesi TBK m.393-m.447" to retrieval query | **Code** | Low-risk fallback → +1pp |

---

## Consolidated Fix Roadmap

### Priority 1: Eval Code Fixes (no system risk, high ROI)
These fix the metrics without touching production code:

1. **`REFUSAL_PATTERNS` additions** (metrics.py):
   - Add: `r"yanıtlayamam"`, `r"yanıtlayamıyorum"`, `r"cevaplayamam"`, `r"bilgi\s+veremiyorum"`, `r"bilgi\s+veremem"`
   - Add: `r"bu\s+soruyu\s+mevcut\s+belgeler\s+kapsamında\s+yanıtlayamıyorum"` (literal from system prompt)
   - Strip `**` markdown before matching: `normalized = re.sub(r'\*+', '', normalized)` before the pattern loop
   - **Impact:** +5-7pp refusal_accuracy → OOS fixes 4-5 questions

2. **`detect_refusal()` position-aware** (metrics.py):
   - If citations exist AND refusal phrase is in last 30% of answer AND answer length > 200 chars → treat as "partial answer" not refusal
   - **Impact:** +1-2pp refusal_accuracy → fixes TBK-096, HAL-005

3. **Eval data review** (test_questions_v2.json):
   - HAL-001: verify if `TBK m.G1`, `TBK m.G2` should be in expected_sources for kira artış questions
   - TMK-CL-009: verify TBK m.323 vs m.349 for "aile konutu kira devri boşanma" scenario

**Estimated impact (eval fixes only):** refusal_accuracy: 75.8% → 83-85% ✅ | correct_source: minimal change

### Priority 2: Prompt Engineering (no code change, medium effort)

4. **System prompt additions** (prompt_builder.py `SYSTEM_PROMPT_STRICT`):
   - "Soru birden fazla madde içeriyorsa, hangi maddelerin kaynaklarda bulunduğunu, hangilerinin bulunmadığını belirt. Ancak bulunan maddeler için yanıt ver — tamamen reddetme."
   - "Kapsam dışı sorularda, kısmen benzer görünen diğer kanun maddelerini listeleme."
   - **Impact:** +1-2pp correct_source, fixes OOS Cause C, reduces hal_prone over-refusal

5. **Router `_detect_scope_refusal_reason()`** (chat.py):
   - Add TCK keyword detection: `tck`, `ceza kanunu`, `suç`, `hapis`, `ceza`
   - Add İİK keyword detection: `iik`, `icra`, `haciz`, `konkordato`, `iflas`
   - **Impact:** Deterministic catch for 6/7 OOS failures → +4pp refusal_acc (but adds maintenance burden)

### Priority 3: Code Changes (medium effort, highest long-term impact)

6. **Cross-law parallel retrieval** (retriever/orchestrator):
   - When `query_classifier` returns `LawScope.CROSS_LAW`: split query into TBK-filtered + TMK-filtered retrievals, merge top-k/2 from each
   - **Impact:** tmk_cross_law correct_src: 40% → 55-65% → +1.5-2pp system-wide

7. **Article-ID force-include** (retriever):
   - When `query_parser` fires on explicit article refs (e.g., "TBK m.323"), ensure those articles appear in context regardless of semantic rank
   - **Impact:** Fixes TMK-CL-004, CL-009, HAL-004, HAL-008 type errors → +2-3pp correct_src

8. **Hizmet section re-embedding check**:
   - Debug why TBK-094/097/098 get only 3 candidates; check Milvus density for m.393-447
   - **Impact:** tbk_hizmet correct_src: 57% → 70-75% → +0.5-1pp system-wide

---

## Expected Score Impact (if all fixes applied)

| Fix group | refusal_acc delta | correct_src delta |
|-----------|-------------------|-------------------|
| P1: Eval code fixes | +7-9pp (75.8→83-85%) | +0-1pp |
| P2: Prompt engineering | +3-4pp | +1-2pp |
| P3: Code changes | +1-2pp | +4-6pp |
| **Total** | **+11-15pp → ~87-91%** ✅ | **+5-9pp → ~71-75%** ✅ |

**Both Faz 1 thresholds reachable** with P1+P2 (eval+prompt) combination.  
P3 needed to reach Wave 4 parity (correct_src≥81%) at the 95-question scale.

---

## Critical Path for Next Eval

1. **Fastest win (1-2 hours):** Apply P1 eval code fixes → re-run eval → expect refusal_accuracy to pass  
2. **Day 1:** Apply P2 system prompt → re-run eval → expect correct_source improvement on hal_prone  
3. **Day 2-3:** Implement P3 fixes 6+7 (parallel retrieval + force-include) → major tmk_cross_law improvement  

Do NOT touch the wave 4 data pipeline or chunking — token budget is at 1-7% utilization (not a bottleneck).

---

*Generated by failure-bucket-analysis subagent | hukuk-ai-p3-failure-bucket-analysis*
