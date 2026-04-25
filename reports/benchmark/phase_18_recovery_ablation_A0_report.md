# Phase 18 Recovery Ablation A0 Report

Date: 2026-04-25

Purpose: Test whether Phase 17F code recovers Phase 17F behavior under the current runtime environment.

## Setup

Baseline code:

- worktree: `../hukuk-ai-ablation-phase17f`
- commit: `d380010 Phase 17F full benchmark artifacts`

Runtime:

- port: `8017`
- `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `MILVUS_ENABLED=true`
- `MILVUS_URI=http://localhost:19530`
- `MILVUS_COLLECTION=mevzuat_e5_shadow`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `GUARDRAILS_ENABLED=false`
- `PRESIDIO_ENABLED=false`

Health:

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"current_serving_lane","api_version":"2026-03-24-rc-h","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Milvus startup log:

```text
Milvus health OK: collection=mevzuat_e5_shadow entities=12923
```

Smoke qids:

```text
CBG-01 CBG-02 CBG-03 CBG-04
MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05
CBKAR-01 CBKAR-02 CBKAR-08
YON-01 YON-02 YON-03
KANUN-01 KANUN-06 KANUN-15
TEB-01 TEB-02
```

Run artifact:

- `reports/benchmark/runs/20260425T_phase18_recovery_A0_phase17f_smoke20`

Note: benchmark run artifacts are ignored by `.gitignore`; this report records the relevant summary.

## Commands

```bash
git worktree add ../hukuk-ai-ablation-phase17f d380010

cd ../hukuk-ai-ablation-phase17f/api-gateway
DGX_BASE_URL=http://192.168.12.243:30000/v1 \
DGX_MODEL=/models/merged_model_fabric_stage_20260321 \
MILVUS_ENABLED=true \
MILVUS_URI=http://localhost:19530 \
MILVUS_COLLECTION=mevzuat_e5_shadow \
EMBEDDING_BACKEND=remote \
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1 \
GUARDRAILS_ENABLED=false \
PRESIDIO_ENABLED=false \
/Users/btmacstudio/Projects/hukuk-ai/api-gateway/.venv/bin/python \
  -m uvicorn src.main:app --host 127.0.0.1 --port 8017 --log-level info

cd /Users/btmacstudio/Projects/hukuk-ai
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8017/v1 \
  --model hukuk-ai-poc \
  --qids CBG-01 CBG-02 CBG-03 CBG-04 MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 CBKAR-01 CBKAR-02 CBKAR-08 YON-01 YON-02 YON-03 KANUN-01 KANUN-06 KANUN-15 TEB-01 TEB-02 \
  --out-dir reports/benchmark/runs/20260425T_phase18_recovery_A0_phase17f_smoke20 \
  --timeout 180 --retries 1 --sleep 0.1

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260425T_phase18_recovery_A0_phase17f_smoke20/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260425T_phase18_recovery_A0_phase17f_smoke20
```

## Result

| Metric | A0 Phase 17F code in current env |
|---|---:|
| total | 20 |
| raw_score_proxy | 88.77 / 200 |
| pass_proxy | 6/20 |
| fail_proxy | 14/20 |
| wrong_family | 7 |
| wrong_document | 12 |
| hallucinated_identifier | 4 |
| unsupported_confident_answer_count | 0 |
| corpus_materialization_required_count | 0 |
| canonical_span_materialized_count | 15 |
| selector_exact_article_hit_rate | 0.35 |
| selected_article_equals_claimed_article_rate | 0.70 |
| selector_preferred_family_hit_rate | 1.0 |

Family result:

| Family | Count | Pass | Avg score |
|---|---:|---:|---:|
| CB_GENELGE | 4 | 4 | 9.03 |
| KANUN | 3 | 2 | 6.94 |
| CB_KARAR | 3 | 0 | 3.83 |
| TEBLIGLER | 2 | 0 | 2.73 |
| YONETMELIK | 3 | 0 | 2.00 |
| MULGA | 5 | 0 | 1.78 |

## Comparison To Phase 18F Same 20 QIDs

The same qids extracted from `reports/benchmark/runs/20260425T091702Z_phase18f_full/scored.csv` produce the same aggregate metrics:

