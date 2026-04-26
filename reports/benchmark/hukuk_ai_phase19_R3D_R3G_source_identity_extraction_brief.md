# Hukuk-AI — Phase 19 R3D–R3G Source Identity Extraction Brief

## Karar

Phase 19 doğru yönde ilerliyor.

R1, R2, T1, R3A, R3B ve R3C **kabul edilebilir**.

Özellikle R3A/R3B/R3C için en önemli güvenlik sinyali şu:

- 20-QID recovery smoke her üç adımda da aynı kaldı:
  - `raw_score_proxy = 140.23 / 200`
  - `pass_proxy = 15/20`
  - `contract_valid = 20/20`
  - `unsupported_confident_answer = 0`
  - `source_key_v2_collision_detected_count = 0`
  - `canonical_key_binding_applied_count = 20`
- Bu, source identity primitive extraction’ın davranış koruyucu olduğunu gösteriyor.

Ancak full R3 hâlâ tamamlanmadı. En riskli parçalar hâlâ `routers/chat.py` içinde:

- metadata-first catalog lookup
- source-key v2 binding
- identity rerank body
- family gate helpers
- source lock / selected source retention

Bunlar extraction sırasında retrieval/source-selection davranışını kolayca bozabilir. Bu yüzden R3D+ kontrollü alt parçalara bölünmeli.

---

## 1. Mevcut Durum Özeti

Tamamlananlar:

| Step | Status | Not |
|---|---|---|
| R1 | complete | runtime trace extraction |
| R2 | complete | source supplement extraction |
| T1 | complete | broad-router test expectation triage |
| R3A | complete | source-family identity primitives |
| R3B | complete | chunk source-family profile primitives |
| R3C | complete | identity match primitives |

T1 kararı geçerli kalmalı:

- `test_chat_router.py` full suite şu an refactor gate değildir.
- Bilinen 7 broad-router failure stale expectation / broad coupling kapsamındadır.
- Focused tests + smoke gate kullanılmalıdır.
- Known stale test: `test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate`
  - expected `<0.75`
  - actual `0.88`
  - runtime behavior zayıflatılmamalı.

---

# 2. R3D — Metadata-First Catalog Lookup Extraction

## Amaç

Metadata-first catalog lookup helper’larını `source_identity.py` içine taşımak.

## Taşınacak Sorumluluklar

- metadata lookup candidate construction
- normalized title / alias lookup helpers
- identifier-driven metadata candidate lookup
- source catalog candidate filtering
- source supplement-aware metadata candidate visibility
- metadata lookup trace value builders

## Taşınmaması Gerekenler

Şimdilik şu parçalar yerinde kalsın:

- final identity rerank scoring body
- selected-source retention
- source-lock final arbitration
- source-key v2 binding final application

## Kurallar

- lookup output order değişmemeli
- candidate filtering değişmemeli
- source supplement path değişmemeli
- no new family rules
- no QID-specific rule
- no prompt/synthesis change

## Focused Tests

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "metadata_first_selector or source_supplement or slash_numbered or source_catalog" -q
```

Known stale testleri hariç tutmak gerekirse explicit `and not ...` filtresiyle çalıştır.

## Smoke

- 20-QID recovery smoke
- CB_GENELGE 4-QID smoke
- metadata-heavy mini smoke:
  - `CBG-01`
  - `CBG-02`
  - `CBKAR-01`
  - `CBKAR-08`
  - `TEB-01`
  - `TEB-03`

## Acceptance

- 20-QID smoke:
  - `raw_score_proxy >= 130/200`
  - `pass_proxy >= 12/20`
  - `wrong_family <= 3`
  - `wrong_document <= 5`
  - `contract_valid = 20/20`
- CB_GENELGE 4/4 korunmalı
- source supplement provenance korunmalı
- metadata candidate order materially değişmemeli

## Commit

### Commit R3D
- metadata-first catalog lookup extraction
- focused tests
- smoke report

---

# 3. R3E — Source-Key v2 Binding Extraction

## Amaç

Source-key v2 binding helper’larını `source_identity.py` içine almak.

Bu adım yüksek risklidir çünkü A1.10 baseline’ın ana garantilerinden biri source-key v2 binding’in 100/100 aktif olmasıdır.

## Taşınacak Sorumluluklar

- canonical source key v2 construction / normalization helpers
- legacy source-key alias handling
- binding source key selection
- binding collision detection helpers
- canonical key applied trace helpers
- source-key v2 compatibility wrappers

## Kurallar

- v2 key schema değişmeyecek
- binding priority değişmeyecek
- legacy alias behavior değişmeyecek
- collision policy değişmeyecek
- selected source logic değişmeyecek

## Focused Tests

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "source_key_v2 or canonical_key_binding or source_key_collision or legacy_and_canonical_source_keys" -q
```

## Smoke

- 20-QID recovery smoke
- source-key collision watch:
  - `CBKAR-08`
  - `CBG-04`
  - `TEB-03`
  - `KANUN-19`

## Acceptance

- `source_key_v2_collision_detected_count = 0`
- `binding_source_key_collision_detected_count = 0`
- `canonical_key_binding_applied_count = 20` on 20-QID smoke
- CBKAR-08 / CBG-04 source-key behavior preserved
- no regression in selected document

## Commit

### Commit R3E
- source-key v2 binding helper extraction
- focused tests
- smoke report

---

# 4. R3F — Identity Rerank Body Extraction

## Amaç

Source identity rerank body’sini `source_identity.py` içine almak.

Bu R3 içindeki en riskli adımdır. Çünkü document selection ve family scoring doğrudan etkilenebilir.

## Taşınacak Sorumluluklar

