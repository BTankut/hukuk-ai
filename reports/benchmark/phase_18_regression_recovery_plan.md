# Phase 18 Regression Recovery Plan

Date: 2026-04-25

Source brief: `reports/benchmark/hukuk_ai_phase18_regression_recovery_and_router_decomposition_brief.md`

Decision: **A1 complete / no runtime code change**. Phase 18 hardening must stop until Phase 17F-level source selection is recovered and the router decomposition plan is staged.

## 1. Baseline Freeze

Phase 17E is already committed:

- `5fe9328 Phase 17E recover CB genelge source grounding`

Phase 17F last known good benchmark state:

- commit: `d380010 Phase 17F full benchmark artifacts`
- run: `reports/benchmark/runs/20260424T212636_phase17f_full`
- green lane: `reports/benchmark/green_lane/20260424T212636_phase17f_full`
- model id: `hukuk-ai-poc`
- API URL: `http://127.0.0.1:8000/v1`
- total: `100`
- contract valid: `100/100`
- green lane: `pass`

Phase 17F key metrics:

| Metric | Value |
|---|---:|
| raw_score_proxy | 767.91 |
| pass_proxy | 77/100 |
| wrong_family | 12 |
| wrong_document | 10 |
| hallucinated_identifier | 18 |
| corpus_materialization_required_count | 2 |
| canonical_span_materialized_count | 98 |
| runtime rubric_sufficient | 88/100 |
| MULGA pass | 3/5 |
| CB_GENELGE pass | 2/4 |
| selector_exact_article_hit_rate | 0.86 |
| selected_article_equals_claimed_article_rate | 0.88 |
| selector_preferred_family_hit_rate | 0.7222 |

## 2. Regression Range

Regression range:

```text
d380010..7f18fd5
```

Phase 18 commits in range:

| Commit | Title | Initial classification |
|---|---|---|
| `8f1fad7` | Phase 18A add required slot matrix | needs ablation |
| `3c71bb7` | Phase 18B add evidence answer slots | needs ablation |
| `65a8a56` | Phase 18C calibrate claim confidence | likely safe, verify |
| `398915a` | Phase 18D synthesize answers from verified slots | risky, isolate |
| `887cc88` | Phase 18E add source materialization supplements | useful but isolate to supplements |
| `7f18fd5` | Phase 18F stabilize slot benchmark contracts | risky/must isolate |

Total runtime-relevant diff from Phase 17F to Phase 18F:

| Path | Change summary |
|---|---:|
| `api-gateway/src/routers/chat.py` | +905 / -small, highest risk |
| `api-gateway/src/answer_contract_v2.py` | +164 / confidence and contract calibration |
| `api-gateway/src/rag/required_slot_matrix.py` | new, 317 lines |
| `api-gateway/src/rag/required_slot_matrix.json` | new, 189 lines |
| `api-gateway/src/rag/source_supplements.py` | new, 195 lines |
| `api-gateway/src/rag/source_catalog.py` | source supplement/catalog changes |
| `scripts/benchmark/run_hukuk_ai_100.py` | benchmark field additions |
| `scripts/benchmark/score_hukuk_ai_100.py` | scorer/reporting additions |

The dominant risk is concentrated in `api-gateway/src/routers/chat.py`, not in the report-only changes.

## 3. Phase 18F Regression Snapshot

Phase 18F full run:

- commit: `7f18fd5 Phase 18F stabilize slot benchmark contracts`
- run: `reports/benchmark/runs/20260425T091702Z_phase18f_full`
- green lane: `reports/benchmark/green_lane/20260425T_phase18f_full`
- model id: `hukuk-ai-poc`
- API URL: `http://127.0.0.1:8000/v1`
- total: `100`
- contract valid: `100/100`
- green lane: `pass`

Phase 18F key metrics:

| Metric | Phase 17F | Phase 18F | Delta |
|---|---:|---:|---:|
| raw_score_proxy | 767.91 | 324.59 | -443.32 |
| pass_proxy | 77 | 12 | -65 |
| wrong_family | 12 | 44 | +32 |
| wrong_document | 10 | 82 | +72 |
| hallucinated_identifier | 18 | 32 | +14 |
| selector_exact_article_hit_rate | 0.86 | 0.31 | -0.55 |
| selected_article_equals_claimed_article_rate | 0.88 | 0.56 | -0.32 |
| selector_preferred_family_hit_rate | 0.7222 | 0.2857 | -0.4365 |
| CB_GENELGE pass | 2/4 | 4/4 | +2 |
| MULGA pass | 3/5 | 0/5 | -3 |
| unsupported_confident_answer_count | 8 | 0 | -8 |

