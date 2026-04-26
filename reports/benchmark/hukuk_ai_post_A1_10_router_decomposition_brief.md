# Hukuk-AI — Post-A1.10 Stable Baseline and Router Decomposition Brief

## Karar

A1.10 sonrası **Phase 18 Recovery Baseline kabul edilmiştir**.

Live `8000`, full mevzuat corpus collection ile çalışır hale gelmiştir:

```text
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
MILVUS_ENTITY_COUNT=349191
VECTOR_DIMENSION=1024
DGX_MODEL=/models/merged_model_fabric_stage_20260321
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

A1.10 gate sonucu:

- repeatability probe: `PASS`
- directional equivalence: `PASS`
- trace drift: bounded / non-blocking
- live full hard gate: `PASS`
- green lane: `PASS`
- cutover decision: `PASS`

Bu nedenle artık Phase 18 recovery hattı kapanabilir.

Ancak:
- productization hâlâ kapalı
- fine-tuning hâlâ kapalı
- yeni retrieval / answer synthesis logic eklenmemeli
- önce monolitik `chat.py` davranış koruyarak parçalanmalı

---

## 1. A1.10’dan Çıkan Net Sonuç

### Live full run metrikleri

| Metric | Result |
|---|---:|
| raw_score_proxy | 756.61 |
| pass_proxy | 79/100 |
| wrong_family | 10 |
| wrong_document | 9 |
| hallucinated_identifier | 11 |
| unsupported_confident_claim | 0 |
| contract_valid | 100/100 |
| green_lane | pass |
| corpus_materialization_required_count | 2 |
| canonical_span_materialized_count | 98 |
| MULGA pass | 3/5 |
| YONETMELIK pass | 6/10 |
| UY pass | 10/10 |
| CB_GENELGE pass | 4/4 |

### Directional candidate/live equivalence

| Metric | Candidate | Live | Gate |
|---|---:|---:|---|
| raw_score_proxy | 766.48 | 756.61 | PASS |
| pass_proxy | 80 | 79 | PASS |
| wrong_family | 11 | 10 | PASS |
| wrong_document | 12 | 9 | PASS |
| hallucinated_identifier | 16 | 11 | PASS |

### Repeatability

Same-endpoint repeatability was exact on the 20-QID smoke set:

- candidate repeat: exact
- live repeat: exact
- selected document match: 100%
- selected article match: 100%

### Trace drift

Trace drift exists but is bounded and classified:

- retrieval ordering nondeterminism: 7 rows
- confidence/finalization drift: 4 rows

This drift does not block the accepted recovery baseline, but it must remain tracked before productization.

---

# 2. Immediate Freeze

Before refactor starts, freeze the accepted recovery baseline.

## Required actions

1. Ensure all A1.10 artifacts are committed and pushed.
2. Create a baseline marker report:

```text
reports/benchmark/phase_18_recovery_baseline.md
```

3. Record:

```text
git SHA
runtime_provenance
live collection
source catalog hash
source supplement hash
green lane result
live full run score summary
candidate/live comparison summary
```

4. Do not start new logic before baseline marker is committed.

## Acceptance

- baseline report exists
- clean or justified worktree state recorded
- live full result path recorded
- green lane path recorded
- provenance valid

---

# 3. Next Work: Behavior-Preserving `chat.py` Decomposition

## Why

`api-gateway/src/routers/chat.py` is too large and mixes too many responsibilities.

It currently acts as:

- FastAPI route
- retrieval planner
- family resolver caller
- source identity selector
- article/span selector
- source supplement handler
- answer slot builder
- answer synthesizer
- trace builder
- contract repair/finalizer
- benchmark adaptation surface

This structure caused repeated regression risk. Now that the runtime baseline is recovered, the next phase must reduce module-boundary risk before any Phase 18 slot-completion redesign resumes.

---

# 4. Refactor Rule

This is a **behavior-preserving refactor**.

Strict rules:

- no benchmark-quality logic changes
- no new retrieval heuristic
- no prompt changes
- no source routing changes
- no slot-completion redesign
- no QID-specific rules
- no fine-tuning
- no productization changes
- every extraction commit must keep tests green
- benchmark smoke after each major extraction

---

# 5. Proposed Module Split

Target modules:

```text
api-gateway/src/routers/chat.py
api-gateway/src/rag/retrieval_planning.py
api-gateway/src/rag/source_identity.py
api-gateway/src/rag/article_span_selection.py
api-gateway/src/rag/answer_slots.py
api-gateway/src/rag/answer_synthesis.py
api-gateway/src/rag/runtime_trace.py
api-gateway/src/rag/source_supplements.py
```

## Responsibilities

| Module | Responsibility |
|---|---|
| `routers/chat.py` | FastAPI route, request/response wiring only |
| `retrieval_planning.py` | query planning, family hints, intent parsing |
| `source_identity.py` | metadata lookup, source-family selection, identity rerank |
| `article_span_selection.py` | article/span/canonical materialization selection |
| `answer_slots.py` | required slot matrix and evidence-to-slot maps |
| `answer_synthesis.py` | verified-slot answer plan and final answer synthesis |
| `runtime_trace.py` | trace payload construction and provenance integration |
| `source_supplements.py` | official source supplement loading/materialization |

---

# 6. Commit Sequence

## Commit R1 — Extract Runtime Trace

Move trace construction helpers to:

```text
api-gateway/src/rag/runtime_trace.py
```

Acceptance:

- no behavior change
- existing trace fields preserved
- targeted tests pass
- 20-QID smoke no material regression

---

## Commit R2 — Extract Source Supplements

Move supplement loading/materialization to:

```text
api-gateway/src/rag/source_supplements.py
```

Acceptance:

- CB_GENELGE supplement path preserved
- CBG-01/02/03/04 smoke does not regress
- source supplement hash still reported in provenance

---

## Commit R3 — Extract Source Identity

Move metadata lookup, family selection and identity rerank helpers to:

```text
api-gateway/src/rag/source_identity.py
```

Acceptance:

- source-key v2 binding behavior preserved
- CB_GENELGE 4/4 preserved on smoke
- UY 10/10-style smoke preserved
- no source family regression on 20-QID recovery smoke

---

## Commit R4 — Extract Article / Span Selection

Move selector and canonical span materialization helpers to:

```text
api-gateway/src/rag/article_span_selection.py
```

Acceptance:

- `canonical_span_materialized_count` remains stable
- `corpus_materialization_required_count` does not increase
- selected article equality on recovery smoke does not regress

---

## Commit R5 — Extract Answer Slots

Move required slot matrix and evidence-to-slot helpers to:

```text
api-gateway/src/rag/answer_slots.py
```

Acceptance:

- answer slot trace fields preserved
- no synthesis behavior change
- contract remains 100%

---

## Commit R6 — Extract Answer Synthesis

Move verified-slot answer plan, finalization and replacement logic to:

```text
api-gateway/src/rag/answer_synthesis.py
```

Acceptance:

- unsupported confident remains low / zero on smoke
- answer modes preserved
- confidence/final_reason preserved
- no regression in 20-QID recovery smoke

---

## Commit R7 — Slim Router

After extractions, reduce `routers/chat.py` to endpoint wiring and orchestration.

Target:

```text
chat.py < 5,000 lines near-term
chat.py < 3,000 lines later target
```

Acceptance:

- endpoint integration tests pass
- 20-QID recovery smoke passes
- full benchmark comparison shows no material regression

---

# 7. Test Plan

## After each commit

Run relevant targeted tests, then:

```bash
api-gateway/.venv/bin/python -m py_compile <changed_modules>
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest <targeted_tests> -q
```

## Smoke after major extraction

Use the A1.9/A1.10 20-QID recovery smoke:

```text
CBG-01 CBG-02 CBG-03 CBG-04
MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05
CBKAR-01 CBKAR-02 CBKAR-08
YON-01 YON-02 YON-03
KANUN-01 KANUN-06 KANUN-15
TEB-01 TEB-02
```

Smoke gate:

| Metric | Minimum |
|---|---:|
| raw_score_proxy | >= 130/200 |
| pass_proxy | >= 12/20 |
| wrong_family | <= 3 |
| wrong_document | <= 5 |
| unsupported_confident_claim | <= 1 |
| contract_valid | 20/20 |
| provenance collection | full collection |

## Full benchmark after R7

Full benchmark gate:

| Metric | Minimum |
|---|---:|
| raw_score_proxy | >= 745 |
| pass_proxy | >= 77 |
| wrong_family | <= 12 |
| wrong_document | <= 12 |
| unsupported_confident_claim | <= 2 |
| contract_valid | 100/100 |
| green_lane | PASS |
| CB_GENELGE | >= 4/4 |
| UY | >= 9/10 |
| MULGA | >= 3/5 |
| YONETMELIK | >= 6/10 |

---

# 8. Test Split Plan

After code extraction, split oversized tests gradually.

Target files:

```text
api-gateway/tests/test_chat_endpoint.py
api-gateway/tests/test_retrieval_planning.py
api-gateway/tests/test_source_identity.py
api-gateway/tests/test_article_span_selection.py
api-gateway/tests/test_answer_slots.py
api-gateway/tests/test_answer_synthesis.py
api-gateway/tests/test_runtime_trace.py
api-gateway/tests/test_source_supplements.py
```

Rules:

- do not split all tests at once
- move tests with the module they cover
- keep endpoint tests small
- preserve behavior before adding new tests

---

# 9. Repo Hygiene Follow-Up

Add a non-blocking long-file check.

Thresholds:

```text
source code > 3000 lines: warn
source code > 5000 lines: refactor required
source code > 10000 lines: critical
```

Also review `.gitignore` for:

```text
logs/
logs/traces/
reports/benchmark/runs/
large raw trace json
temporary benchmark artifacts
```

Track summaries and selected CSV reports, not raw massive local artifacts unless explicitly needed.

---

# 10. After Refactor

Only after behavior-preserving decomposition passes:

1. create new stable full benchmark baseline
2. then reopen Phase 18 slot-completion redesign
3. use clean module boundaries:
   - source identity changes in `source_identity.py`
   - span changes in `article_span_selection.py`
   - slot work in `answer_slots.py`
   - synthesis in `answer_synthesis.py`

Do not reintroduce all logic into `chat.py`.

---

# 11. Fine-Tuning Gate

Still closed.

Do not open fine-tuning until:

- recovery baseline stable across at least two full runs
- router decomposition complete
- corpus/materialization blockers small
- unsupported confident near zero
- required slot completeness genuinely improves
- no major refactor in flight

---

# 12. Required Report

Produce:

```text
reports/benchmark/phase_19_router_decomposition_report.md
```

Report must include:

1. commit SHA list
2. files moved / modules created
3. behavior-preservation statement
4. tests run
5. smoke results after major extraction
6. final full benchmark delta vs A1.10 baseline
7. remaining risks
8. whether Phase 18 slot-completion redesign can resume

---

## Final Note

A1.10 recovered the live benchmark baseline.  
The system is now stable enough to refactor, not stable enough to productize.

The next goal is **structural risk reduction**, not new model behavior.
