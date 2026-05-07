# Phase 24HT Same-Family Source Identity Final Report

## Commit SHA List

- `4c967dd` Audit and design Phase 24HT same-family candidates
- `6b494de` Prototype Phase 24HT same-family domain scoring
- `934471d` Record Phase 24HT focused smoke and recovery decision

## KANUN-08 Candidate Audit

Audit report:

- `reports/benchmark/phase_24HT_A_kanun08_same_family_candidate_audit.md`
- `reports/benchmark/phase_24HT_A_kanun08_same_family_candidate_audit.csv`

Result:

- Phase24HS selected `TÜRK BORÇLAR KANUNU / TBK m.255`.
- Source identity already ranked `TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18` first.
- TBK won later because article selector used `selected_source_lock` on `tbk m.1`.
- Therefore the blocker was same-family document arbitration after source identity, not absence of the TKHK candidate.

## Same-Family Domain Compatibility Design

Design report:

- `reports/benchmark/phase_24HT_B_same_family_domain_compatibility_design.md`

Implemented feature flag:

- `ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true`

Rule summary:

- explicit law/article references remain authoritative;
- no QID-specific logic;
- no benchmark answer key;
- no model, prompt, or top-k change;
- source identity may override a weaker same-family selected-source lock only when dual-lane source identity is strong and same-family compatible.

## Prototype

Prototype report:

- `reports/benchmark/phase_24HT_C_non_live_prototype_report.md`

Changed files:

- `api-gateway/src/rag/article_span_selection.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/tests/test_chat_router.py`

Targeted unit tests:

- `3 passed, 326 deselected`

Full `test_chat_router.py` run:

- `319 passed, 10 failed`
- representative failures also fail in isolation, so they are tracked as existing repository test debt, not Phase24HT-specific failures.

## Focused Smoke Result

Smoke report:

- `reports/benchmark/phase_24HT_D_focused_non_live_smoke_report.md`

Run dir:

- `reports/benchmark/runs/phase_24HT_focused_non_live_candidate_smoke`

Safety counters:

- contract valid: `13/13`
- answer contract invalid: `0`
- unsupported confident answer: `0`
- source_key_v2 collision: `0`
- binding collision: `0`

KANUN-08:

- Phase24HS: `3.25 FAIL`, selected `TÜRK BORÇLAR KANUNU / TBK m.255`
- Phase24HT: `3.93 FAIL`, selected `TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18`
- selector reason: `same_family_domain_identity_lock`
- source identity margin over TBK: `42.0305`

Guard rows:

- `TEB-04`, `TUZUK-05`, `YON-05`, `MULGA-01`, `MULGA-05`, `TEB-06`, `KANUN-12`, `YON-04`, `CBG-01`, `CBKAR-08` stayed stable versus Phase24HS v6.
- `CBY-06` and `TUZUK-04` remained unchanged pre-existing focused residuals.

## Full Candidate Result

Full candidate was not run.

Report:

- `reports/benchmark/phase_24HT_E_full_candidate_not_run.md`

Reason:

- focused smoke was safety-clean and KANUN-08 document identity improved;
- KANUN-08 still failed, so full benchmark would measure a known incomplete candidate.

## Recovery Decision

Decision report:

- `reports/benchmark/phase_24HT_F_recovery_decision.md`

Decision:

- Option B: same-family scoring improves but candidate remains insufficient.

Residual:

- KANUN-08 now exposes a source-role/secondary-family recall issue.
- `pre_filter_family_set=["kanun"]` prevents the secondary `YONETMELIK` evidence path from reliably entering the selected pool.
- Answer slots still select an unrelated TBK supporting span for the exception slot instead of the distance-sales/custom-production exception evidence.

## Productization Decision

No productization.

## Internal Eval Decision

No internal eval.

## Fine-Tuning Decision

No fine-tuning.

## Final Live 8000 State

Live `8000` was not modified.

Final health:

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Candidate `8042` was stopped after focused smoke.

## Next Recommended Phase

Open a targeted KANUN-08 source-role retrieval and secondary-family recall phase:

- keep Phase24HT as non-live diagnostic candidate behavior;
- recover `secondary_types=YONETMELIK` routing without QID-specific logic;
- represent primary KANUN and supporting YONETMELIK roles separately in trace;
- prevent answer-slot extraction from filling exception slots with unrelated same-family/private-law spans.
