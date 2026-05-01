# Hukuk-AI — Phase 22S Official Source Acquisition Brief

## Karar

Phase 22M-R2 tamamlandı ve karar netleşti:

```text
Option B — Wait for missing source acquisition
```

Legal review sonuçları artık mevcut ve P0 kararları kullanılabilir durumda. Ancak Phase 22F hâlâ açılamaz.

Sebep:

- official source rows için `downloaded=false`
- `sha256` alanları boş
- `raw_file_path` alanları boş
- parser readiness doğrulanmamış
- article boundaries detectable bilgisi doğrulanmamış

Bu nedenle sıradaki faz:

```text
Phase 22S — Official Source Acquisition
```

Bu faz runtime remediation fazı değildir.

Productization kapalı.  
Fine-tuning kapalı.  
Phase 22F kapalı.

---

## 1. Phase 22M-R2’den Gelen Legal Kararlar

### MULGA-01

Legal review şunları teyit etti:

```text
2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği = historical/repealed source
2023 repeal instrument = gerekli
2547 sayılı Yükseköğretim Kanunu m.54 = current-law basis
Sayıştay Kanunu m.98 = bu item için hukuken ilgisiz
```

Backfill gerekiyor.

### TEB-06

Legal review şunları teyit etti:

```text
23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ = primary tebliğ
6102 TTK m.210 = supporting legal basis
Ticaret Sicili Yönetmeliği = supporting framework
2021 amendment instrument = current text control için gerekli
Relevant article scope = m.4-m.8
Direct signing = m.8
Identity/document verification = m.6
```

Title-only/body=0 evidence hukuken yeterli değil. Backfill gerekiyor.

---

# 2. Phase 22S Ana Hedef

P0 shadow backfill için gerekli resmî kaynak paketlerini hazırlamak.

Bu fazın çıktısı:

```text
official URL
raw downloaded file
raw_file_path
SHA-256 hash
parser readiness
article-boundary detectability
source provenance bundle
```

Bu bilgiler tamamlanmadan Phase 22F açılamaz.

---

# 3. Kesin Kurallar

Phase 22S boyunca:

- runtime code change yok
- source identity patch yok
- article/span selector patch yok
- answer synthesis patch yok
- answer slot patch yok
- retrieval/top-k/prompt değişikliği yok
- Milvus live collection update yok
- shadow collection build yok
- benchmark run yok
- productization yok
- fine-tuning yok
- private benchmark answer key kullanılmayacak

Bu faz yalnız resmî kaynak edinimi, hash/provenance ve parser-readiness doğrulama fazıdır.

---

# 4. Phase 22S-A — Official Source Acquisition Manifest

## Amaç

Legal review sonucunda required hale gelen resmî kaynakları tek manifest altında listelemek.

## Output

```text
reports/benchmark/phase_22S_official_source_acquisition_manifest.md
reports/benchmark/phase_22S_official_source_acquisition_manifest.csv
```

## Required sources

Minimum kaynaklar:

```text
2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği
2023 repeal instrument for 2012 YÖK discipline regulation
2547 sayılı Yükseköğretim Kanunu m.54
23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ
6102 sayılı Türk Ticaret Kanunu m.210
Ticaret Sicili Yönetmeliği relevant framework provisions
2021 amendment instrument for 23093 current text control
```

## Her kaynak için alanlar

```text
source_id
source_title
source_family
purpose
qid_dependency
official_url
publication_date
official_gazette_no
raw_source_expected_format
download_required
parser_required
article_scope_required
notes
```

## Commit

```text
Create Phase 22S official source acquisition manifest
```

Push zorunlu.

---

# 5. Phase 22S-B — Raw Source Download and Provenance Bundle

## Amaç

Manifestteki kaynakları resmî/public URL’lerden indirmek ve provenance bundle oluşturmak.

## Raw source directory

```text
reports/benchmark/source_acquisition/phase_22S/raw/
```

## Provenance directory

```text
reports/benchmark/source_acquisition/phase_22S/provenance/
```

## Her kaynak için kaydedilecekler

```text
raw_file_path
official_url
retrieved_at
sha256
content_type
file_size_bytes
download_method
source_title
source_family
qid_dependency
```

## Output

```text
reports/benchmark/phase_22S_raw_source_provenance.md
reports/benchmark/phase_22S_raw_source_provenance.csv
```

## Kurallar

- Yalnız resmî/public source kullanılacak.
- URL kaydedilecek.
- Raw file değiştirilmeden saklanacak.
- SHA-256 hash hesaplanacak.
- Eğer kaynak indirilemiyorsa failure reason yazılacak.
- OCR yapılmayacak; OCR gerekiyorsa ayrı karar istenecek.
- Live collection’a hiçbir şey yazılmayacak.

