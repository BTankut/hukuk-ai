# Hukuk-AI — Phase 19 R3–R7 Router Decomposition Continuation Brief

## Karar

Phase 19 doğru yönde ilerliyor.

R1 ve R2 **kabul edilebilir**:

- R1: runtime trace extraction tamamlandı.
- R2: source supplement extraction tamamlandı.
- Her iki adımda da davranış değiştiren retrieval / source selection / synthesis logic eklenmedi.
- A1.10 recovery baseline korunmuş görünüyor.
- CB_GENELGE supplement path R2 smoke’ta `4/4` geçti.
- 20-QID recovery smoke R1 sonrası kabul edilebilir seviyede kaldı.

Ancak devam etmeden önce önemli bir ayrım yapılmalı:

`test_chat_router.py` içindeki 7 broad-router failure, R1 extraction regression gibi görünmüyor. Bunlar eski beklentiler / geniş kapsamlı test borcu / önceki sistem değişiklikleriyle uyumsuz beklentiler gibi duruyor.

Bu nedenle R3’e geçmeden önce kısa bir **test expectation triage** yapılmalı. Bu triage refactor’u durdurmamalı ama test borcunu görünür hale getirmeli.

---

## 1. R1 / R2 Sonuç Özeti

### R1 — Runtime Trace Extraction

Durum: `complete`

Dosyalar:

- `api-gateway/src/rag/runtime_trace.py`
- `api-gateway/src/routers/chat.py`

Kabul gerekçesi:

- trace payload helpers ayrıldı
- `routers.chat` import uyumluluğu korunmuş
- parity trace testleri geçti
- kabul edilen 20-QID smoke:
  - `answered = 20/20`
  - `errors = 0`
  - `contract_valid = 20/20`
  - `unsupported_confident_answer = 0`
  - `raw_score_proxy = 140.23 / 200`
  - `pass_proxy = 15/20`
  - full collection provenance doğru

### R2 — Source Supplement Extraction

Durum: `complete`

Dosyalar:

- `api-gateway/src/rag/source_supplements.py`
- `api-gateway/src/routers/chat.py`

Kabul gerekçesi:

- supplement materialization ayrıldı
- CB_GENELGE supplement path korundu
- focused tests geçti
- CBG smoke:
  - `answered = 4/4`
  - `contract_valid = 4/4`
  - `pass_proxy = 4/4`
  - family/document/article match `4/4`
  - unsupported confident `0`

---

## 2. Test Debt Triage — R3 Öncesi Mini Adım

## Amaç

R1/R2 sonrası görülen 7 broad-router failure’ın gerçek regression mı, eski beklenti mi, yoksa refactor sırasında korunması gereken behavior mı olduğunu sınıflamak.

## Raporlanan failure tipleri

R1 raporunda broad-router failures:

- source family prior confidence expected below `0.75`, actual `0.88`
- native dialog answer includes verified answer plan suffix
- bazı retrieval tests eski retriever call count bekliyor
- trace whitelist expectation later-expanded source aliases ile uyumsuz

## Yapılacaklar

Her failure için şu sınıflandırma yapılmalı:

```text
failure_id
test_name
expected_old_behavior
actual_behavior
is_regression: true/false
category:
  - stale_test_expectation
  - behavior_intentionally_changed_before_phase19
  - real_refactor_regression
  - broad_test_too_coupled
  - requires_new_focused_test
decision:
  - update_test
  - keep_xfail_temporarily
  - fix_code
  - split_test
```

## Acceptance

- Rapor üret:
  - `reports/benchmark/phase_19_test_expectation_triage.md`
- R1/R2 extraction regression olmadığı netleşmeli.
- Gerçek regression varsa R3’e geçmeden düzeltilmeli.
- Stale expectation ise test güncelleme veya split planına eklenmeli.

## Commit

### Commit T1
- test expectation triage report
- no runtime behavior change
- optional focused test updates only if clearly stale

---

# 3. R3 — Extract Source Identity Helpers

## Amaç

Metadata lookup, source-family selection, identity rerank ve source-key binding helper’larını `chat.py` dışına almak.

## Hedef modül

```text
api-gateway/src/rag/source_identity.py
```

