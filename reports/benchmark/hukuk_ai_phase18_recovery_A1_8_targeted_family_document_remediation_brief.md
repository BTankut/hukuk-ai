# Hukuk-AI — Phase 18 Recovery A1.8 Targeted Family / Document Remediation Brief

## Karar

A1.7 sonucu **NO_CUTOVER** kararını doğruluyor. Live `8000` hâlâ değiştirilmemeli.

Büyük collection (`mevzuat_faz1_shadow_20260418_compat1024`) doğru yönde ciddi iyileşme sağladı, ancak full acceptance gate’i geçmedi:

- `raw_score_proxy = 729.1`, hedef `>=735`
- `pass_proxy = 71`, hedef `>=73`
- `wrong_family = 17`, hedef `<=15`
- `wrong_document = 17`, hedef `<=15`
- `hallucinated_identifier = 24`, hedef `<=23`

Buna karşılık olumlu sinyaller güçlü:

- `unsupported_confident_claim = 0`
- `contract_valid = 100/100`
- `green_lane = pass`
- `corpus_materialization_required_count = 1`
- `canonical_span_materialized_count = 99`

Bu nedenle sorun artık genel corpus yokluğu değil. Büyük collection doğru yönde; fakat **family routing + document identity + selected-source arbitration** hâlâ cutover için yeterli değil.

---

## 1. A1.7 Ana Bulgular

### Full candidate sonucu

| Metric | Value |
|---|---:|
| raw_score_proxy | 729.1 |
| pass_proxy | 71 |
| wrong_family | 17 |
| wrong_document | 17 |
| hallucinated_identifier | 24 |
| unsupported_confident_claim | 0 |
| corpus_materialization_required_count | 1 |
| canonical_span_materialized_count | 99 |

### Aile bazlı tablo

En sorunlu aileler:

| Family | Pass | Not |
|---|---:|---|
| YONETMELIK | 3/10 | en büyük kayıp; Phase17F 7/10 idi |
| MULGA | 2/5 | hâlâ kırılgan |
| KKY | 8/11 | Phase17F’den -1 |
| UY | 8/10 | Phase17F’den -1 |
| CB_KARAR | 6/8 | Phase17F’den -1 |
| TUZUK | 3/5 | güçlü aile ama dikkat |
| KHK | 5/6 | güçlü aile, küçük risk |

Korunması gerekenler:

- `CB_GENELGE = 4/4`
- `CB_KARARNAME = 6/6`
- `TEBLIGLER = 7/8`

Ana recovery hedefi:

1. `YONETMELIK`
2. `MULGA`
3. `KANUN` relation / supporting source arbitration
4. strong-family regression guard

---

# Phase A1.8 — Targeted Family / Document Remediation

## Amaç

A1.7 candidate full run’ın cutover gate’i geçmesini engelleyen az sayıdaki family/document drift’i düzeltmek.

Bu fazda yeni slot-completion veya synthesis geliştirmesi yapılmayacak.

Odak:

- selected source family
- selected document identity
- relation/family arbitration
- active/repealed routing
- strong-family regression guard

---

## 2. A1.8-A — Failed Row Cluster Audit

## Yapılacaklar

A1.7 failed rows üzerinden cluster audit üret.

### YONETMELIK failures

- `YON-01`
- `YON-02`
- `YON-03`
- `YON-05`
- `YON-06`
- `YON-08`
- `YON-10`

### MULGA failures

- `MULGA-01`
- `MULGA-02`
- `MULGA-05`

### KANUN failures

- `KANUN-02`
- `KANUN-03`
- `KANUN-04`
- `KANUN-09`
- `KANUN-18`
- `KANUN-19`

### Strong-family / regression watch

- `KKY-01`
- `KKY-04`
- `KKY-10`
- `UY-07`
- `UY-08`
- `TUZUK-04`
- `TUZUK-05`
- `KHK-06`
- `CBKAR-03`
- `CBKAR-08`
- `CBY-01`
- `CBY-03`

Her satır için şu alanları raporla:

```text
qid
expected_family
claimed_family
selected_document
expected_document_if_available
failure_classes
pre_filter_family_set
family_gate_status
selected_family_confidence
metadata_lookup_hit
metadata_lookup_candidates
dense_top_candidates
source_key_v2
binding_source_key
document_identity_score
why_wrong_family_or_document
fix_type
```

## Fix type enum