| Metric | A0 Phase 17F code | Phase 18F same qids |
|---|---:|---:|
| raw_score_proxy | 88.77 | 88.77 |
| pass_proxy | 6/20 | 6/20 |
| wrong_family | 7 | 7 |
| wrong_document | 12 | 12 |
| hallucinated_identifier | 4 | 4 |
| CB_GENELGE pass | 4/4 | 4/4 |
| MULGA pass | 0/5 | 0/5 |
| canonical_span_materialized_count | 15 | 15 |

## Scorer Drift Check

The original Phase 17F candidate answers were re-scored with the current scorer:

- input: `reports/benchmark/runs/20260424T212636_phase17f_full/candidate_answers.csv`
- output: `reports/benchmark/runs/20260425T_phase18_recovery_phase17f_original_rescore`

Full 100 re-score result:

| Metric | Original Phase 17F re-score |
|---|---:|
| raw_score_proxy | 767.91 |
| pass_proxy | 77/100 |
| wrong_family | 12 |
| wrong_document | 10 |
| hallucinated_identifier | 18 |
| selector_exact_article_hit_rate | 0.86 |
| selected_article_equals_claimed_article_rate | 0.88 |
| selector_preferred_family_hit_rate | 0.7222 |
| corpus_materialization_required_count | 2 |
| canonical_span_materialized_count | 98 |

Same 20-qid subset comparison:

| Metric | Original Phase 17F answers | A0 Phase 17F code current env | Phase 18F same qids |
|---|---:|---:|---:|
| raw_score_proxy | 141.18 | 88.77 | 88.77 |
| pass_proxy | 14/20 | 6/20 | 6/20 |
| wrong_family | 1 | 7 | 7 |
| wrong_document | 3 | 12 | 12 |
| hallucinated_identifier | 3 | 4 | 4 |
| CB_GENELGE pass | 2/4 | 4/4 | 4/4 |
| MULGA pass | 3/5 | 0/5 | 0/5 |
| CB_KARAR pass | 2/3 | 0/3 | 0/3 |
| YONETMELIK pass | 2/3 | 0/3 | 0/3 |
| TEBLIGLER pass | 2/2 | 0/2 | 0/2 |

Representative selected-document drift:

| QID | Original Phase 17F selected document | A0 current-env selected document |
|---|---|---|
| `MULGA-02` | `GÜVENLİK SORUŞTURMASI,BAZI NEDENLERLE GÖREVLERİNE SON VERİLEN...` | `HUKUK MUHAKEMELERİ KANUNU` |
| `CBKAR-01` | `İTHALAT REJİMİ KARARINA EK KARAR (KARAR SAYISI: 1362)` | empty / no selected document |
| `YON-01` | `İŞYERİ HEKİMİ VE DİĞER SAĞLIK PERSONELİNİN GÖREV...` | empty / no selected document |
| `KANUN-01` | `İŞ KANUNU` | `HUKUK MUHAKEMELERİ KANUNU` |
| `TEB-01` | `KAMU İHALE GENEL TEBLİĞİ` | empty / no selected document |

## Interpretation

A0 did **not** recover Phase 17F behavior under the current runtime environment. The Phase 17F code produced the same 20-row aggregate result as the Phase 18F full-run subset.

The current scorer re-scores the original Phase 17F candidate answers back to the published Phase 17F score. Therefore this is **not scorer drift**.

This means the regression cannot be attributed only to Phase 18 code changes on this smoke set. The leading hypothesis is now current runtime/data/index/catalog drift. At least one of the following must be investigated before cherry-pick ablations are meaningful:

- runtime data/index state drift in `mevzuat_e5_shadow`
- source catalog / canonical metadata state drift
- guardrails/runtime mode difference
- current active model or retrieval service state difference

The strongest immediate clue is that the current Phase 17F code path still selects `kanun` pre-filter pools for several `MULGA`, `YONETMELIK`, `TEBLIGLER`, and `CB_KARAR` rows. This matches the Phase 18F failure surface.

## Decision

Do not proceed directly to Phase 18 cherry-pick ablations yet.

Next required step is an **environment/data parity audit**:

1. Compare Phase 17F original run trace/candidate rows against A0 current-env rows for the same 20 qids.
2. Compare selected source ids, pre-filter family sets, canonical source keys and metadata lookup lanes.
3. Verify whether `mevzuat_e5_shadow` row count/content/source-key bindings changed after Phase 17F.
4. Verify source catalog inputs loaded by the gateway under Phase 17F code in the current worktree.
5. Only after parity is understood, resume isolated Phase 18 safe-patch ablations.

## Runtime Cleanup

The temporary gateway on port `8017` was stopped after the run.
