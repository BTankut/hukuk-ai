# Phase 17C Evidence-To-Answer Required Slot Synthesis Report

Tarih: 2026-04-24

## Scope

Phase 17C iki parçaya ayrıldı.

- Commit 3: `b6ffb1f Phase 17C add evidence required slot schema`
- Commit 4: final cevap yüzeyine evidence slot synthesis, benchmark export/scorer alanları ve audit artefact üretimi

Bu çalışma soru odaklı özel kural eklemez. Değişiklikler genel required-slot şeması, seçilmiş evidence span'lerden slot çıkarımı, slot görünürlük synthesis'i ve slot seçim kalitesi üzerindedir.

## Implemented

- `api-gateway/src/routers/chat.py`
  - Evidence required slot değerleri final answer contract ve trace içine taşındı.
  - Final cevapta eksik veya görünmeyen güvenli slotlar, seçilmiş evidence span id'siyle birlikte bounded şekilde append edilir.
  - `procedure_or_consequence` slot seçiminde `sure` / `süreli` yanlış eşleşmesi engellendi.
  - Slot excerpt seçimi ilk eşleşmeye değil en yüksek hint skoruna göre yapılır.
  - `governing_source`, `exact_source_identity`, `document_selection_reason` slotları selector primary chunk'a bağlandı; adjacent chunk kimlik kayması azaltıldı.
  - Synthesis trace alanları eklendi:
    - `evidence_slot_synthesis_applied`
    - `evidence_slot_synthesis_slots`
    - `evidence_slot_synthesis_reason`
- `api-gateway/tests/test_chat_router.py`
  - Evidence slot synthesis ve procedure slot seçim regresyonları eklendi.
- `scripts/benchmark/run_hukuk_ai_100.py`
  - Runtime output'a evidence slot synthesis alanları eklendi.
- `scripts/benchmark/score_hukuk_ai_100.py`
  - Scored output ve summary'ye synthesis alanları eklendi.
- `scripts/benchmark/phase17_evidence_slot_audit.py`
  - `candidate_answers.csv` ve `scored.csv` üzerinden Phase 17C slot audit CSV/MD üretimi eklendi.

## Verification

Geçen kontroller:

- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py scripts/benchmark/phase17_evidence_slot_audit.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "completeness_synthesis or answer_slot_synthesis_hint or evidence_slot_synthesis or procedure_slot"`
  - Sonuç: `14 passed`

Tam `api-gateway/tests/test_chat_router.py` koşusunda 5 failure görüldü. Bunlar bu Phase 17C değişikliğinin doğrudan regression'ı olarak sınıflandırılmadı:

- `test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate`
  - Beklenen confidence `<0.75`, mevcut değer `0.88`.
  - İlgili dosya `source_family_resolver.py` zaten ayrı dirty durumda.
- Dört retrieval call-count testi eski exact çağrı sayısına bağlı:
  - `test_law_filter_passed_to_retriever`
  - `test_explicit_article_refs_are_force_included`
  - `test_cross_law_questions_trigger_per_law_candidate_generation`
  - `test_concept_anchor_rules_force_include_exact_articles`
  - Mevcut retrieval expansion daha fazla çağrı üretiyor; davranışsal correctness yerine brittle call-count assert'leri etkileniyor.

## Runtime Smoke

Run:

- `reports/benchmark/runs/20260424T_phase17c_slot_synthesis_smoke_v2`
- QID set: `KANUN-01,KANUN-04,CBK-01,CBK-06,CBKAR-01,CBY-02,KHK-05,TUZUK-05,YON-04,MULGA-01`

Özet:

- `raw_score_proxy`: `71.52 / 100`
- `pass_proxy`: `7/10`
- `minimum_answer_facts_present_count`: `7/10`
- `evidence_slot_synthesis_count`: `9/10`
- `contract_valid`: `10/10`
- `unsupported_confident_answer`: `0`
- `canonical_missing_required_content_signal`: `10/10`
- `canonical_partial_grounding_only`: `10/10`

Audit:

- `reports/benchmark/phase_17c_evidence_slot_audit_v2.md`
- `reports/benchmark/phase_17c_evidence_slot_audit_v2.csv`

Before/after smoke delta:

- First 10-row Phase 17C smoke: `70.19 / 100`, synthesis `0/10`
- Current smoke v2: `71.52 / 100`, synthesis `9/10`
- Delta: `+1.33` raw score, visible slot synthesis active

Targeted KANUN-01 verify:

- Run: `reports/benchmark/runs/20260424T_phase17c_slot_synthesis_single_verify_v3`
- Audit: `reports/benchmark/phase_17c_evidence_slot_single_verify_v3.md`
- `score_0_10_proxy`: `9.10`
- `pass_proxy`: `1/1`
- Synthesized slots:
  - `governing_source`
  - `procedure_or_consequence`
  - `temporal_validity`
  - `current_applicability`
- Identity slot now binds to `İŞ KANUNU | IK m.18 | kanun | IK m.18/f.0`
- Procedure slot now binds to `IK m.20/f.0`

## Gate Result

Phase 17C is partially successful but not accepted against the full Phase 17C gate.

Met:

- Required-slot schema exists.
- Evidence-to-slot extraction exists.
- Final answer synthesis from selected evidence exists.
- Benchmark/scorer/report fields exist.
- Focused regression tests pass.
- Visible slot synthesis is active in runtime smoke.
- Unsupported confident answer count did not increase in smoke.

Not met:

- `missing_required_content_signal <= 92` cannot be proven from the 10-row smoke; smoke remains `10/10`.
- `partial_grounding_only <= 92` cannot be proven from the 10-row smoke; smoke remains `10/10`.
- Runtime completeness improved locally but the smoke still shows evidence coverage/selection insufficiency in hard rows.

## Diagnosis

Phase 17C fixed the answer-surface visibility layer, but remaining failures are not primarily caused by hidden slot values anymore.

Current blockers:

- Some rows select the wrong document/family before synthesis. Example: `KANUN-04` has wrong family/document, so slot synthesis can only make wrong evidence more visible.
- Some rows have correct primary identity but insufficient multi-span bundle coverage. Example: `KANUN-01` now surfaces `IK m.18` and `IK m.20`, but must-include coverage remains `2/6`; the answer needs a selected source bundle that carries all required scenario facts, not only one slot per class.
- `MULGA` and `CB_GENELGE` still need their dedicated Phase 17D/17E family templates and body/span handling.

## Next Step

Proceed to Phase 17D only after committing this Phase 17C closure state. The next effective work is not more answer formatting; it is family-specific evidence bundle completeness:

- MULGA historical/current/replacement slots
- CB_GENELGE circular body span model
- Multi-span answer bundle assembly for rows where one selected span cannot satisfy all required facts
