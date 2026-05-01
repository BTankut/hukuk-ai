# Hukuk-AI — Phase 22M-R Manual Legal Review Results Intake Brief

## Karar

Phase 22M tamamlandı ve doğru karar verildi:

```text
Option B — Legal sign-off incomplete
```

Bu nedenle sıradaki faz:

```text
Phase 22M-R — Manual Legal Review Results Intake
```

Phase 22M-R bir runtime remediation fazı değildir.

Amaç:

- Avukatlardan dönen legal review CSV’lerini içeri almak
- P0 ve P1 kararlarını normalize etmek
- Official source acquisition checklist durumunu doğrulamak
- Phase 22F P0 Shadow Backfill açılabilir mi kararını vermek
- Productization / fine-tuning gate kararını güncellemek

Runtime patch yok.  
Live collection update yok.  
Productization kapalı.  
Fine-tuning kapalı.

---

# 1. Phase 22M’den Gelen Girdiler

Avukatlara gönderilen CSV paketleri:

```text
reports/benchmark/phase_22M_P0_manual_legal_review_packet.csv
reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.csv
reports/benchmark/phase_22M_official_source_acquisition_checklist.csv
```

Beklenen avukat dönüşleri:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

Eğer dosya isimleri farklı gelirse, input path’leri raporda açıkça yazılmalı.

---

# 2. Phase 22M-R Ana Hedefleri

## 2.1 P0 Legal Sign-Off Intake

P0 rows:

```text
MULGA-01
TEB-06
```

Her row için legal reviewer decision okunmalı:

```text
confirmed_expected_source
confirmed_article_or_clause
confirmed_effective_state
confirmed_current_law_relation
confirmed_backfill_required
accepted_as_manual_residual
benchmark_item_legally_invalid
needs_more_official_source_acquisition
```

## 2.2 P1 Taxonomy Sign-Off Intake

P1 rows:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

Allowed legal reviewer decisions:

```text
do_not_relabel
expected_cb_yonetmelik_source_identified
expected_primary_law_identified
benchmark_item_needs_rubric_review
kky_taxonomy_rule_confirmed
keep_yonetmelik_classification
expected_kky_source_identified
expected_tuzuk_article_identified
corpus_backfill_required
expected_yonetmelik_source_identified
defer_needs_more_legal_research
```

## 2.3 Official Source Acquisition Intake

Her required source için şu alanlar doğrulanmalı:

```text
official_url
raw_source_available
downloaded
sha256
parser_ready
article_boundaries_detectable
```

---

# 3. Kesin Kurallar

Phase 22M-R boyunca:

- runtime code change yok
- source identity patch yok
- article/span selector patch yok
- answer synthesis patch yok
- answer slot patch yok
- Milvus live collection update yok
- shadow collection build yok
- fine-tuning yok
- productization yok
- benchmark private answer key commit yok
- legal reviewer CSV’leri sanitize edilmeden runtime config’e bağlanmayacak

Bu faz yalnız karar ve intake fazıdır.

---

# 4. Phase 22M-R-A — Review File Validation

## Amaç

Avukatlardan dönen CSV dosyalarının eksiksiz ve beklenen şemaya uygun olduğunu doğrulamak.

## Output

```text
reports/benchmark/phase_22M_R_review_file_validation.md
reports/benchmark/phase_22M_R_review_file_validation.csv
```

## Kontrol edilecekler

### P0 CSV

Zorunlu alanlar:

```text
qid
legal_reviewer_decision
legal_reviewer_notes
confirmed_expected_source
confirmed_article_or_clause
official_source_url
effective_state_decision
current_law_relation
backfill_required
```

### P1 CSV

Zorunlu alanlar:

```text
qid
legal_reviewer_decision
legal_reviewer_notes
expected_source_if_any
taxonomy_decision
runtime_relabel_allowed
backfill_required
```

### Official source checklist

Zorunlu alanlar:

```text
source_title
official_url
downloaded
sha256
parser_ready
article_boundaries_detectable
```

## Validation statuses

```text
valid
missing_required_field
unknown_decision_value
missing_legal_notes
missing_official_url
missing_hash
not_ready_for_backfill
```

## Acceptance

- Tüm input CSV’ler validate edilmeli.
- Eksik alan varsa Phase 22F açılmamalı.
- Runtime behavior değişmemeli.

## Commit

```text
Validate Phase 22M legal review result files
```

Push zorunlu.

---

# 5. Phase 22M-R-B — P0 Decision Normalization

## Amaç

`MULGA-01` ve `TEB-06` için legal review kararını normalize etmek.

## Output

```text
reports/benchmark/phase_22M_R_P0_decision_normalization.md
reports/benchmark/phase_22M_R_P0_decision_normalization.csv
```

## Normalized decision enum

```text
ready_for_shadow_backfill
needs_more_legal_review
needs_official_source_acquisition
accepted_manual_residual
benchmark_item_invalid
not_safe_to_patch
```

## Row-specific handling

### MULGA-01

Karar için gereken minimum veri:

