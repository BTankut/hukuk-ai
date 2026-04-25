# Hukuk-AI — Phase 18 Regression Recovery + Router Decomposition Task Brief

## Amaç

Bu doküman kod asistanına verilecek güncel görev brifidir.

Dış uzman değerlendirmesi, Phase 17E CB_GENELGE recovery raporu, Phase 18 full report ve repo large-file audit birlikte değerlendirildi. Karar net:

1. **Phase 18 mevcut haliyle devam ettirilmemeli.**
2. **Phase 17F stabil davranış geri kazanılmalı.**
3. **Phase 18’den yalnız güvenli kazanımlar cherry-pick edilmeli.**
4. **`api-gateway/src/routers/chat.py` davranış koruyarak parçalanmalı.**
5. **Fine-tuning hâlâ kapalı kalmalı.**

Yeni retrieval, slot-completion veya synthesis mantığı eklenmeden önce regression recovery ve modülerleşme yapılacak.

---

# 1. Neden Bu Müdahale Gerekli?

## 1.1 Phase 17F güçlü baseline idi

Phase 17F sonucu:

- `raw_score_proxy = 767.91`
- `pass_proxy = 77/100`
- `wrong_family = 12`
- `wrong_document = 10`
- `hallucinated_identifier = 18`
- `corpus_materialization_required_count = 2`
- `canonical_span_materialized_count = 98`
- `runtime rubric_sufficient = 88/100`
- `MULGA pass = 3/5`
- `CB_GENELGE pass = 2/4`
- source-key v2 runtime binding active on `100/100`
- v2 collision and binding collision both `0`

Bu seviye, Phase 18’e geçiş için yeterliydi fakat productization/fine-tuning için hâlâ yeterli değildi.

## 1.2 Phase 18 ciddi regresyon üretti

Phase 18F full run:

- `raw_score_proxy = 324.59`
- `pass_proxy = 12/100`
- `wrong_family = 44`
- `wrong_document = 82`
- `selector_exact_article_hit_rate = 0.31`
- `selected_article_equals_claimed_article_rate = 0.56`
- `selector_preferred_family_hit_rate = 0.2857`
- `missing_required_content_signal = 100`
- `partial_grounding_only = 100`

Bu, normal başarısız faz değil; full-set source-selection collapse anlamına gelir. Phase 18 raporu da target gate sonucunu `3/13`, kararını `FAIL / gate closed` olarak veriyor.

## 1.3 Phase 18 içinde değerli parçalar var

Phase 18 tamamen çöpe atılmamalı. Faydalı parçalar:

- `CB_GENELGE = 4/4 pass`
- `unsupported_confident_answer_count = 0`
- confidence consistency yüksek
- slash-numbered identifiers korunuyor
- `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04` tarafında anlamlı iyileşme var
- CB_GENELGE document-level body supplement/template path çalışıyor

Ancak bu kazanımlar full-set source-selection regresyonu yüzünden doğrudan merge/promote edilmemeli.

## 1.4 Repo yapısal riski büyümüş durumda

Large-file audit sonucu:

- `api-gateway/src/routers/chat.py` yaklaşık `14,514` satır
- `312` function
- `6` class
- endpoint, retrieval planning, source selection, answer synthesis, trace, finalizer ve benchmark adaptasyonları aynı dosyada
- en büyük fonksiyonlardan biri `chat_completions(...)`, yaklaşık `1,463` satır
- `_select_article_span_evidence(...)`, `_rerank_chunks_by_source_identity(...)`, `_build_trace_payload(...)`, `_finalize_chat_response(...)` gibi büyük runtime fonksiyonları aynı dosyada

Bu dosya artık modül-boundary failure durumunda. Yeni benchmark hardening logic’i doğrudan buraya eklemek regresyon riskini artırıyor.

---

# 2. Ana Strateji

## Kısa karar

- Phase 18 doğrudan devam etmeyecek.
- Phase 18’den yalnız güvenli ve izole edilebilir kazanımlar cherry-pick edilecek.
- Phase 17F veya en yakın stabil commit baseline alınacak.
- Phase 18 regresyonu izole edilmeden slot-completion geliştirmesi sürmeyecek.
- `chat.py` davranış koruyarak bölünecek.
- Fine-tuning kapalı kalacak.

---

# 3. Immediate Halt Rules

Aşağıdakiler durdurulsun:

- `chat.py` içine yeni hardening logic ekleme
- yeni prompt tightening
- yeni dense top-k tuning
- yeni QID-specific veya benchmark-specific fix
- Phase 18 slot-completion logic’ini doğrudan genişletme
- fine-tuning hazırlığı
- productization gate tartışması

Önce regression recovery.

---

# 4. Track A — Phase 18 Regression Recovery

## Amaç

Phase 17F seviyesindeki full benchmark davranışını geri kazanmak ve Phase 18’deki faydalı parçaları güvenli şekilde ayrıştırmak.

---

## A1 — Baseline Freeze

### Yapılacaklar