Interpretation: Phase 18 improved CB_GENELGE and unsupported-confident behavior but collapsed full-set source/document selection.

## 4. Runtime / Environment Diff

Phase 17F artifacts explicitly record:

- `api_url=http://127.0.0.1:8000/v1`
- `model=hukuk-ai-poc`
- `include_trace=True`
- `contract_valid=100`

Phase 17F artifacts do **not** include a full environment snapshot. Launcher defaults near this lane indicate:

- `MILVUS_COLLECTION=mevzuat_e5_shadow`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct`
- `GUARDRAILS_ENABLED=true`
- `PRESIDIO_ENABLED=false`

Phase 18F report explicitly records:

```text
DGX_BASE_URL=http://192.168.12.243:30000/v1
DGX_MODEL=/models/merged_model_fabric_stage_20260321
MILVUS_ENABLED=true
MILVUS_URI=http://localhost:19530
MILVUS_COLLECTION=mevzuat_e5_shadow
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

Current active health check:

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"current_serving_lane","api_version":"2026-03-24-rc-h","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Current active process env confirms:

- `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `MILVUS_COLLECTION=mevzuat_e5_shadow`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `GUARDRAILS_ENABLED=false`
- `PRESIDIO_ENABLED=false`

Environment assessment:

- Collection appears consistent: `mevzuat_e5_shadow`.
- Embedding backend appears consistent: remote E5 lane.
- Guardrails differ or are at least not proven consistent: Phase 18F disabled; Phase 17F historical env not recorded, launcher defaults enabled.
- The source-selection collapse is large enough that code ablation is still required even if guardrails contributed to answer-surface differences.

## 5. Suspect Commit Classification

### Likely Safe / Keep If Ablation Confirms

`65a8a56 Phase 18C add claim confidence calibration`

- Scope: `answer_contract_v2.py`, confidence ceilings, tests, scorer fields.
- Expected source-selection effect: low.
- Benefit: lowers unsupported-confident behavior.
- Required verification: source/document metrics unchanged vs Phase 17F.

Slash-numbered identifier preservation in `7f18fd5`

- Scope: `faz2a_hardening.py`, `answer_contract_v2.py`.
- Expected source-selection effect: low.
- Benefit: preserves `2024/7`, `2019/12` circular identifiers.
- Required verification: CB_GENELGE remains improved without non-KANUN collapse.

### Useful But Must Be Isolated

`887cc88 Phase 18E add source materialization supplements`

- Benefit: CB_GENELGE recovered to 4/4 in Phase 18F.
- Risk: source supplement injection touches context/source selection path.
- Policy: keep behind narrow source-family/supplement guard; verify on full 100.

### Needs Ablation

`8f1fad7 Phase 18A add required slot matrix`

- Benefit: slot trace/reporting.
- Risk: touches `chat.py`, benchmark fields and source selection-adjacent runtime surfaces.
- Policy: ablate as reporting-only vs runtime-influencing.

`3c71bb7 Phase 18B add evidence answer slots`

- Benefit: evidence-to-slot extraction.
- Risk: touches `chat.py` and scorer fields.
- Policy: verify it does not influence retrieval/source selection.

### Risky / Revert Or Feature-Flag If Confirmed

`398915a Phase 18D synthesize answers from verified slots`

- Risk area: answer synthesis/replacement path.
- Policy: must not affect selected source; isolate behind feature flag until source selection recovers.

`7f18fd5 Phase 18F stabilize slot benchmark contracts`

- Risk areas: domain law hints, selector exact-span priority, whitelist expansion, controlled replacement, primary-slot selection changes.
- Policy: split into safe identifier/confidence fixes vs source-selection/finalization changes; ablate before keeping.

## 6. Ablation Matrix

Run all rows in the same environment. Use `mevzuat_e5_shadow`, merged DGX model, remote E5 embedding, and a documented guardrails setting. Because current guardrails are disabled for benchmark stability, first run all ablations with `GUARDRAILS_ENABLED=false`; if recovery succeeds, perform one guardrails-on parity smoke separately.

### Mini Regression Smoke

Use 20 rows:

- 4 CB_GENELGE
- 5 MULGA
- 3 CB_KARAR
- 3 YONETMELIK
- 3 KANUN
- 2 TEBLIGLER

Metrics to compare:

- raw/pass
- wrong_family
- wrong_document
- selector_exact_article_hit_rate
- selected_article_equals_claimed_article_rate
- selector_preferred_family_hit_rate
- CB_GENELGE pass
- MULGA pass
- unsupported_confident_answer_count

### Required Ablation Rows

| Label | Code state | Purpose | Expected decision |
|---|---|---|---|
| A0 | Phase 17F baseline `d380010` | confirm baseline in current env | if degraded, env/config issue exists |
| A1 | Phase 17F + CB_GENELGE supplement only | preserve CB_GENELGE gain | keep if no full-set source collapse |
| A2 | Phase 17F + confidence calibration only | preserve unsupported-confident reduction | keep if source metrics stable |
| A3 | Phase 17F + required slot matrix reporting only | verify trace/report safety | keep only if source-neutral |
| A4 | Phase 17F + evidence answer slots only | verify slot extraction safety | keep only if source-neutral |
| A5 | Phase 17F + verified-slot synthesis only | test synthesis risk | feature-flag/revert if source or answer collapse |
| A6 | Phase 17F + slash identifier fixes only | preserve CBG identifiers | keep if source-neutral |
| A7 | full Phase 18F `7f18fd5` | known failing comparator | fail expected |

Nihai karar için full 100 required after smoke narrows suspect range.

## 7. Recovery Candidate Policy

Start from Phase 17F behavior, not from Phase 18F.

Safe candidate assembly order:

1. Recreate/checkout Phase 17F baseline in a temporary worktree.
2. Apply slash-numbered identifier preservation.
3. Apply CB_GENELGE source supplement path only.
4. Apply claim confidence ceiling only.
5. Run 20-row smoke.
6. If stable, run full 100.
7. Only then consider required-slot reporting fields.

Do not include in first recovery candidate:

- verified-slot answer replacement
- broad source whitelist expansion
- selector exact-span priority changes
- domain law hint overrides
- any answer-slot logic that can affect selected source before source identity is stable

## 8. Recovery Gate

Recovery candidate must meet:

| Metric | Target |
|---|---:|
| raw_score_proxy | >=750 |
| pass_proxy | >=75 |
| wrong_family | <=15 |
| wrong_document | <=15 |
| hallucinated_identifier | <=20 |
| unsupported_confident_claim/answer | <=8 |
| corpus_materialization_required_count | <=3 |
| CB_GENELGE pass | >=2/4, preferably 4/4 |
| MULGA pass | >=3/5 |
| contract_valid | 100/100 |
| green_lane | pass |

## 9. Router Decomposition Gate

Do not add new hardening logic to `api-gateway/src/routers/chat.py`.

After recovery candidate is stable, split behavior-preserving modules in this order:

1. `api-gateway/src/rag/runtime_trace.py`
2. `api-gateway/src/rag/source_supplements.py`
3. `api-gateway/src/rag/source_identity.py`
4. `api-gateway/src/rag/article_span_selection.py`
5. `api-gateway/src/rag/answer_slots.py`
6. `api-gateway/src/rag/answer_synthesis.py`
7. slim `api-gateway/src/routers/chat.py`

Refactor rules:

- no behavior change
- no benchmark-specific fix
- no QID-specific fix
- targeted tests after each move
- full benchmark only after major split

## 10. Immediate Next Command Plan

Recommended next local actions:

```bash
# create a clean ablation worktree at Phase 17F
git worktree add ../hukuk-ai-ablation-phase17f d380010

# run baseline smoke using the same active benchmark environment
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --qids CBG-01 CBG-02 CBG-03 CBG-04 MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 CBKAR-01 CBKAR-02 CBKAR-08 YON-01 YON-02 YON-03 KANUN-01 KANUN-06 KANUN-15 TEB-01 TEB-02 \
  --out-dir reports/benchmark/runs/phase18_recovery_smoke_phase17f
```

Then apply one isolated patch at a time and repeat smoke before any full 100 run.

## 11. Current Status

- A1 baseline/config/diff report is complete.
- No runtime code was changed.
- Phase 18 remains halted.
- Fine-tuning remains closed.