## Taşınacak sorumluluklar

- metadata-first source lookup
- source-family candidate scoring
- family gate status helpers
- selected source identity scoring
- source-key v2 binding helpers
- canonical source key / legacy alias handling
- document identity rerank helpers
- source lock / selected source retention helpers

## Kesin kurallar

- behavior change yok
- retrieval score ağırlıkları değişmeyecek
- family boundary rule eklenmeyecek
- source-key logic değişmeyecek
- QID-specific hiçbir şey eklenmeyecek
- `routers.chat` import compatibility shim geçici olarak korunabilir

## Testler

Focused tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest   api-gateway/tests/test_chat_router.py   -k "source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate" -q
```

Smoke:

- 20-QID recovery smoke
- CB_GENELGE 4-QID smoke
- UY / KKY / YON boundary mini smoke önerilir

## Acceptance

- CB_GENELGE `4/4` korunmalı
- 20-QID smoke:
  - `raw_score_proxy >= 130/200`
  - `pass_proxy >= 12/20`
  - `wrong_family <= 3`
  - `wrong_document <= 5`
  - `contract_valid = 20/20`
- source-key v2 collision `0` kalmalı
- live full collection provenance korunmalı

## Commit

### Commit R3
- source identity extraction
- focused tests
- smoke report

---

# 4. R4 — Extract Article / Span Selection

## Amaç

Article/span selector ve canonical materialization helper’larını `chat.py` dışına almak.

## Hedef modül

```text
api-gateway/src/rag/article_span_selection.py
```

## Taşınacak sorumluluklar

- `_select_article_span_evidence(...)` benzeri selector logic
- selected main span selection
- supporting span selection
- canonical span materialization checks
- title-only fallback classification
- candidate completeness scoring
- article-zero/body-span helpers
- span noise suppression helpers

## Kurallar

- selector behavior değişmeyecek
- yeni span heuristic eklenmeyecek
- body/materialization logic değiştirilmeyecek
- title-only policy değişmeyecek

## Testler

Focused tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest   api-gateway/tests/test_chat_router.py   -k "article_span_selector or selected_document_only_bundle or canonical_span_materialization or title_only or candidate_completeness" -q
```

Smoke:

- 20-QID recovery smoke
- CBKAR-08 / KANUN-06 materialization mini smoke
- KKY-09 / YON-07 selector smoke

## Acceptance

- `canonical_span_materialized_count` smoke seviyesinde düşmemeli
- `corpus_materialization_required_count` artmamalı
- selected article identity regresyonu olmamalı
- unsupported confident artmamalı

## Commit

### Commit R4
- article/span selection extraction
- focused tests
- smoke report

---

# 5. R5 — Extract Answer Slot Helpers

## Amaç

Required slot matrix ve evidence-to-slot helper’larını ayrı modüle almak.

## Hedef modül

```text
api-gateway/src/rag/answer_slots.py
```

## Taşınacak sorumluluklar

- required slot matrix lookup
- task/family slot resolver
- evidence-to-slot trace builder
- missing slot reason helpers
- runtime rubric sufficient helpers
- slot coverage calculations

## Kurallar

- slot matrix içerik değişmeyecek
- slot coverage scoring değişmeyecek
- answer synthesis değişmeyecek
- sadece taşıma yapılacak

## Testler

Focused tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest   api-gateway/tests/test_chat_router.py   -k "required_slot or answer_slot or evidence_slot or slot_coverage" -q
```

## Acceptance

- answer slot trace fields korunmalı
- contract validity korunmalı
- runtime rubric sufficient smoke’da beklenmeyen gerileme göstermemeli

## Commit

### Commit R5
- answer slot helper extraction
- focused tests
- smoke report

---

# 6. R6 — Extract Answer Synthesis Helpers

## Amaç

Verified-slot answer plan, finalization ve replacement logic’i ayrı modüle almak.

## Hedef modül

```text
api-gateway/src/rag/answer_synthesis.py
```

## Taşınacak sorumluluklar

- verified answer plan builder
- final answer replacement / suppression helpers
- confidence/final_reason shaping
- answer mode selection helpers
- insufficient evidence response shaping
- controlled verified-slot answer replacement

## Kurallar

- answer text behavior değiştirilmemeli
- confidence policy değiştirilmemeli
- replacement thresholds değiştirilmemeli
- prompt değişikliği yok

## Testler

Focused tests:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest   api-gateway/tests/test_answer_contract_v2.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest   api-gateway/tests/test_chat_router.py   -k "verified_answer_slot_plan or completeness_synthesis or final_reason or insufficient_evidence or confidence" -q
```

