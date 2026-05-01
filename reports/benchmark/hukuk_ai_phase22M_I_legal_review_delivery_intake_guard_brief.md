# Hukuk-AI — Phase 22M-I Legal Review Delivery / Intake Guard Brief

## Karar

Phase 22M-C tamamlandı ve Phase 22M-R sonucuna göre hâlâ şu karar geçerli:

```text
Await filled legal review CSV files.
No runtime work.
No productization.
No fine-tuning.
```

Repo’daki Phase 22M-C raporu, üç filled CSV dönmeden Phase 22F’nin kapalı kalacağını söylüyor:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

Bu nedenle sıradaki görev runtime geliştirme değil, legal-review delivery/intake guard hazırlığıdır.

---

## 1. Amaç

Phase 22M-I’nin amacı:

1. Avukatlara gönderilecek paketi tek manifest altında netleştirmek.
2. Filled CSV dosyaları döndüğünde nereye konacağını standartlaştırmak.
3. Phase 22F’nin yanlışlıkla erken açılmasını engellemek.
4. Repo içinde legal-review pending durumunu makine-okunabilir hale getirmek.
5. Runtime/model/Milvus/benchmark davranışına dokunmadan intake sürecini güvenli hale getirmek.

---

## 2. Kesin Kurallar

Phase 22M-I boyunca:

- runtime code change yok
- source identity patch yok
- article/span selector patch yok
- answer synthesis patch yok
- answer slot patch yok
- retrieval / top-k / prompt değişikliği yok
- Milvus live collection update yok
- shadow collection build yok
- benchmark run yok
- productization yok
- fine-tuning yok
- QID-specific rule yok

Bu faz yalnızca dokümantasyon, intake klasörü ve validasyon guard fazıdır.

---

## 3. Phase 22M-I-A — Legal Review Delivery Manifest

## Amaç

Avukatlara gönderilecek tüm dosyaları ve beklenen dönüşleri tek yerde listeleyen manifest üretmek.

## Output

```text
reports/benchmark/phase_22M_I_legal_review_delivery_manifest.md
```

## İçerik

### Gönderilecek input dosyaları

```text
reports/benchmark/phase_22M_P0_manual_legal_review_packet.csv
reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.csv
reports/benchmark/phase_22M_official_source_acquisition_checklist.csv
reports/benchmark/phase_22M_C_legal_review_followup_packet.md
reports/benchmark/phase_22M_C_legal_review_followup_checklist.md
reports/benchmark/phase_22M_C_P0_reviewer_instructions.md
reports/benchmark/phase_22M_C_P1_taxonomy_reviewer_instructions.md
reports/benchmark/phase_22M_C_official_source_acquisition_instructions.md
reports/benchmark/phase_22M_C_legal_review_handoff_summary.md
```

### Beklenen dönüş dosyaları

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

### Minimum karar

```text
P0 rows must have legal decision.
P1 rows must have taxonomy decision.
Official source rows must have URL/hash/parser readiness where required.
No private benchmark answer key should be shared.
```

## Commit

```text
Create Phase 22M-I legal review delivery manifest
```

Push zorunlu.

---

## 4. Phase 22M-I-B — Legal Review Return Drop Folder

## Amaç

Avukatlardan dönen dosyaların repo içinde standart bir yere konmasını sağlamak.

## Klasör

```text
reports/benchmark/legal_review_returns/
```

## Oluşturulacak dosyalar

```text
reports/benchmark/legal_review_returns/README.md
reports/benchmark/legal_review_returns/.gitkeep
```

## README içeriği

README şu kuralları içermeli:

1. Avukat dönüş dosyaları bu klasöre konur.
2. Beklenen dosya adları:
   ```text
   filled_phase_22M_P0_manual_legal_review_packet.csv
   filled_phase_22M_P1_manual_taxonomy_review_packet.csv
   filled_phase_22M_official_source_acquisition_checklist.csv
   ```
3. Dosyalarda private answer key olmamalı.
4. Official source raw files burada tutulmamalı; yalnız CSV kararları burada tutulur.
5. Raw source bundle ayrı provenance klasöründe tutulur.
6. Bu dosyalar geldikten sonra Phase 22M-R2 açılır.
7. Bu dosyalar yoksa Phase 22F açılamaz.

## Commit

```text
Create legal review return drop folder
```

Push zorunlu.

---

## 5. Phase 22M-I-C — Intake Guard Script

## Amaç

Filled CSV dosyaları gelmeden Phase 22F’ye yanlışlıkla geçilmesini önlemek.