## Commit

```text
Acquire Phase 22S official raw sources
```

Push zorunlu.

---

# 6. Phase 22S-C — Parser Readiness / Article Boundary Audit

## Amaç

İndirilen raw source dosyalarının Phase 22F shadow backfill için parse edilebilir olup olmadığını değerlendirmek.

## Output

```text
reports/benchmark/phase_22S_parser_readiness_audit.md
reports/benchmark/phase_22S_parser_readiness_audit.csv
```

## Her kaynak için alanlar

```text
source_id
source_title
raw_file_path
sha256
content_type
text_extractable
parser_ready
article_boundaries_detectable
detected_article_count
required_article_scope_present
required_article_scope
encoding_issue
table_or_annex_issue
manual_cleanup_required
ocr_required
phase22F_ready
blocking_reason
```

## Required article scopes

### MULGA-01

```text
2012 YÖK Öğrenci Disiplin Yönetmeliği: relevant discipline articles
2023 repeal instrument: repeal clause
2547 m.54: current-law basis
```

### TEB-06

```text
23093 tebliğ: m.4-m.8
23093 tebliğ: m.6
23093 tebliğ: m.8
6102 TTK: m.210
Ticaret Sicili Yönetmeliği: relevant company formation / registry provisions
2021 amendment instrument: current text control
```

## Commit

```text
Audit Phase 22S parser readiness
```

Push zorunlu.

---

# 7. Phase 22S-D — Filled Official Source Checklist Update

## Amaç

Legal review return checklist’in source acquisition alanlarını doldurmak.

## Output

```text
reports/benchmark/legal_review_returns/filled_phase_22M_official_source_acquisition_checklist.csv
```

Bu dosyada artık şu alanlar dolu olmalı:

```text
source_title
official_url
downloaded
raw_file_path
sha256
parser_ready
article_boundaries_detectable
```

## Acceptance

- Required source rows eksiksiz olmalı.
- `downloaded=true` olan her kaynak için `raw_file_path` ve `sha256` dolu olmalı.
- Phase 22F’ye girecek kaynaklarda `parser_ready=true`.
- Article boundaries detect edilemiyorsa Phase 22F için blocker yazılmalı.

## Commit

```text
Update filled official source acquisition checklist
```

Push zorunlu.

---

# 8. Phase 22S-E — Phase 22F Readiness Recheck

## Amaç

Guard script ve readiness logic ile Phase 22F açılabilir mi tekrar kontrol etmek.

## Komut

```bash
python3 scripts/benchmark/check_phase22m_review_returns.py
```

## Beklenen sonuç

Eğer P0/P1 filled CSV’ler zaten mevcutsa ve official checklist tamamlandıysa:

```text
EXIT_CODE=0
Phase 22M-R2 intake may proceed
```

Eğer eksik varsa:

```text
EXIT_CODE=2 or EXIT_CODE=3
Phase 22F blocked
```

## Output

```text
reports/benchmark/phase_22S_phase22F_readiness_recheck.md
```

## Commit

```text
Recheck Phase 22F readiness after source acquisition
```

Push zorunlu.

---

# 9. Phase 22S Final Report

## Output

```text
reports/benchmark/phase_22S_official_source_acquisition_report.md
```

## İçerik

1. commit SHA list
2. acquisition manifest summary
3. raw source provenance table
4. parser readiness table
5. updated filled source checklist path
6. guard script result
7. Phase 22F readiness decision
8. productization gate decision
9. fine-tuning gate decision
10. next phase recommendation

## Decision options

### Option A — Phase 22F ready

```text
Open Phase 22M-R2 intake first, then Phase 22F if validation passes
```

### Option B — Source acquired but parser not ready

```text
Open Phase 22P parser/materialization preparation
No Phase 22F yet
```

### Option C — Source acquisition incomplete

```text
Continue Phase 22S
No Phase 22F
```

### Option D — Legal/source mismatch found

```text
Return to Phase 22M legal review
No Phase 22F
```

---

# 10. Productization / Fine-Tuning

Productization remains closed.

Fine-tuning remains closed.

Phase 22S yalnız source acquisition fazıdır. Başarılı olsa bile doğrudan productization veya fine-tuning açılmaz.

---

## Final Note

Legal review geldi; artık blocker source acquisition.

Phase 22S’nin görevi resmi kaynakları bulmak, indirmek, hashlemek ve parser-readiness doğrulamaktır.

Bu tamamlanmadan shadow backfill yapılamaz.