## Acceptance

- unsupported confident smoke’da `0` veya baseline seviyesinde kalmalı
- answer contract invalid olmamalı
- confidence/final_reason korunmalı
- 20-QID recovery smoke geçmeli

## Commit

### Commit R6
- answer synthesis extraction
- focused tests
- smoke report

---

# 7. R7 — Slim Router

## Amaç

`api-gateway/src/routers/chat.py` dosyasını route wiring ve orchestrasyon katmanına indirmek.

## Hedef

Near-term:

```text
chat.py < 5,000 lines
```

Later target:

```text
chat.py < 3,000 lines
```

## Yapılacaklar

- artık taşınmış helper kodlarını kaldır
- route handler’ı küçük orchestration akışı olarak bırak
- import compatibility shim’leri mümkünse temizle
- endpoint integration tests’i küçük bir test dosyasına ayırmaya başla

## Testler

- endpoint integration tests
- 20-QID recovery smoke
- full benchmark
- green lane

## Full benchmark gate

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

## Commit

### Commit R7
- slim router
- integration tests
- full benchmark report

---

# 8. Test Split Plan

Refactor ilerledikçe testler de bölünmeli.

Yeni hedef test dosyaları:

```text
api-gateway/tests/test_chat_endpoint.py
api-gateway/tests/test_runtime_trace.py
api-gateway/tests/test_source_supplements.py
api-gateway/tests/test_source_identity.py
api-gateway/tests/test_article_span_selection.py
api-gateway/tests/test_answer_slots.py
api-gateway/tests/test_answer_synthesis.py
```

Kurallar:

- testleri tek seferde bölme
- modül çıkarıldıkça ilgili testleri taşı
- eski broad-router testleri temizlenene kadar focused testleri önceliklendir
- stale expectation testlerini güncelle veya ayrı rapora bağla

---

# 9. Large File / Artifact Hygiene

Raporun devamında şunlar da ele alınmalı:

- `chat.py` satır sayısı
- `test_chat_router.py` satır sayısı
- tracked / untracked büyük artifactler
- logs/traces ignore durumu

Önerilen non-blocking check:

```text
source code > 3000 lines: warn
source code > 5000 lines: refactor required
source code > 10000 lines: critical
```

---

# 10. Phase 18 Slot-Completion Redesign Ne Zaman Açılır?

Sadece şu koşullardan sonra:

- R3-R7 tamam
- `chat.py` ciddi şekilde küçüldü
- full benchmark behavior-preserving gate geçti
- source selection baseline stabil
- trace/provenance çalışıyor
- productization ve fine-tuning hâlâ kapalı

Sonra Phase 18 slot-completion tekrar açılabilir ama modül bazlı:

- slot işi: `answer_slots.py`
- synthesis işi: `answer_synthesis.py`
- source identity işi: `source_identity.py`
- span işi: `article_span_selection.py`

---

# 11. Nihai Rapor

Kod asistanı sonunda şu raporu üretmeli:

```text
reports/benchmark/phase_19_router_decomposition_final_report.md
```

İçerik:

1. commit SHA listesi
2. oluşturulan modüller
3. `chat.py` before/after line count
4. test split durumu
5. stale broad-router test triage sonucu
6. smoke sonuçları
7. final full benchmark delta vs A1.10 baseline
8. green lane sonucu
9. kalan riskler
10. Phase 18 slot-completion redesign’a geçilebilir mi?

---

## Final Note

R1/R2 başarılı.  
Şimdi refactor’un en riskli kısmı başlıyor: source identity ve span selection extraction.

Bu süreçte kalite iyileştirme yapma.  
Amaç sadece davranışı koruyarak modül sınırlarını düzeltmek.
