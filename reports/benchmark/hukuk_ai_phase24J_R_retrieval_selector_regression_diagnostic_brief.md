# Hukuk-AI — Phase 24J-R Retrieval / Selector Regression Diagnostic Brief

## Karar

Phase 24J-A/B/C teknik olarak geçti:

- source bundle verification PASS
- span materialization PASS
- shadow collection build PASS
- canonical/binding collision = 0
- 17 yeni span eklendi
- target collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j`

Ancak Phase 24J-D targeted smoke **FAILED**.

Kritik regresyon:

```text
MULGA-01: Phase 23R PASS -> Phase 24J FAIL
MULGA-05: Phase 23R PASS -> Phase 24J FAIL
TEB-06:   Phase 23R PASS -> Phase 24J FAIL
```

Bu stop-rule tetiklediği için:

```text
Phase 24K full shadow benchmark NOT RUN
Phase 24L = Option C, still not ready
Phase 25A/B/C NOT RUN / productization closed
```

Live `8000` değişmedi.  
Internal eval kapalı.  
Productization kapalı.  
Fine-tuning kapalı.

Sıradaki faz:

```text
Phase 24J-R — Retrieval / Selector Regression Diagnostic
```

Bu faz implementation fazı değildir. Önce regression root cause bulunacak.

---

## 1. Ana Teşhis

Phase 24J collection key/collision açısından temiz, fakat 17 yeni span eklendikten sonra eski kritik guard rows kayboldu.

Bu durum muhtemelen:

```text
candidate retrieval pool ordering değişti
selector/reranker source choice değişti
metadata/canonical source collision görünmese de score/ranking drift oluştu
new Phase24J spans query-near veya family-near olarak critical rows’u bastırdı
```

olabilir.

Bu nedenle önce iki collection karşılaştırılacak:

```text
BASE:   mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
TARGET: mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j
```

---

## 2. Kesin Kurallar

Phase 24J-R boyunca:

- live `8000` değişmeyecek
- live/base collection değişmeyecek
- new backfill yapılmayacak
- prompt/model/top-k değişmeyecek
- source identity patch yok
- answer synthesis patch yok
- QID-specific rule yok
- benchmark answer key kullanılmayacak
- full benchmark yok
- internal eval yok
- productization yok
- fine-tuning yok

Bu faz yalnız diagnostic/audit fazıdır.

---

## 3. Phase 24J-R-A — Critical Row Retrieval Diff

## Amaç

`MULGA-01`, `MULGA-05`, `TEB-06` için BASE ve TARGET collection retrieval farklarını çıkarmak.

## Rows

```text
MULGA-01
MULGA-05
TEB-06
```

## Output

```text
reports/benchmark/phase_24J_R_critical_retrieval_diff.md
reports/benchmark/phase_24J_R_critical_retrieval_diff.csv
```

## Compare

For each QID and each collection:

```text
retrieval_top_k candidates
metadata_lookup candidates
source_identity top_scores
rerank_list
selected_main_span
selected_source_key
claimed_source_identifier
answer_contract fields
trace relation fields
```

## Required fields

```text
qid
collection
candidate_rank
candidate_source_key
candidate_source_family
candidate_title
candidate_article
candidate_score_dense
candidate_score_sparse
candidate_score_rerank
candidate_is_phase24j_new_span
selected_by_selector
in_final_evidence_bundle
why_selected_or_rejected
```

## Acceptance

- 3/3 rows diffed.
- Identify whether Phase24J new spans entered top-k or selector path.
- Identify exact point where BASE pass behavior diverged from TARGET fail behavior.
- No runtime behavior change.

## Commit

```text
Audit Phase 24J critical retrieval diff
```

Push required.

---

## 4. Phase 24J-R-B — Phase24J Span Interference Audit

## Amaç

Yeni eklenen 17 span’ın critical guard rows’u etkileyip etkilemediğini belirlemek.

## Input

```text
reports/benchmark/phase_24J_span_materialization_report.md
reports/benchmark/phase_24J_catalog_delta_report.md
reports/benchmark/phase_24J_shadow_collection_build_report.md
```

## Output

```text
reports/benchmark/phase_24J_R_span_interference_audit.md
reports/benchmark/phase_24J_R_span_interference_audit.csv
```

## Fields

```text
new_span_key
new_source_title
new_source_family
new_article
qid_interfered
appears_in_top_k_for_guard_qid
rank_for_guard_qid
selector_score
reason_it_competes
should_be_scoped_away
safe_filter_candidate
```

## Guard rows

```text
MULGA-01
MULGA-05
TEB-06
```

## Acceptance

- All 17 new spans classified.
- If no interference, state that regression is runtime binding/provenance or selector nondeterminism.
- No runtime behavior change.

## Commit

```text
Audit Phase 24J new span interference
```

Push required.

---

## 5. Phase 24J-R-C — Runtime Provenance / Lane Diff

## Amaç

BASE pass ve TARGET fail koşuları arasında sadece collection mı değişti, yoksa lane/runtime/provenance farkı da var mı?

## Output

```text
reports/benchmark/phase_24J_R_runtime_provenance_diff.md
reports/benchmark/phase_24J_R_runtime_provenance_diff.json
```

## Compare

```text
api_url
lane
git_sha
model
DGX_MODEL
embedding_model
milvus_collection
entity_count
vector_dimension
guardrails
verification
presidio
source_catalog_hash
source_supplement_hash
feature flags
relation_chain flags
split_temporal_policy flags
S7/S5/S4 diagnostics availability
```

## Acceptance

- If provenance differs beyond collection/entity_count, report.
- If provenance is identical except collection, focus remediation on collection/scoping.
- No runtime behavior change.

## Commit

```text
Audit Phase 24J runtime provenance diff
```

Push required.

---

## 6. Phase 24J-R-D — Remediation Design, No Implementation

## Amaç

Root cause’a göre güvenli bir sonraki fazı tasarlamak.

## Output

```text
reports/benchmark/phase_24J_R_remediation_design.md
```

## Possible designs

### Option A — Span scoping/filter fix

If new Phase24J spans interfere with unrelated guard QIDs:

```text
Design source/family/query-scope filter.
New residual spans should only enter evidence when query/source family/domain matches.
No QID-specific branch.
```

### Option B — Shadow collection split

If Phase24J residual backfill creates unacceptable global retrieval drift:

```text
Keep Phase24J residual collection separate.
Do not merge into benchmark/live lane.
Use targeted residual evaluation only.
```

### Option C — Selector/reranker normalization

If scoring/rerank overweights new spans:

```text
Add deterministic family/source compatibility gate.
No broad top-k change.
No prompt/model change.
```

### Option D — Runtime/provenance mismatch

If lanes differ:

```text
Normalize runtime configuration and rerun targeted smoke.
No code fix until provenance equalized.
```

### Option E — Abandon Phase24J backfill

If interference cannot be safely scoped:

```text
Discard Phase24J shadow collection.
Keep Phase23R live baseline.
Continue human/source review for residuals.
```

## Commit

```text
Design Phase 24J regression remediation
```

Push required.

---

## 7. Phase 24J-R-E — Final Decision Report

## Output

```text
reports/benchmark/phase_24J_R_regression_diagnostic_report.md
```

## Include

1. commit SHA list
2. critical retrieval diff summary
3. span interference audit summary
4. runtime provenance diff summary
5. root cause
6. recommended next phase
7. productization decision
8. fine-tuning decision
9. live 8000 final state

## Decision options

```text
Open Phase 24J-S scoped span filter remediation
Keep Phase24J shadow as targeted-only
Discard Phase24J shadow collection
Rerun with normalized provenance
Return to source acquisition/legal review
```

## Commit

```text
Report Phase 24J retrieval regression diagnostic
```

Push required.

---

## 8. Productization / Fine-Tuning

Productization remains closed.

Fine-tuning remains closed.

Reason:

```text
Phase24J targeted smoke regressed critical guard rows.
This is retrieval/selector/corpus interaction, not model capability.
```

---

## Final Note

Do not patch yet.

First prove exactly why adding 17 valid residual spans broke MULGA/TEB guard rows.

The correct next action is differential diagnosis, not another remediation attempt.