```text
historical_source_confirmed
repeal_instrument_confirmed
current_law_basis_confirmed
effective_state_correction_required
article_or_clause_confirmed
official_source_urls_present
source_hashes_present
```

Eğer 2012 yönetmelik + repeal instrument + 2547 m.54 chain netleşmişse:

```text
ready_for_shadow_backfill
```

Eğer zincir eksikse:

```text
needs_more_legal_review
or
needs_official_source_acquisition
```

### TEB-06

Karar için gereken minimum veri:

```text
primary_teblig_confirmed
article_or_clause_confirmed
official_body_source_url_present
source_hash_present
parser_ready
```

Eğer 23093 veya başka source netleşmiş ve body source hazırsa:

```text
ready_for_shadow_backfill
```

Eğer expected source belirsizse:

```text
needs_more_legal_review
```

Eğer source belli ama raw/body yoksa:

```text
needs_official_source_acquisition
```

## Acceptance

- Her P0 row için normalized decision üretilmeli.
- Phase 22F sadece `ready_for_shadow_backfill` rows için açılabilir.
- Runtime behavior değişmemeli.

## Commit

```text
Normalize Phase 22M P0 legal decisions
```

Push zorunlu.

---

# 6. Phase 22M-R-C — P1 Taxonomy Decision Normalization

## Amaç

P1 rows için legal taxonomy kararlarını normalize etmek.

## Output

```text
reports/benchmark/phase_22M_R_P1_taxonomy_decision_normalization.md
reports/benchmark/phase_22M_R_P1_taxonomy_decision_normalization.csv
```

## Normalized action enum

```text
do_not_patch
ready_for_future_source_identity_fix
ready_for_future_corpus_backfill
needs_more_legal_review
benchmark_rubric_review_required
watch_only
```

## P1 rows

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

## Acceptance

- Runtime relabeling yalnız legal reviewer açıkça izin verirse future backlog’a alınabilir.
- Generic family relabel yok.
- Geniş source-family weakening yok.
- Bu fazda runtime patch yok.

## Commit

```text
Normalize Phase 22M P1 taxonomy decisions
```

Push zorunlu.

---

# 7. Phase 22M-R-D — Phase 22F Readiness Decision

## Amaç

Legal review sonucu Phase 22F P0 Shadow Backfill açılabilir mi kararını vermek.

## Output

```text
reports/benchmark/phase_22M_R_phase22F_readiness_decision.md
```

## Decision options

### Option A — Open Phase 22F

Şartlar:

```text
at least one P0 row ready_for_shadow_backfill
official source URL present
raw source downloaded
sha256 present
parser readiness confirmed
article boundaries detectable
```

Karar:

```text
Open Phase 22F P0 Shadow Backfill Implementation
```

### Option B — Wait for missing source acquisition

Şartlar:

```text
legal source confirmed
but URL/hash/raw source/parser readiness incomplete
```

Karar:

```text
Open Phase 22S Official Source Acquisition
```

### Option C — Continue legal review

Şartlar:

```text
legal source or expected article still unclear
```

Karar:

```text
Continue Phase 22M legal review
```

### Option D — Accept manual residual

Şartlar:

```text
legal owner accepts unresolved row as known corpus/legal backlog
```

Karar:

```text
Open Phase 23 Productization Readiness Audit with accepted residual risk
```

### Option E — Benchmark rubric review

Şartlar:

```text
legal reviewer says benchmark item is invalid or ambiguous
```

Karar:

```text
Open benchmark rubric review
```

## Commit

```text
Record Phase 22M-R readiness decision
```

Push zorunlu.

---

# 8. Phase 22F Preview

Phase 22F yalnız Option A durumunda açılacak.

Scope:

```text
P0 shadow backfill implementation
official source bundle only
shadow collection only
no live overwrite
targeted smoke
full benchmark
cutover decision
```

Target shadow collection:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

Phase 22F açılmadan önce ayrı brief hazırlanmalı.

---

# 9. Productization Gate

Productization remains closed in Phase 22M-R.

Productization readiness audit ancak şu durumda konuşulur:

```text
Phase 22A stability accepted
P0 rows resolved or formally accepted by legal owner
official source provenance complete
runtime serving config separated from benchmark config
residual risk register complete
```

---

# 10. Fine-Tuning Gate

Fine-tuning remains closed.

Reason:

- Current blockers are legal/corpus/source materialization issues.
- Fine-tuning will not fix missing official source text.
- Benchmark contamination controls still required.

---

# 11. Required Final Report

Produce:

```text
reports/benchmark/phase_22M_R_manual_legal_review_results_intake_report.md
```

Report content:

1. commit SHA list
2. input legal review files
3. review file validation summary
4. P0 normalized decisions
5. P1 normalized decisions
6. official source acquisition readiness
7. Phase 22F readiness decision
8. productization gate decision
9. fine-tuning gate decision
10. next phase recommendation

---

## Final Note

Phase 22M created the packets.  
Phase 22M-R ingests the answers.

Do not implement backfill or runtime fixes in Phase 22M-R.  
Only validate, normalize, and decide the next phase.