## Script

```text
scripts/benchmark/check_phase22m_review_returns.py
```

## Davranış

Script aşağıdaki dosyaları kontrol etmeli:

```text
reports/benchmark/legal_review_returns/filled_phase_22M_P0_manual_legal_review_packet.csv
reports/benchmark/legal_review_returns/filled_phase_22M_P1_manual_taxonomy_review_packet.csv
reports/benchmark/legal_review_returns/filled_phase_22M_official_source_acquisition_checklist.csv
```

## Kontroller

### P0 CSV required columns

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

### P1 CSV required columns

```text
qid
legal_reviewer_decision
legal_reviewer_notes
expected_source_if_any
taxonomy_decision
runtime_relabel_allowed
backfill_required
```

### Official checklist required columns

```text
source_title
official_url
downloaded
raw_file_path
sha256
parser_ready
article_boundaries_detectable
```

## Exit behavior

- Eğer üç dosyadan biri yoksa:
  - exit code `2`
  - mesaj: `Phase 22F blocked: filled legal review CSVs missing`
- Eğer kolon eksikse:
  - exit code `3`
  - eksik kolonları yaz
- Eğer dosyalar ve kolonlar varsa:
  - exit code `0`
  - mesaj: `Phase 22M-R2 intake may proceed`

## Script kuralları

- Runtime’a bağlanmayacak.
- Milvus’a bağlanmayacak.
- Benchmark çalıştırmayacak.
- Sadece filesystem/CSV şema kontrolü yapacak.

## Test

Basit pytest veya script-level smoke eklenmeli:

```text
api-gateway/tests/test_phase22m_review_returns_guard.py
```

Testler:

1. Dosyalar yokken blocked.
2. Eksik kolonla invalid.
3. Tam kolonla pass.

## Commit

```text
Add Phase 22M legal review return guard
```

Push zorunlu.

---

## 6. Phase 22M-I-D — Pending Status JSON

## Amaç

Mevcut legal-review durumunu makine-okunabilir hale getirmek.

## Output

```text
reports/benchmark/phase_22M_status.json
```

## İçerik

```json
{
  "phase": "22M",
  "status": "awaiting_legal_review_returns",
  "phase22F_allowed": false,
  "productization_allowed": false,
  "finetuning_allowed": false,
  "required_return_files": [
    "reports/benchmark/legal_review_returns/filled_phase_22M_P0_manual_legal_review_packet.csv",
    "reports/benchmark/legal_review_returns/filled_phase_22M_P1_manual_taxonomy_review_packet.csv",
    "reports/benchmark/legal_review_returns/filled_phase_22M_official_source_acquisition_checklist.csv"
  ],
  "next_phase_when_ready": "Phase 22M-R2",
  "runtime_work_allowed": false
}
```

## Commit

```text
Record Phase 22M machine-readable pending status
```

Push zorunlu.

---

## 7. Phase 22M-I-E — Final Intake Readiness Report

## Output

```text
reports/benchmark/phase_22M_I_intake_readiness_report.md
```

## İçerik

1. Commit SHA listesi
2. Delivery manifest path
3. Return drop folder path
4. Guard script path
5. Guard test result
6. Pending status JSON path
7. Phase 22F gate status
8. Productization gate decision
9. Fine-tuning gate decision
10. Next trigger

## Final decision

```text
Await filled legal review CSV files.
Phase 22M-R2 may proceed only after guard passes.
No runtime work.
No productization.
No fine-tuning.
```

## Commit

```text
Record Phase 22M-I intake readiness report
```

Push zorunlu.

---

## 8. Phase 22M-R2 Trigger

Phase 22M-R2 yalnız şu komut exit code `0` verirse açılır:

```bash
python scripts/benchmark/check_phase22m_review_returns.py
```

Aksi halde:

```text
Continue legal review follow-up.
Do not open Phase 22F.
```

---

## 9. Productization / Fine-Tuning

Productization kapalı.

Fine-tuning kapalı.

Bu gate’ler yalnızca:

1. legal-review CSV’leri geldikten,
2. Phase 22M-R2 intake geçtikten,
3. gerekiyorsa Phase 22F shadow backfill tamamlandıktan,
4. stability tekrarlandıktan

sonra yeniden ele alınabilir.

---

## Final Note

Bu fazın amacı ilerleme kaydetmek değil, yanlış ilerlemeyi engellemektir.

Filled legal-review CSV’leri gelmeden runtime patch veya shadow backfill açmak yasak.