- Phase 17F son iyi commit/run seti belirle.
- Phase 18 branch state ile Phase 17F baseline arasındaki diff’i çıkar.
- Phase 18 commitlerini modül/modül sınıflandır:
  - safe / likely safe
  - risky
  - must revert
  - needs isolation
- Phase 18 runtime environment farklarını kaydet:
  - Milvus collection
  - guardrails on/off
  - embedding backend
  - model path
  - environment variables
  - source supplement settings

### Özellikle kontrol et

Phase 18 report’ta runtime şu şekilde koşmuş:

```text
MILVUS_COLLECTION=mevzuat_e5_shadow
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

Önceki Phase 17F ile aynı collection/config mi kullanıldı?
Eğer değilse skor düşüşünün bir kısmı code değil environment/config kaynaklı olabilir.

### Acceptance

- Phase 17F baseline commit/run açık.
- Phase 18F regression commit aralığı açık.
- Config/env diff raporu var.

### Commit / Push

#### Commit A1
- baseline/config diff report
- no runtime code change

---

## A2 — Regression Bisect / Ablation Matrix

### Amaç

Phase 18’de hangi değişikliğin full-set routing/source-selection collapse ürettiğini bulmak.

### Koşulacak ablation setleri

Aşağıdaki kombinasyonlar mümkünse aynı environment ile koşulsun:

1. Phase 17F baseline
2. Phase 17F + CB_GENELGE supplement only
3. Phase 17F + confidence calibration only
4. Phase 17F + required slot matrix only
5. Phase 17F + answer-slot extraction only
6. Phase 17F + verified-slot synthesis only
7. Full Phase 18

### Mini smoke öncesi

Full 100 pahalıysa önce 20-row regression smoke oluştur:

- 4 CB_GENELGE
- 5 MULGA
- 3 CB_KARAR
- 3 YONETMELIK
- 3 KANUN
- 2 TEBLIGLER

Ama nihai karar için full 100 gerekir.

### Acceptance

- Regresyonun ana kaynağı tespit edildi.
- `wrong_document=82` ve `wrong_family=44` artışına neden olan değişiklik/konfig izole edildi.
- CB_GENELGE kazanımını koruyan minimum safe patch belirlendi.

### Commit / Push

#### Commit A2
- ablation report
- regression attribution table

---

## A3 — Safe Cherry-Pick Policy

### Phase 18’den korunabilecek muhtemel parçalar

Aşağıdakiler ancak ablation’da güvenliyse korunmalı:

- slash-numbered identifier preservation
- CB_GENELGE source supplement path
- CB_GENELGE document-level template
- confidence ceiling policy
- unsupported-confident audit/reporting
- slot trace fields, eğer source selection’ı etkilemiyorsa

### Geri alınması gerekebilecek parçalar

Aşağıdakiler regresyon ürettiyse revert veya feature-flag arkasına alınmalı:

- verified-slot replacement logic
- answer synthesis replacement path
- source whitelist expansion
- selector exact-span priority changes
- hardening/finalization path içinde source-selection etkileyen logic
- any code path that changes selected source before retrieval/source identity stabilizes

### Acceptance

- Phase 17F-level source selection geri geldi.
- CB_GENELGE kazanımı mümkünse korundu.
- `unsupported_confident_answer_count` düşük kaldı.
- Full benchmark raw/pass Phase 17F’ye yakın veya daha iyi.

---

## A4 — Recovery Full Run

### Hedef

Recovery candidate şu seviyeye dönmeli:

| Metric | Target |
|---|---:|
| raw_score_proxy | `>=750` |
| pass_proxy | `>=75` |
| wrong_family | `<=15` |
| wrong_document | `<=15` |
| hallucinated_identifier | `<=20` |
| unsupported_confident_claim | `<=8` |
| corpus_materialization_required_count | `<=3` |
| CB_GENELGE pass | `>=2/4`, preferably `4/4` |
| MULGA pass | `>=3/5` |
| contract_valid | `100/100` |
| green_lane | `pass` |

### Commit / Push

#### Commit A3
- recovered runtime patch
- phase_18_recovery_summary.md
- full benchmark artifacts

---

# 5. Track B — Behavior-Preserving `chat.py` Decomposition

Bu track, Track A recovery sonrası veya recovery ile paralel ama **davranış değiştirmeden** yapılmalı. Yeni kalite logic ekleme.

## Amaç

`api-gateway/src/routers/chat.py` dosyasını küçük, test edilebilir modüllere ayırmak.

## Neden?

`chat.py` artık 14K+ satırlık mixed runtime surface. Yeni logic eklemek regression riskini çok yükseltiyor.

---

## B1 — Module Split Plan

Önerilen modüller:

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

### Sorumluluklar

| Module | Responsibility |
|---|---|
| `routers/chat.py` | FastAPI endpoint, request/response wiring only |
| `retrieval_planning.py` | query planning, legal hints, family priors |
| `source_identity.py` | metadata lookup, source-family selection, identity rerank |
| `article_span_selection.py` | article/span/canonical materialization selection |
| `answer_slots.py` | required slot matrix, evidence-to-slot maps |
| `answer_synthesis.py` | verified-slot answer plan and final answer |
| `runtime_trace.py` | trace payload construction |
| `source_supplements.py` | official source supplement loading/materialization |

---

## B2 — Refactor Rules

- İlk split davranış koruyucu olacak.
- No benchmark logic change.
- No new retrieval heuristic.
- No QID-specific rule.
- Her taşıma küçük commit.
- Import compatibility shim gerekirse kullanılabilir.
- Her commit sonrası targeted tests.
- Full benchmark sadece major split bittikten sonra.

---

## B3 — Suggested Commit Sequence

### Commit B1
- Extract `runtime_trace.py`
- Move trace payload builders
- Tests green

### Commit B2
- Extract `source_supplements.py`
- Move supplement materialization code
- Tests green

### Commit B3
- Extract `source_identity.py`
- Move metadata lookup, source-family selection, identity rerank
- Tests green

### Commit B4
- Extract `article_span_selection.py`
- Move selector and span materialization
- Tests green

### Commit B5
- Extract `answer_slots.py`
- Move required slot matrix and slot extraction helpers
- Tests green

### Commit B6
- Extract `answer_synthesis.py`
- Move final answer plan / synthesis / replacement logic
- Tests green

### Commit B7
- Slim `routers/chat.py`
- Keep endpoint integration tests
- Run smoke

---

## B4 — Test Split

Current `api-gateway/tests/test_chat_router.py` is also too large.

After code split, test files should map to modules:

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

Do not split all tests before code split. Split incrementally.

---

# 6. Repo Hygiene / Large Artifact Policy

## Immediate

- Add/tighten `.gitignore` for:
  - `logs/`
  - `logs/traces/`
  - local massive trace JSON
  - temporary benchmark run artifacts not intended for commit

## Policy

- Track markdown summaries and selected CSV summaries.
- Avoid committing huge raw JSON reports unless explicitly needed.
- Old large eval JSON should move to ignored artifact storage, compressed archive, or Git LFS.
- Primary source legal text can remain if intentionally part of corpus fixtures.

## CI

Add a non-blocking long-file check first:

```text
source code > 3000 lines: warn
source code > 5000 lines: refactor required
source code > 10000 lines: critical
```

Do not fail CI initially; report only.

---

# 7. Track C — Phase 18 Redesign After Recovery

Once Track A recovery and Track B decomposition are stable, Phase 18 can be redesigned.

## Core Principle

Do not let answer-slot/synthesis logic affect source selection unless explicitly intended and tested.

## Phase 18 Redesign Scope

### C1 — Required Slot Matrix

Use slot matrix as reporting/extraction layer first, not source-selection driver.

### C2 — Evidence-to-Slot Extraction

Slots must be bound to evidence spans.

### C3 — Claim-Level Confidence

Confidence should degrade based on missing critical slots.

### C4 — Verified-Slot Synthesis

Only after A/B confirms it does not alter selected source.

### C5 — Human/Judge Calibration

If `missing_required_content_signal` remains high despite good slot coverage, run 20–30 QID human/judge audit of slot mapping.

---

# 8. Acceptance Gates

## Recovery Gate

Before new hardening:

- raw score back to `>=750`
- pass `>=75`
- wrong_document `<=15`
- wrong_family `<=15`
- green lane pass
- contract valid 100/100
- no massive regression in UY, KKY, KHK, TUZUK

## Refactor Gate

Before adding new logic after split:

- targeted tests pass
- endpoint smoke pass
- Phase 17F-equivalent smoke pass
- full benchmark no material regression
- `chat.py` below 3000 lines target eventually, below 5000 as near-term threshold

## Phase 18 Reopen Gate

Phase 18 redesign can resume only if:

- recovery stable
- source selection stable
- v2 source-key binding stable
- `chat.py` split at least into source_identity / span_selection / synthesis modules

---

# 9. Fine-Tuning Gate

Fine-tuning remains closed.

Do not open until:

- retrieval/source identity stable across two full reruns
- corpus materialization blockers tiny
- unsupported confident near zero
- required slot completeness validated
- no major module-boundary refactor in flight

If any training is considered before then, prefer:

1. cross-encoder reranker training
2. source resolver/entity parser training
3. span selector training
4. slot extractor calibration

LLM answer fine-tuning is last.

---

# 10. Immediate To-Do for Code Assistant

## Step 1

Commit/push Phase 17E if not already committed.

## Step 2

Do **not** continue Phase 18 logic directly.

## Step 3

Create `phase_18_regression_recovery_plan.md` with:

- Phase 17F baseline
- Phase 18F regression
- environment/config diff
- suspect commits
- ablation matrix

## Step 4

Run recovery ablations.

## Step 5

Prepare safe recovered candidate.

## Step 6

After recovery candidate is green, start behavior-preserving `chat.py` decomposition.

---

## Final Note

The expert review confirms the strategic direction, but Phase 18 implementation produced a serious regression. The answer is not to add more hardening on top. The correct move is:

1. recover stable Phase 17F behavior,
2. isolate the useful Phase 18 improvements,
3. split the monolithic router,
4. then reintroduce slot-completion behind clean module boundaries.

This is the safest path to avoid repeatedly rediscovering the same failures.
