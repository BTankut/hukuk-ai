# Phase C0 — Retrieval Diagnostic Eval

**Date:** 2026-03-15  
**Status:** COMPLETE ✅  
**Branch:** chore/dgxnode2-ft-handoff  
**HEAD commit:** 27dcc6b (`feat(eval): add retrieval diagnostics before embedding ab`)  
**Session label:** hukuk-ai-phaseC0-diagnostic-eval-run

---

## 1. Purpose

Determine whether failing questions lose the expected article:
1. In retrieval (B1: not in candidates)
2. At assembly (B2: dropped during dedup/merge)
3. At token-fit (B3: dropped by budget enforcement)
4. After all of the above, in the final LLM answer (B4: in context but wrong)

---

## 2. Environment

| Parameter | Value |
|-----------|-------|
| Collection | `mevzuat_bge_m3_shadow` (1307 chunks, BGE-M3 dim=1024) |
| Profile | `shadow` (`MILVUS_COLLECTION_PROFILE=shadow`) |
| Reranker | OFF |
| Hybrid BM25 | OFF |
| Verification | OFF (`USE_VERIFICATION=false`) |
| Token budget | ACTIVE — window=32768, system_reserve=512, output_ratio=0.20 |
| DGX model | `qwen35moe` @ `http://192.168.12.243:30000/v1` |
| Embedding | `BAAI/bge-m3`, device=cpu, local backend |
| Top-k (default) | **10** (chat router `Field(default=10, ge=1, le=50)`) |
| Guardrails | enabled, strict_mode=false |

**API gateway startup command:**
```bash
cd /Users/btmacstudio/.openclaw/workspace/projects/hukuk-ai/api-gateway
DGX_BASE_URL=http://192.168.12.243:30000/v1 \
DGX_MODEL=qwen35moe \
DGX_API_KEY=not-needed \
MILVUS_ENABLED=true \
MILVUS_URI=http://localhost:19530 \
MILVUS_COLLECTION=mevzuat \
MILVUS_SHADOW_COLLECTION=mevzuat_bge_m3_shadow \
MILVUS_COLLECTION_PROFILE=shadow \
MILVUS_STRICT_PROFILE_ROUTING=true \
MILVUS_ENABLE_SHADOW_ROUTING=false \
EMBEDDING_BACKEND=local \
EMBEDDING_MODEL=BAAI/bge-m3 \
EMBEDDING_DEVICE=cpu \
LLM_CONTEXT_WINDOW=32768 \
RAG_TOKEN_SYSTEM_RESERVE=512 \
RAG_TOKEN_MIN_CHUNKS=2 \
RAG_TOKEN_OUTPUT_RESERVE_RATIO=0.20 \
GUARDRAILS_ENABLED=true \
GUARDRAILS_STRICT_MODE=false \
USE_VERIFICATION=false \
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --log-level info \
  > /tmp/hukuk-ai-gw-phaseC0.log 2>&1 &
```

**Eval run command:**
```bash
cd /Users/btmacstudio/.openclaw/workspace/projects/hukuk-ai
api-gateway/.venv/bin/python evaluation/eval_runner.py \
  --api-url http://127.0.0.1:8000 \
  --questions configs/evaluation/test_questions.json \
  --retrieval-profile shadow \
  --max-errors 3 \
  --output evaluation/reports/eval_phaseC0_diagnostic_20260315_123110.json \
  2>&1 | tee evaluation/reports/eval_phaseC0_diagnostic_20260315_123110.log
```

---

## 3. Aggregate Results

| Metric | Phase C0 | Phase B | Delta | Faz1 Threshold | Status |
|--------|----------|---------|-------|----------------|--------|
| citation_rate | **86.0%** | 82.0% | +4.0 | ≥ 80% | ✅ |
| correct_source_rate | **74.2%** | 72.5% | +1.7 | ≥ 70% | ✅ |
| hallucination_rate | **6.0%** | 4.0% | +2.0 | ≤ 10% | ✅ |
| refusal_accuracy | **98.0%** | 98.0% | 0.0 | ≥ 80% | ✅ |
| avg_latency_ms | 14,499 | 13,851 | +648 | — | — |

