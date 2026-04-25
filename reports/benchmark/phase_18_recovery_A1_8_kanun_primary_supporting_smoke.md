# Phase 18 Recovery A1.8-D — KANUN Primary / Supporting Source Smoke

Date: 2026-04-25

Decision: Step D accepted on candidate runtime only. Live `8000` was not changed.

## Runtime Provenance

- API URL: `http://127.0.0.1:8018/v1`
- Model: `hukuk-ai-poc`
- DGX upstream: `http://192.168.12.243:30000/v1`
- DGX model: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Milvus entities at startup: `349191`
- Embedding backend: `remote`
- Embedding URL: `http://127.0.0.1:8081/v1`
- Guardrails: `disabled`
- Presidio: `disabled`

## Systemic Changes

- Added domain-law routing for `HUAK` / `6325` civil mandatory mediation questions.
- Tightened rent-increase routing so generic rent mediation questions no longer lock to `TBK m.344`.
- Preserved 6356 collective-labor mediation context by excluding `toplu iş sözleşmesi`, `grev`, `lokavt`, `görevli makam`, and `uyuşmazlık yazısı` from HUAK routing.
- Extended KANUN primary/supporting arbitration for domain-law source bridges, including active/repealed alias arbitration and supporting regulation/source surfacing.
- No QID-specific behavior patch was added.

## Verification Commands

```bash
cd api-gateway
.venv/bin/python -m py_compile src/routers/chat.py src/source_family_resolver.py
.venv/bin/python -m pytest tests/test_chat_router.py -k "civil_mediation or rent_mediation or domain_law_supporting or source_family_prior_keeps_current_answer" -q
```

```bash
RUN_DIR=reports/benchmark/runs/20260425T_phase18_recovery_A1_8_kanun21_smoke_final_v3
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8018/v1 \
  --model hukuk-ai-poc \
  --qids KANUN-01 KANUN-02 KANUN-03 KANUN-04 KANUN-05 KANUN-06 KANUN-07 KANUN-08 KANUN-09 KANUN-10 KANUN-11 KANUN-12 KANUN-13 KANUN-14 KANUN-15 KANUN-16 KANUN-17 KANUN-18 KANUN-19 KANUN-20 KANUN-21 \
  --top-k 20 \
  --max-tokens 1200 \
  --timeout 180 \
  --out-dir "$RUN_DIR" \
  --allow-missing-trace
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers "$RUN_DIR/candidate_answers.csv" \
  --out-dir "$RUN_DIR"
```

## Results

6-row final smoke:

- Run: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_kanun_smoke_v12_final`
- Result: `6/6 PASS`
- Raw score: `48.65/60`
- Wrong family: `0`
- Wrong document: `0`
- Hallucinated source: `0`
- Unsupported confident answer: `0`

21-row KANUN smoke:

- Run: `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_kanun21_smoke_final_v3`
- Result: `21/21 PASS`
- Raw score: `174.37/210`
- Average score: `8.30`
- Contract invalid: `0`
- Wrong family proxy: `0`
- Hallucinated source: `0`
- Unsupported confident answer: `0`
- Canonical span materialized: `21/21`

Targeted trace checks:

- `KANUN-02`: primary `İŞ KANUNU`, article `41`; supporting source includes `6249 m.1/f.0`, `6249 m.6/f.0`, `6249 m.4/f.0`; answer surface now includes `6249` / `Fazla Çalışma` signal.
- `KANUN-19`: primary `TEBLİGAT KANUNU`; supporting source includes `29033` Elektronik Tebligat Yönetmeliği; no active answer over repealed-title/mülga wording leak.
- `KANUN-21`: primary `HUKUK UYUŞMAZLIKLARINDA ARABULUCULUK KANUNU`; article `6325 m.18`; prior `6356` and `TBK m.344` drifts are removed.

Ignored run:

- `reports/benchmark/runs/20260425T_phase18_recovery_A1_8_kanun21_smoke_final` is invalid because the zsh scalar QID list was not split and the runner executed `0` questions.

## Residual Risks

- Deterministic scorer still classifies all 21 KANUN rows as `structurally_full_but_legally_misaligned` with `missing_required_content_signal | partial_grounding_only`; this is a scoring/answer-synthesis depth signal, not a family/document blocker for Step D.
- `KANUN-21` remains `document_match_score=0.5` because the rubric expects the broader `6325 + 7445` chain; primary source identity is now correct and `6325 m.18` is locked.

## Step D Status

Accepted. Proceed to A1.8-E strong-family regression guard before any full rerun or cutover decision.
