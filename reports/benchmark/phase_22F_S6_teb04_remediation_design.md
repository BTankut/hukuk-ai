# Phase 22F-S6-B TEB-04 KDV Teblig Remediation Design

## Decision

Use Option B with a small Option C component:

- Option B: Source exists, retrieval/metadata alias is missing.
- Option C: Source exists, but source identity/rerank cannot promote it because the candidate never enters the selected pool.

Do not use Option A. The KDV General Application Communique is present in both the canonical catalog and Milvus. Do not use Option D as the primary path; the current blocker is before scoring.

Reference audit commit:

- `cbcde5f` - `Audit TEB-04 KDV teblig source pool`

## Evidence Summary

`TEB-04` asks which main consolidated communique should be used for KDV withholding or refund questions. The current S5 run selects `ELEKTRONİK TEBLİGAT SİSTEMİ GENEL TEBLİĞİ (SIRA NO: 1)` / `24345 m.1`, which is the right family but the wrong document.

The expected KDV source exists:

- Catalog source key: `19631`
- Canonical title: `KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ`
- Family: `teblig`
- State: `active`
- Milvus rows: `3`

But the current runtime does not promote it:

- It is absent from runtime `retrieval_top_k=24`.
- It is absent from source identity `top_scores`.
- It is absent from the S5 `rerank_list`.
- Raw dense search first finds `19631` at rank `130`.
- `metadata_lookup_hit=false`.

## Narrow Remediation Surface

Future implementation should be limited to source identity and metadata-guided recall. It must not change model, prompt, generation, guardrails, scorer rubric, broad top-k, or live collection.

Allowed implementation areas:

- `api-gateway/src/rag/source_identity.py`
- `api-gateway/src/rag/source_catalog.py`
- `api-gateway/src/rag/retrieval_orchestration.py`
- narrowly scoped tests under `tests/`
- targeted benchmark report files under `reports/benchmark/`

Disallowed implementation areas:

- no QID-specific branch for `TEB-04`
- no answer-key driven runtime logic
- no broad retrieval top-k increase
- no prompt/model/fine-tuning change
- no live `8000` cutover
- no productization switch

## Proposed Mechanism

Add a generic KDV tebliğ source identity rule, not a benchmark question rule.

The rule should recognize these query signals:

- `kdv`
- `katma deger vergisi`
- `tevkifat`
- `iade`
- `konsolide`
- `ana teblig`
- `genel uygulama tebligi`

When these signals co-occur with a `TEBLIGLER` source-family intent, the metadata-guided recall layer should add source key `19631` as a candidate. The candidate should then pass through the normal source identity reranker, not bypass it.

The implementation should enrich or supplement source `19631` with aliases such as:

- `KDV Genel Uygulama Tebliği`
- `Katma Değer Vergisi Genel Uygulama Tebliği`
- `KDV uygulama tebliği`
- `KDV ana tebliğ`
- `KDV konsolide tebliğ`
- `KDV tevkifat iade tebliği`

The selector should still require family compatibility. These aliases must not promote `19631` for non-KDV tebliğ questions.

## Acceptance Gate

Minimum targeted gate before any broader benchmark:

1. Unit tests for KDV alias/signal extraction and source-key candidate generation.
2. Targeted TEB smoke including at least `TEB-04` plus adjacent TEB rows from the 100-question suite.
3. `TEB-04` must surface source `19631` / `KDV Genel Uygulama Tebliği` in selected or supporting evidence.
4. Existing non-KDV tebliğ rows must not drift to source `19631`.
5. Live `8000` must remain untouched.

Suggested targeted command shape for the future implementation phase:

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:<shadow-port>/v1 --model hukuk-ai-poc --qids TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08 --out-dir reports/benchmark/runs/<timestamp>_phase22F_S7_teb_source_identity_smoke --timeout 420 --retries 0 --sleep 0.2
```

## Risk Controls

The main risk is over-promoting `19631` for generic tax or tebliğ questions. The fix must therefore require a KDV-specific signal bundle, not just the word `teblig`.

The second risk is hiding materialization weakness. `19631` is currently represented mostly as `m0` document-level rows, including a truncated row. The S7 fix may recover source identity, but a later materialization phase may still be needed if answer completeness remains weak after the source is selected.

## Next Phase Recommendation

Open Phase 22F-S7 TEB source identity fix.

Scope:

- KDV alias/signal extraction for `19631`.
- Metadata-guided recall candidate injection for KDV tebliğ source key.
- Narrow source identity rerank support for KDV tebliğ title aliases.
- Targeted TEB smoke only.

Productization, fine-tuning, and live cutover remain closed.