**All 4 Faz-1 criteria: ✅ PASSED**

Category breakdown:

| Category | n | src_rate | hal_rate |
|----------|---|----------|----------|
| tbk_genel | 23 | 75.4% | 8.7% |
| tbk_kira | 5 | 72.0% | 20.0% |
| tbk_haksiz_fiil | 5 | 90.0% | 0.0% |
| tbk_eser | 2 | 100.0% | 0.0% |
| tbk_kefalet | 2 | 100.0% | 0.0% |
| tbk_satis | 2 | 100.0% | 0.0% |
| tbk_vekaletname | 2 | 75.0% | 0.0% |
| tbk_hizmet | 2 | 75.0% | 0.0% |
| tbk_ceza_sarti | 1 | 66.7% | 0.0% |
| tmk_esya | 1 | 0.0% | 0.0% |
| tmk_genel | 2 | 0.0% | 0.0% |
| tmk_aile | 1 | 0.0% | 0.0% |

Notes:
- `tbk_kira` has the highest hallucination rate (20%) — driven by TBK-002 (m.299 missing from retrieval)
- `tmk_*` categories all 0% src_rate — expected, TMK questions are mostly out-of-scope refusals (correct behavior), but TBK-020 needs TMK m.706 coverage

---

## 4. Pipeline Health: B2 & B3 are Zero

| Stage | Count | Description |
|-------|-------|-------------|
| Assembly losses (B2) | **0** | No chunks lost during article dedup/merge |
| Token-fit losses (B3) | **0** | No chunks dropped by budget enforcement |

**Token budget utilization across all questions:**

| Range | Count | Context usage |
|-------|-------|---------------|
| 0.1–6% utilization | 44 | 36–1,480 tokens used of ~25,690 available |
| Notable outlier | TBK-012 | Only **1 candidate** retrieved (very low recall) |
| Notable outlier | TBK-011 | **20 candidates** (expansion rule boosted top_k) → perfect |

**Conclusion:** Phase A token-budget enforcement is working correctly and is NOT a bottleneck. With 1–6% token utilization and zero dropped chunks, the system has ample capacity to serve 3–5× more candidates.

---

## 5. Bucketed Findings

### B1: Expected article missing from retrieval candidates — **10 questions**

All have top_k=10 (default). At least one expected source was never retrieved.

| Question | csr | Expected (missing) | Expected (found) | Pattern |
|----------|-----|--------------------|-----------------|---------|
| TBK-002 | 0.00 ⚠️HAL | TBK m.299 | TBK m.314 | Multi-article kira; m.299 not pulled |
| TBK-003 | 0.50 | TBK m.146 | TBK m.72 | Haksız fiil + zamanaşımı; m.146 not retrieved |
| TBK-004 | 0.60 | TBK m.349 | m.347,348,350,351 | 5-article kira sona erme; one missing |
| TBK-008 | 0.50 | TBK m.436 | TBK m.435 | Adjacent article (m.435/436); m.436 not pulled |
| TBK-012 | 0.33 | TBK m.117, m.118 | TBK m.112 | Only 1 candidate returned — severe recall failure |
| TBK-016 | 0.50 | TBK m.505 | TBK m.508 | Vekalet özen; m.505 not retrieved |
| TBK-020 | 0.50 | TMK m.706 | TBK m.237 | Cross-law: TMK m.706 not in shadow collection |
| TBK-031 | 0.50 | TBK m.108 | TBK m.107 | Adjacent article (m.107/108); m.108 missing |
| TBK-033 | 0.50 | TBK m.183 | TBK m.184 | Adjacent article (m.183/184); m.183 missing |
| TBK-045 | 0.00 🚫 | TBK m.128 | TBK m.582 | Unrelated articles; m.128 not retrieved |

**Sub-patterns within B1:**

- **Adjacent article miss** (article N found, N±1 missing): TBK-008, TBK-031, TBK-033 → 3 questions  
  These are canonically fixed by adjacent-article expansion: when article M is retrieved, also include M-1 and M+1.

