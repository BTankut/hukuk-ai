# Phase 24HS-A - TEB Active Temporal Guard Audit

## Scope

- Target failure: `TEB-04`.
- Baseline run: `reports/benchmark/runs/phase_24HR_option_C_targeted_candidate_smoke`.
- Candidate run: `reports/benchmark/runs/phase_24HS_focused_non_live_candidate_smoke_final_v6`.
- Non-live endpoint: `http://127.0.0.1:8041/v1`.
- Live `8000`: not modified.

## Baseline Failure

| QID | Baseline claim | Baseline score | Failure |
| --- | --- | ---: | --- |
| `TEB-04` | `MULGA`, `19631 m.2`, `madde:2`, `repealed` | `0.00 FAIL` | active KDV GUT source was surfaced as repealed/MULGA and auto-failed |

The selected source family was close to the right document identity, but temporal/surface synthesis rewrote an active teblig source into a historical claim surface. The immediate root cause was that active consolidated teblig states such as `current_consolidated` / `consolidated_current` were not treated as active non-repealed states by the final temporal claim guard. A second issue was answer-surface granularity: a document-level "which consolidated text should be used" question was forced into an article-level `19631 m.2` surface.

## Audit Questions

| Question | Result |
| --- | --- |
| Why did source `19631` get claimed as MULGA/repealed? | Active consolidated state aliases were not preserved as active non-MULGA during temporal claim finalization. |
| Which temporal policy produced repealed surface? | The final temporal claim/surface preservation path allowed historical-claim surface despite an active TEBLIGLER source. |
| Was source effective_state active/amended? | Candidate trace now resolves the KDV GUT document-level source as `active`. |
| Was relation_chain_expansion_applied incorrectly? | No evidence that relation-chain expansion was required for this document-level query. The fix is temporal preservation, not relation expansion. |
| Was historical_claim_surface_allowed incorrectly true? | Effectively yes for this surface: active TEBLIGLER should not enter MULGA/repealed claim text without explicit repeal relation. |
| Was claim_family_rewrite_allowed incorrectly true? | The final claim surface allowed the visible family to drift. The candidate preserves `TEBLIGLER`. |

## Systemic Guard Implemented

Implemented in `api-gateway/src/rag/answer_synthesis.py`:

- Treat `current_consolidated` and `consolidated_current` as active non-repealed states.
- Preserve `TEBLIGLER` claim family for active/amended/unknown-non-repealed sources unless an explicit repeal relation exists.
- Apply the same active-source clamp to active non-MULGA preservation and teblig-domain mismatch surfaces.
- Detect document-level teblig source identity questions and keep the claim at `m.0` / `document_level` instead of inventing article-level scope.

Benchmark runner source-surface extraction was also tightened in `scripts/benchmark/run_hukuk_ai_100.py` so answer-visible current-law basis fields are captured without reintroducing full trace candidate pollution.

## Candidate Result

| QID | Candidate claim | Candidate score | Result |
| --- | --- | ---: | --- |
| `TEB-04` | `TEBLIGLER`, `19631 m.0`, `document_level`, `active` | `8.15 PASS` | no MULGA/repealed claim, no auto-fail |

Candidate answer surface:

```text
Güncellik/yürürlük sınırı:
- Esas alınacak ana konsolide metin: KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ; 19631 m.0; belge düzeyi. [Kaynak: 19631 m.0]
- Sınır: Bu cevap belge kimliğini bildirir; somut tevkifat/iade uygulamasında ilgili bölüm ve madde ayrıca seçilmelidir.
```

## Decision

The Phase 24HS active TEB temporal guard is accepted for the focused candidate. It is systemic: it is keyed to source family/effective state/document-level query semantics, not to `TEB-04`.
