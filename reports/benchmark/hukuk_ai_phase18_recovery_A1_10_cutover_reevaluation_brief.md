# Hukuk-AI — Phase 18 Recovery A1.10 Cutover Re-Evaluation Brief

## Karar

A1.9 rollback prosedürel olarak doğruydu; çünkü mevcut A1.9 brief mutlak candidate/live equivalence şartı koymuştu.

Ancak A1.9 raporları birlikte değerlendirildiğinde teknik sonuç şudur:

- Live `8000` full collection ile **hard quality gate’i geçti**.
- Rollback yalnızca candidate/live equivalence gate’inde `wrong_document` mutlak delta `3 > 2` olduğu için yapıldı.
- Bu delta kalite açısından kötüleşme değil, iyileşme yönündeydi:
  - Candidate `wrong_document = 12`
  - Live `wrong_document = 9`
- Live full run ayrıca:
  - `raw_score_proxy = 756.61`
  - `pass_proxy = 79/100`
  - `wrong_family = 10`
  - `unsupported_confident_claim = 0`
  - `contract_valid = 100/100`
  - `green_lane = pass`

Bu yüzden sıradaki iş yeni remediation değil.  
Sıradaki iş **candidate/live nondeterminism ve equivalence policy düzeltmesi** olmalı.

---

## 1. A1.9’dan Çıkan Net Sonuç

### Live hard gate geçti

Live full `8000` full collection run şu metriklerle geçti:

| Metric | Live Result | Gate | Status |
|---|---:|---:|---|
| raw_score_proxy | 756.61 | >=735 | PASS |
| pass_proxy | 79/100 | >=73 | PASS |
| wrong_family | 10 | <=15 | PASS |
| wrong_document | 9 | <=15 | PASS |
| hallucinated_identifier | 11 | <=23 | PASS |
| unsupported_confident_claim | 0 | <=8 | PASS |
| contract_valid | 100/100 | 100/100 | PASS |
| green_lane | pass | PASS | PASS |
| corpus_materialization_required_count | 2 | <=6 | PASS |
| canonical_span_materialized_count | 98 | >=90 | PASS |
| YONETMELIK pass | 6/10 | >=6/10 | PASS |
| MULGA pass | 3/5 | >=3/5 | PASS |

### Candidate/live equivalence fail nedeni

A1.9 equivalence:

| Metric | Candidate | Live | Abs Delta | Tolerance | Status |
|---|---:|---:|---:|---:|---|
| raw_score_proxy | 766.48 | 756.61 | 9.87 | <=10 | PASS |
| pass_proxy | 80 | 79 | 1 | <=2 | PASS |
| wrong_family | 11 | 10 | 1 | <=2 | PASS |
| wrong_document | 12 | 9 | 3 | <=2 | FAIL |

Bu fail, kalite düşüşü değil; live tarafında `wrong_document` iyileşmesi nedeniyle oluştu. Ancak row-level PASS/FAIL drift de var. Bu yüzden doğrudan “cutover tamam” demek de doğru değil.

---

## 2. Ana Teknik Teşhis

A1.9 iki şey gösteriyor:

1. **Full collection live’da çalışıyor ve kalite gate’i geçiyor.**
2. **Candidate/live davranışı tam deterministik değil.**

Bu nondeterminism şunlardan kaynaklanabilir:

- candidate ve live run farklı git SHA / dirty worktree ile koşuldu
- generation sampling parametreleri sabit değil
- upstream LLM nondeterministic
- retrieval top-k ordering tie-break deterministic değil
- Milvus sonuç sıralaması eşit skor/tie durumunda değişiyor
- concurrent gateway state / warm cache farkı
- source supplement veya catalog hash aynı görünse de runtime load order farklı
- candidate ve live arasında environment veya config mikro farkları var
- live run candidate’dan sonra farklı process lifecycle / cache ile koşuldu

---

# Phase 18 Recovery A1.10 — Cutover Re-Evaluation

## Amaç

Live full collection cutover’ın gerçekten güvenli olup olmadığını tekrar değerlendirmek.

Bu faz remediation yapmayacak.  
Bu faz **determinism / repeatability / equivalence policy** fazıdır.

---

## A1.10-A — Clean Commit and Provenance Lock

## Yapılacaklar

A1.9 raporlarında `dirty_worktree=True` görünüyor. Bu kabul edilebilir değil.

Önce:

```bash
git status
git diff --stat
git add <intended files>
git commit -m "benchmark: phase 18 recovery A1.9 cutover validation artifacts"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

Sonra candidate/live rerun’larda hedef:

```text
dirty_worktree=false
same git_sha
same source_catalog_py_sha256
same source_supplements_py_sha256
same MILVUS_COLLECTION
same DGX_MODEL
same EMBEDDING endpoint
same benchmark runner version
same scorer version
```

## Acceptance

- Yeni A1.10 run’larda `dirty_worktree=false` veya dirty state açıkça gerekçelendirilmiş olmalı.
- Candidate ve live aynı git SHA’dan çalışmalı.
- Runtime provenance eksiksiz olmalı.

---

## A1.10-B — Determinism Probe

## Amaç

Aynı endpoint, aynı config, aynı collection ile iki ardışık run ne kadar oynuyor?

## Koşulacaklar

### Candidate repeat probe

Candidate `8018` full collection ile aynı 20-QID smoke iki kez koş:

```text
A1.10_candidate_smoke20_r1
A1.10_candidate_smoke20_r2
```

### Live repeat probe

Live `8000` full collection geçici olarak açıldığında aynı 20-QID smoke iki kez koş:

```text
A1.10_live_smoke20_r1
A1.10_live_smoke20_r2
```

Karşılaştır:

- raw_score
- pass
- wrong_family
- wrong_document
- selected_document_id per QID
- selected_article per QID
- claimed source per QID
- top retrieved candidates per QID
- answer mode / confidence

## Acceptance

Eğer aynı endpoint üzerinde iki run arasında ciddi drift varsa sorun candidate/live farkı değil, genel nondeterminism’dir.

Ölçüm:

```text
same_endpoint_pass_delta <= 1
same_endpoint_wrong_document_delta <= 1
same_endpoint_selected_document_match_rate >= 90%
```

---

## A1.10-C — Candidate/Live Directional Equivalence Policy

## Problem

A1.9 eski policy mutlak fark kullanıyordu:

```text
abs(candidate_wrong_document - live_wrong_document) <= 2
```

Bu, live tarafında kalite iyileştiğinde bile fail üretiyor.

## Yeni policy önerisi

Candidate/live equivalence ikiye ayrılmalı:

### 1. Hard quality gate

Live tek başına şu eşiği geçmeli:

```text
raw_score >= 735
pass >= 73
wrong_family <= 15
wrong_document <= 15
unsupported_confident_claim <= 8
contract_valid = 100/100
green_lane = pass
```

### 2. Adverse delta gate

Live, candidate’a göre ciddi kötüleşmemeli:

```text
raw_score_delta >= -10
pass_delta >= -2
wrong_family_delta <= +2
wrong_document_delta <= +2
hallucinated_identifier_delta <= +3
```

Burada negatif/pozitif yön önemli:

- `wrong_document 12 -> 9` **PASS** sayılmalı.
- `wrong_document 12 -> 15` tolerance içinde olabilir.
- `wrong_document 12 -> 16` fail olmalı.

### 3. Row-level drift warning

Row-level PASS/FAIL flip olursa raporlanmalı ama hard fail yalnız şu durumda olmalı:

```text
candidate_pass_live_fail_count > candidate_fail_live_pass_count + 3
```

veya kritik watch QID’lerde regresyon varsa:

```text
CB_GENELGE pass drops below 4/4
MULGA pass drops below 3/5
UY drops below 9/10
YONETMELIK drops below 6/10
```

## Acceptance

- Policy güncellenmeli.
- A1.9 run bu yeni directional policy ile yeniden yorumlanmalı.
- Eğer A1.9 yeni policy ile pass ediyorsa live cutover tekrar denenebilir.

---

## A1.10-D — Trace Ordering Diff

A1.9 row drift için şu QID’ler incelensin:

Candidate PASS, live FAIL:

- `CBY-01`
- `CBY-06`
- `KANUN-15`
- `TEB-01`
- `TEB-03`
- `YON-05`

Candidate FAIL, live PASS:

- `CBY-03`
- `KHK-06`
- `KKY-02`
- `KKY-04`
- `YON-03`

Her QID için:

```text
candidate selected_document
live selected_document
candidate selected_article
live selected_article
candidate top5 retrieved candidates
live top5 retrieved candidates
candidate metadata_lookup result
live metadata_lookup result
candidate source lock
live source lock
candidate generation confidence
live generation confidence
```

## Amaç

Drift retrieval ordering’den mi, generation’dan mı, source-lock finalization’dan mı geliyor?

## Acceptance

- Row-level drift source sınıflanmalı:
  - retrieval_ordering_nondeterminism
  - generation_nondeterminism
  - source_lock_tie_break
  - evidence_bundle_ordering
  - confidence/finalization drift
  - unknown

---

# A1.10-E — Controlled Live Cutover Retry

Aşağıdaki koşullar sağlanırsa live cutover tekrar denenebilir:

1. clean git/provenance tamam
2. same-endpoint repeat drift kabul edilebilir
3. directional equivalence policy kabul edildi
4. A1.9 veya yeni live run hard quality gate’i geçiyor
5. adverse delta yok

## Cutover retry

Live `8000` full collection’a alınır:

```text
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
```

Sonra:

1. live smoke20
2. live full100
3. green lane
4. directional candidate/live comparison
5. cutover decision

## Acceptance

Live cutover accepted if:

```text
hard quality gate = PASS
adverse delta gate = PASS
green lane = PASS
runtime provenance = valid
critical family watch = PASS
```

---

# A1.10-F — If Accepted

Yeni baseline ilan et:

```text
Phase 18 Recovery Baseline
```

Artifacts:

- `phase_18_recovery_A1_10_cutover_summary.md`
- `phase_18_recovery_A1_10_repeatability_probe.md`
- `phase_18_recovery_A1_10_directional_equivalence.md`
- `phase_18_recovery_A1_10_live_full_summary.md`
- `phase_18_recovery_A1_10_cutover_decision.md`

Sonra sıra:

1. behavior-preserving `chat.py` decomposition
2. Phase 18 slot-completion redesign

---

# A1.10-G — If Rejected

Eğer repeatability veya adverse delta kötü çıkarsa:

- live cutover yapılmaz
- rollback korunur
- nondeterminism kaynağı izole edilir
- candidate/live process parity düzeltilmeden yeni logic eklenmez

---

## Commit Plan

### Commit 1
- clean A1.9 artifacts
- provenance/run cleanliness fixes

### Commit 2
- repeatability probe scripts/reports
- directional equivalence policy report

### Commit 3
- trace ordering diff report
- cutover retry decision

### Commit 4, only if accepted
- live cutover acceptance artifacts
- new recovery baseline declaration

Her commit sonrası push.

---

## Final Not

A1.9 rollback prosedürel olarak doğruydu; ama yeni analiz gösteriyor ki eski equivalence policy fazla katıydı.

Kalite bakımından live full collection run başarılıydı.  
Şimdi yapılacak iş, kaliteyi değil **determinism ve cutover equivalence policy’yi** doğrulamak.

Bu doğrulanırsa live cutover tekrar denenebilir.