- **Same-topic multi-article miss** (related but non-adjacent): TBK-002, TBK-003, TBK-004, TBK-016, TBK-045 → 5 questions  
  Addressed by raising top_k; the missing articles exist in the collection but didn't rank in top 10.

- **Cross-law miss** (TMK m.706): TBK-020 → 1 question  
  TMK m.706 may not be in the shadow collection. Needs data verification.

- **Severe retrieval recall failure** (only 1 candidate): TBK-012 → 1 question  
  "Temerrüt koşulları" query returned only 1 chunk. Likely an embedding/query issue specific to this phrasing.

### B2: In candidates, lost at assembly — **0 questions**

### B3: Survived assembly, lost at token-fit — **0 questions**

### B4: In final context, answer still wrong — **4 pure questions**

All 4 have their expected articles present in final context (often at rank 1), yet the LLM produces wrong citations.

| Question | csr | Expected | Rank in context | LLM cites | Pattern |
|----------|-----|----------|----------------|-----------|---------|
| TBK-032 | 0.00 ⚠️HAL | TBK m.136 | **rank 1** | m.135, m.137 | Off-by-one hallucination |
| TBK-044 | 0.00 ⚠️HAL | TBK m.166 | **rank 1** | m.169 | Off-by-one hallucination |
| TBK-006 | 0.67 | m.179, m.180, m.182 | ranks 5, 10, 8 | m.176, m.420, m.178 extra | Context contamination + miss |
| TBK-035 | 0.50 | m.143, m.144 | ranks 2, 3 | m.139, m.142, m.326 extra | Over-citation + m.144 miss |

**Pattern:**  
- TBK-032 and TBK-044: The correct article is the **top-ranked** chunk but the LLM cites the neighboring article in the same passage. This is a known off-by-one grounding error — the LLM reads the article text but constructs the citation from adjacent headings.  
- TBK-006 and TBK-035: The correct articles are in context but the LLM adds many extra wrong citations. The context contains adjacent articles that the LLM over-cites.

### Unexpected refusal — **1 question**

| Question | Expected | Behavior |
|----------|----------|----------|
| TBK-045 | TBK m.128, TBK m.582 | Model refused despite m.582 being at rank 1 in context. TBK m.128 not in candidates. Likely triggered refusal due to "garanti vs kefalet" cross-conceptual question with only partial retrieval coverage. |

---

## 6. Token Budget: Deep Data

| Stat | Value |
|------|-------|
| Max available_for_chunks | ~25,700 tokens |
| Max chunks_dropped | 0 |
| Avg total_tokens_used | ~700–900 tokens (10 chunks × ~70–90 tokens each) |
| Max total_tokens_used | 1,480 (TBK-011 with 20 candidates) |
| Token utilization range | 0.1% – 5.8% |

**If top_k is raised to 30**: estimated 30 × ~100 tokens = ~3,000 tokens, still only ~12% utilization. Safe.  
**If top_k is raised to 50**: estimated ~5,000 tokens, ~20% utilization. Comfortable.  
**Token-budget ceiling does not block any retrieval strategy change.**

---

## 7. Diagnosis Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE          │ FAILURES │ ROOT CAUSE                             │
├─────────────────────────────────────────────────────────────────────┤
│  Retrieval (B1) │    10    │ top_k=10 too small for multi-article   │
│                 │          │ questions; adjacent articles not pulled │
│                 │          │ TBK-012: severe recall (1 candidate)    │
│                 │          │ TBK-020: TMK m.706 not in collection   │
├─────────────────────────────────────────────────────────────────────┤
│  Assembly  (B2) │     0    │ No problem                             │
├─────────────────────────────────────────────────────────────────────┤
│  Token-fit (B3) │     0    │ No problem (1–6% budget usage)         │
├─────────────────────────────────────────────────────────────────────┤
│  Context→Answer │     4    │ Off-by-one hallucination (m.136→m.135, │
│  (B4 pure)      │          │ m.166→m.169); over-citation noise      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Recommended Next Step