```text
family_prior_error
relation_query_arbitration_error
active_repealed_arbitration_error
metadata_candidate_missing
candidate_present_but_not_selected
wrong_supporting_source_promoted
source_key_alias_collision
document_identity_rerank_error
strong_family_regression
rubric_only_not_source_error
```

## Acceptance

- Her failed row fix_type ile sınıflanmış olmalı.
- YONETMELIK ve MULGA için ayrı dominant failure açıklaması çıkmalı.
- QID-specific patch yazılmamalı.

## Commit

### Commit 1
- failed-row cluster audit script/report
- no runtime logic change

---

## 3. A1.8-B — YONETMELIK Family Recovery

## Neden öncelik?

A1.7’de `YONETMELIK = 3/10`; Phase17F’de `7/10` idi. Bu aile cutover gate’i en çok düşüren cluster.

## Gözlenen tipik sapmalar

A1.7 failed rows içinde:

- `YON-01`: claimed `KKY`, selected `Sendikalar ve Toplu İş Sözleşmesi Kanunu`
- `YON-02`: claimed `KKY`, selected doğru başlığa yakın ama family yanlış
- `YON-03`: claimed `CB_YONETMELIK`
- `YON-05`: claimed `KANUN`
- `YON-08`: claimed `UY`
- `YON-10`: claimed `KKY`

Bu, `YONETMELIK` ailesinde family boundary’nin KKY/UY/KANUN/CB_YONETMELIK tarafından ezildiğini gösteriyor.

## Yapılacaklar

- `YONETMELIK` için family-prior ve document identity arbitration güçlendir.
- `YONETMELIK` vs `KKY` ayrımı:
  - kurum-kuruluş yönetmelikleri ve kamu/kurul düzenlemeleri KKY’ye kaçmasın
  - genel yönetmelik başlığı exact ise YONETMELIK üstün gelsin
- `YONETMELIK` vs `KANUN` ayrımı:
  - kanun supporting source olabilir ama primary expected yönetmelikse kanun ana kaynak olmasın
- `YONETMELIK` vs `UY` ayrımı:
  - üniversite adı varsa UY
  - genel yükseköğretim yönetmeliği ise YONETMELIK
- `YONETMELIK` vs `CB_YONETMELIK` ayrımı:
  - Cumhurbaşkanlığı/CB authority sinyali yoksa CB_YONETMELIK’e kaçma

## Trace alanları

```text
yonetmelik_boundary_reason
supporting_law_demoted_for_regulation_question
university_specific_regulation_detected
cb_authority_signal_detected
primary_regulation_selected
```

## Acceptance

Targeted YON smoke:

- `YONETMELIK pass >= 6/10`
- wrong_family düşmeli
- kanun/supporting source ana cevap olmamalı

## Commit

### Commit 2
- YONETMELIK family boundary rules
- targeted tests
- YON smoke report

---

## 4. A1.8-C — MULGA Recovery

## Neden?

A1.7’de `MULGA = 2/5`; Phase17F `3/5` idi. Ayrıca historical/current reasoning hâlâ kırılgan.

## Gözlenen sapmalar

- `MULGA-01`: selected modern/active administrative law style source
- `MULGA-02`: selected Kültür ve Turizm Bakanlığı Teşkilat Kanunu
- `MULGA-05`: selected old 6570 m.16 but score düşük

## Yapılacaklar

- Historical/repealed intent detected ise active-law material tekrar primary olmasın.
- MULGA answer slotlarını enforce et:
  - source is repealed/historical
  - applicable period
  - current applicability
  - replacement/current-law relation
  - transition rule
  - direct conclusion
- Eğer replacement relation bulunamazsa:
  - bunu açık missing slot olarak yaz
  - ama active source ile yanlış tamamlamaya çalışma
- `mulga_kanun` family internal arbitration:
  - historical title exact > active kanun related topical source
  - repealed family state compatible > current family topical match

## Acceptance

MULGA smoke:

- `MULGA pass >= 3/5`
- `repealed_source_used_as_active = 0`
- wrong_family artmamalı
- active-law overclaim yok

## Commit

### Commit 3
- MULGA internal arbitration
- historical answer slot enforcement
- MULGA smoke report

---

## 5. A1.8-D — KANUN Relation / Supporting-Source Arbitration

## Neden?

A1.7 failed KANUN rows’unda supporting regulation/tebliğ veya mülga kaynak ana kaynak yapılmış.

Örnekler:

- `KANUN-03`: claimed YONETMELIK / Alt İşverenlik Yönetmeliği
- `KANUN-04`: claimed TEBLIGLER
- `KANUN-09`: claimed MULGA
- `KANUN-19`: Tebligat Kanununun yürürlükten kaldırılmış hükümleri

## Yapılacaklar

- KANUN expected family veya law-heavy query’de primary source kanun olmalı.
- Yönetmelik/tebliğ supporting source olabilir ama primary source yerine geçmemeli.
- Relation query detector şu ayrımı yapsın:
  - primary law question
  - regulation implementing law
  - tebliğ supporting law
  - repealed law historical comparison
- KANUN family claim replacement guard:
  - supporting source primary claim’i overwrite etmesin
  - active/repealed state ile primary kanun seçimi uyumlu olsun

## Acceptance

KANUN targeted smoke:

- `KANUN pass >= 16/21` hedeflenmeli
- KANUN wrong_family düşmeli
- KANUN-19 mülga tebligat hükümlerine kaymamalı

## Commit

### Commit 4
- KANUN primary/supporting arbitration
- relation-query tests
- KANUN smoke report

---

## 6. A1.8-E — Strong-Family Regression Guard

## Amaç

UY, KKY, KHK, TUZUK gibi güçlü aileler cutover sonrası gerilememeli.

## Yapılacaklar

Targeted smoke set:

- `UY-07`, `UY-08`
- `KKY-01`, `KKY-04`, `KKY-10`
- `KHK-06`
- `TUZUK-04`, `TUZUK-05`

Guard rules:

- `UY`:
  - üniversite adı + yönetmelik varsa UY korunmalı
- `KKY`:
  - kurum/kurul karar-yönetmelik türleri KKY olarak korunmalı
  - kanun/tebliğ supporting source ana kaynak olmasın
- `TUZUK`:
  - tüzük ailesi mülga/kanun family tarafından ezilmesin
- `KHK`:
  - KHK vs CB_KARARNAME ayrımı korunmalı

## Acceptance

- Strong-family smoke pass kaybı olmamalı
- UY/KKY/TUZUK/KHK full family pass Phase17F’den fazla düşmemeli

## Commit

### Commit 5
- strong-family guard tests
- targeted smoke
- no broad behavior change

---

# 7. A1.8-F — Candidate Full Rerun

A1.8 remediation sonrası candidate `8018` full benchmark tekrar koşulsun.

## Runtime

```text
api_url=http://127.0.0.1:8018/v1
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
```

## Acceptance gate

| Metric | Target |
|---|---:|
| raw_score_proxy | `>= 735` |
| pass_proxy | `>= 73` |
| wrong_family | `<= 15` |
| wrong_document | `<= 15` |
| hallucinated_identifier | `<= 23` |
| unsupported_confident_claim | `<= 8` |
| contract_valid | `100/100` |
| green_lane | `PASS` |
| corpus_materialization_required_count | `<= 6` |
| canonical_span_materialized_count | `>= 90` |

Additional watch:

- `YONETMELIK pass >= 6/10`
- `MULGA pass >= 3/5`
- strong-family regressions absent

## If gate passes

- controlled live cutover can be reconsidered
- cutover still requires live 20-QID smoke and live full 100 confirmation

## If gate fails

- no cutover
- continue targeted family audit
- do not return to Phase 18 slot-completion yet

---

# 8. Provenance Requirement

Every run must include:

- git SHA
- dirty worktree
- api URL
- model name
- DGX model
- Milvus collection
- Milvus entity count
- vector dimension
- embedding backend/base
- guardrails/presidio flags
- source catalog hash
- source supplement hash

No provenance = invalid run.

---

# 9. Commit Plan

## Commit 1
- failed-row cluster audit
- A1.8 audit reports

## Commit 2
- YONETMELIK recovery
- YON smoke

## Commit 3
- MULGA recovery
- MULGA smoke

## Commit 4
- KANUN primary/supporting arbitration
- KANUN smoke

## Commit 5
- strong-family regression guard
- strong-family smoke

## Commit 6
- A1.8 candidate full benchmark
- cutover recommendation

Her commit sonrası push.

---

## Final Not

A1.7 sonucu doğru karar: **NO_CUTOVER**.

Ama büyük collection yönü doğru. Geriye kalan fark artık dar ve teşhis edilebilir:

- `YONETMELIK` family boundary
- `MULGA` historical/internal arbitration
- `KANUN` primary vs supporting source arbitration
- strong-family regression guard

Bu başlıklar kapanmadan live collection cutover yapılmamalı.
