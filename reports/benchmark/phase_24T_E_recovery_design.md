# Phase 24T-E Recovery Design

Generated at UTC: `2026-05-05T11:20:59Z`  
Git HEAD before E commit: `392f4b1e0865f5247438c7214931c54fdc720927`

## Diagnostic Inputs

```text
Phase23R-E good baseline = 816.86 / 91
Phase24R BASE trace-off = 725.40 / 72
Phase24S CBY live trace-off = 727.18 / 73
Phase24T-D current base trace-on = 805.09 / 89
```

Phase24T-A/B/C show that Phase24R/S low full scores are not provenance-equivalent to Phase23R-E because Phase23R-E used `include_trace=True` while Phase24R/S used `include_trace=False`. The scorer depends on trace-derived selected document/source-key fields; trace-off runs produced empty selected-source fields and inflated wrong-document/hallucinated-identifier failures.

Phase24T-D shows trace-on current base recovers most of the loss but still does not reproduce Phase23R-E exactly.

## Selected Design Path

Use a combined Option A + Option B path.

### Option A — Runtime/scorer provenance issue

Status: `SELECTED_FIRST`

Action:

```text
Normalize benchmark command/provenance before any CBY decision.
Require include_trace=True for full matched A/B score gates, or explicitly mark trace-off runs as contract-only/non-score-comparable.
Rerun BASE and CBY matched full on non-live candidate ports with identical trace-on runner/scorer/config.
Do not change live 8000.
```

Acceptance for the next phase:

```text
BASE trace-on matched full reproduces current live trace-on result within deterministic tolerance.
CBY trace-on matched full differs from BASE only in intended CBY rows or proves otherwise.
All score comparisons cite include_trace, git_sha, source_supplement_hash, scorer_hash, and collection.
```

### Option B — Code/source supplement drift since Phase23R-E

Status: `SELECTED_SECOND`

Reason:

```text
Phase24T-D current trace-on = 805.09 / 89
Phase23R-E trace-on = 816.86 / 91
remaining_gap = -11.77 raw / -2 pass
```

Likely narrow audit surface:

```text
source_supplement_hash changed: a301cdd8... -> 282503e9...
changed file: api-gateway/src/rag/source_supplements.py
key commit in ancestry: ddcadd2 Execute Phase 24O shadow residual remediation
new behavior: dynamic Phase24N source supplements enabled by default through ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=true
```

Next audit should isolate this without altering live:

```text
Run non-live candidate A/B:
A = current code, ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=true
B = current code, ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=false
both trace-on, base collection, same model/top_k/scorer
compare only remaining drift rows: MULGA-04, KANUN-08, KANUN-02, YON-05, YON-08 plus improved rows KANUN-12/YON-04
```

### Option C — Collection binding / candidate runtime issue

Status: `NOT_PRIMARY`

Reason: Phase24R BASE and Phase24T-D both use the base collection. The large 725/72 collapse is explained by trace-off scoring non-equivalence, not by proven collection binding mismatch. CBY still needs matched trace-on A/B before any merge.

### Option D — Source identity logic regression

Status: `DEFERRED_UNTIL_TRACE_ON_ABLATION`

Reason: Phase24T-C did not prove source identity selection regression because Phase24R selected document/source-key fields were absent due trace-off. If the Phase24N supplement ablation still leaves the remaining gap, open systemic source/document identity code audit.

### Option E — Stop CBY merge line

Status: `TEMPORARY_HOLD`

Reason: CBY-06 candidate evidence is useful, but CBY cannot be promoted until score-comparable trace-on matched full A/B passes and the remaining Phase23R-E drift is explained.

## Non-Negotiable Controls

```text
live_8000_change = forbidden
productization = closed
internal_eval = closed
fine_tuning = closed
qid_specific_runtime_branch = forbidden
answer_key_driven_patch = forbidden
prompt/model/top_k_change = forbidden
```

## Next Recommended Phase

```text
Phase24U — Trace-Normalized Matched A/B and Source Supplement Drift Isolation
```

Minimum work:

1. Start non-live BASE/CBY candidate ports with the same model and collection bindings used in Phase24R.
2. Run matched full benchmark with `include_trace=True` for BASE and CBY.
3. Run base-collection ablation with `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=false` on a non-live port.
4. Attribute remaining drift rows before any code change.
5. Only after Phase23R-E-level trace-on score is recovered, revisit CBY merge/cutover.

## Decision

```text
recovery_design = OptionA_then_OptionB
implementation_in_phase24T = none
```