### PRIMARY: Retrieval / top_k / adjacent-article strategy

This addresses 10/14 failing questions (71%).

**Action 1 — Raise default top_k from 10 to 20:**
- `chat.py`: change `top_k: int = Field(default=10, ...)` to `Field(default=20, ...)`
- No code changes needed in retriever.py (already defaults to 20 there)
- Token budget impact: 0.1–6% → 0.2–12% utilization — trivially safe
- Expected gain: questions currently failing due to "article N+1 not retrieved" should fix

**Action 2 — Adjacent-article expansion:**
- When article K is retrieved at high score, also retrieve K-1 and K+1 from the collection
- Targets TBK-008 (m.435→m.436), TBK-031 (m.107→m.108), TBK-033 (m.183→m.184) specifically

**Action 3 — Investigate TBK-012 recall failure:**
- Query "temerrüt koşulları" returned only 1 candidate (m.112)
- Root cause: embedding/query mismatch for "temerrüt koşulları" + "borçlu temerrüdü" phrase
- Fix: add query expansion for "temerrüt" → include "TBK m.112 m.117 m.118 borçlu temerrüdü"

**Action 4 — Verify TMK m.706 in shadow collection:**
- `mevzuat_bge_m3_shadow` was built from TBK only; TMK m.706 may not exist
- Check: query Milvus for `article_key` containing `TMK_m706`
- Fix if absent: run targeted ingest for TMK m.706 into shadow collection

### SECONDARY: Prompt/refusal logic fix (B4 off-by-one)

This addresses 4/14 failing questions (29%), specifically the hallucination cases.

The LLM cites adjacent articles (m.135 instead of m.136, m.169 instead of m.166) even when the correct article is at rank 1. This is a known off-by-one citation grounding issue caused by:
- Article-context chunks containing neighboring article headings/text
- LLM constructing citations from the passage structure rather than the explicit chunk citation

**Fix candidates:**
- Strengthen citation instruction in prompt (explicit "cite only the exact article number shown at the beginning of each passage")
- Reduce article-context chunk size to prevent neighboring article text from bleeding in
- Add citation validation post-processing: if cited article ≠ article in any retrieved chunk, flag/block

### NOT YET: Assembly / context strategy

B2 and B3 are **zero**. Assembly and token-fit stages are working correctly.

### NOT YET: Embedding A/B (Phase C proper)

Do NOT start embedding A/B until retrieval strategy (top_k, adjacent) is addressed.  
Rationale: if 10 of 14 failures are due to insufficient top_k, embedding comparison results will be confounded by retrieval under-coverage. Raise top_k first, re-eval to get a clean baseline, then compare e5 vs BGE-M3 on the improved retrieval layer.

---

## 9. Artifacts

| File | Description |
|------|-------------|
| `evaluation/reports/eval_phaseC0_diagnostic_20260315_123110.json` | Full eval report with per-question retrieval diagnostics |
| `evaluation/reports/eval_phaseC0_diagnostic_20260315_123110.log` | Eval runner stdout log |
| `/tmp/hukuk-ai-gw-phaseC0.log` | API gateway log (ephemeral) |
| `coordination/phaseC0-diagnostic-eval-2026-03-15.md` | This document |

---

## 10. Phase C0 Verdict

| Check | Result |
|-------|--------|
| Trustworthy diagnostic? | ✅ YES — real API, shadow collection, Phase A active, 0 errors |
| B2/B3 pipeline losses? | ✅ NONE — assembly and token-fit stages working |
| Token budget a bottleneck? | ✅ NO — 1–6% utilization, zero dropped chunks |
| Primary failure identified? | ✅ YES — B1: top_k=10 insufficient, 10/14 failures |
| Secondary failure identified? | ✅ YES — B4: off-by-one hallucination, 4/14 failures |
| Next action clear? | ✅ YES — raise top_k to 20 (+ adjacent expansion) first |
| Ready for embedding A/B? | ❌ NO — retrieval strategy must be addressed first |