- `_rerank_chunks_by_source_identity(...)` body
- document identity scoring helpers
- title / identifier / issuer / year match classification
- identity lock strength helpers
- metadata-selected source preference logic
- selected source cluster scoring

## Kurallar

- rerank weights değişmeyecek
- tie-break değişmeyecek
- candidate ordering değişmeyecek
- scoring thresholds değişmeyecek
- no new heuristic
- no cleanup refactor beyond extraction

## Pre-Extraction Requirement

R3F öncesi mevcut function için snapshot-style regression fixture üret:

```text
reports/benchmark/phase_19_R3F_identity_rerank_fixture.md
```

En az şu QID veya source cluster örnekleri üzerinden before/after input-output karşılaştır:

- `CBG-01`
- `CBKAR-01`
- `CBKAR-08`
- `MULGA-02`
- `YON-01`
- `TEB-01`
- `KANUN-01`
- `UY-07`

## Focused Tests

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "source_identity_reranker or selected_source_cluster or metadata_selected_source or title_match or identifier_match" -q
```

## Smoke

- 20-QID recovery smoke
- YONETMELIK boundary smoke:
  - `YON-01`
  - `YON-02`
  - `YON-03`
  - `YON-05`
- MULGA smoke:
  - all 5 MULGA rows
- Strong-family guard smoke:
  - `UY-07`
  - `UY-08`
  - `KKY-10`

## Acceptance

- 20-QID smoke no material regression:
  - `raw_score_proxy >= 130/200`
  - `pass_proxy >= 12/20`
  - `wrong_family <= 3`
  - `wrong_document <= 5`
- `CB_GENELGE 4/4` preserved
- `MULGA >= 3/5` on targeted smoke if full smoke set used
- `UY` guard preserved
- selected document match rate vs previous R3C/R3E smoke >= 90%

## Commit

### Commit R3F
- identity rerank body extraction
- rerank fixture report
- focused tests
- smoke report

---

# 5. R3G — Family Gate and Selected-Source Retention Extraction

## Amaç

Family gate helpers, selected-source retention, source-lock finalization helpers’ı `source_identity.py` içine taşımak.

Bu adım source selection final behavior’a dokunduğu için yüksek risklidir.

## Taşınacak Sorumluluklar

- family gate status helper functions
- preferred family pool logic wrappers
- selected source retention helpers
- source-lock key matching helpers
- primary vs supporting source retention utilities
- source claim normalization helpers, sadece source identity ile ilgili olanlar

## Taşınmaması Gerekenler

- final answer synthesis
- answer contract repair
- confidence policy
- text generation prompt logic

## Tests

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_chat_router.py \
  -k "family_gate or preferred_family or selected_source_retention or source_lock or primary_source" -q
```

## Smoke

- 20-QID recovery smoke
- KANUN primary/supporting arbitration smoke:
  - `KANUN-03`
  - `KANUN-04`
  - `KANUN-09`
  - `KANUN-19`
- YONETMELIK boundary smoke
- CB_GENELGE smoke

## Acceptance

- 20-QID recovery smoke passes baseline gate
- supporting source does not overwrite primary source
- family gate statuses materially unchanged
- no increase in wrong family
- no increase in wrong document

## Commit

### Commit R3G
- family gate and selected-source retention extraction
- focused tests
- smoke report

---

# 6. R3 Completion Gate

After R3D–R3G complete, run:

## 20-QID recovery smoke

Same QID set as A1.10.

Minimum:

| Metric | Minimum |
|---|---:|
| raw_score_proxy | >= 130/200 |
| pass_proxy | >= 12/20 |
| wrong_family | <= 3 |
| wrong_document | <= 5 |
| unsupported_confident_claim | <= 1 |
| contract_valid | 20/20 |
| source_key_v2_collision | 0 |
| binding_source_key_collision | 0 |

## Focused family smokes

- CB_GENELGE 4/4
- MULGA >= 3/5
- YONETMELIK >= 6/10, if full family smoke is run
- UY strong-family smoke preserved

## Report

Produce:

```text
reports/benchmark/phase_19_R3_source_identity_extraction_report.md
```

Report must include:

1. R3A–R3G commit list
2. moved functions/classes
3. remaining source identity code still in `chat.py`
4. test results
5. smoke deltas
6. known stale tests
7. decision whether R4 may proceed

---

# 7. R4 Prep — Article / Span Selection Extraction

R4 should **not** start until R3 completion gate passes.

R4 target module:

```text
api-gateway/src/rag/article_span_selection.py
```

Pre-R4 required inventory:

- list all article/span selector functions still in `chat.py`
- identify dependencies on:
  - source identity
  - temporal helpers
  - answer slot helpers
  - trace helpers
- create fixture for selector input/output on:
  - `CBKAR-08`
  - `KANUN-06`
  - `KKY-09`
  - `YON-07`
  - `TEB-01`

---

# 8. Stop Rules

Stop and report immediately if any extraction causes:

- `wrong_family` +2 or more on 20-QID smoke
- `wrong_document` +2 or more on 20-QID smoke
- `CB_GENELGE` drops below 4/4
- `source_key_v2_collision_detected_count > 0`
- `binding_source_key_collision_detected_count > 0`
- `contract_valid` below 100%
- gateway errors/refusals
- provenance missing

No broad refactor should continue past a failed stop rule.

---

## Final Note

R3A/R3B/R3C were safe because they extracted primitives without moving final selection behavior.

R3D–R3G move progressively closer to final source selection.  
Therefore the extraction must become more conservative, fixture-backed, and smoke-gated.

Do not optimize. Do not clean up logic. Do not improve behavior.

Only move code and prove behavior stayed equivalent.
