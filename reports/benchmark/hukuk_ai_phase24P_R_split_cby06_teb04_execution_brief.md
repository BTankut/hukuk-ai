# Hukuk-AI — Phase 24P-R Split Execution Brief: CBY-06 Shadow Materialization + TEB-04 Raw Capture

## Karar

Phase 24P raporu iki farklı durum gösterdi:

## CBY-06

```text
official_source_found = yes
raw_source_captured = yes
raw_sha256 = ee7fb174b947cb3e0b56aec314fd553ad1c4a9edd80c1acd77f5ebde185577ae
normalized_ocr_sha256 = 9ffabf7aa48476431298308b2bfd302d017704c8baf734bbfd20ee5c57656fe2
m11_added_paragraph_visible = yes
safe_for_materialization = yes
```

CBY-06 artık shadow materialization için güvenlidir.

## TEB-04

```text
official_consolidated_source_confirmed = yes
source_key = 19631
current_runtime_problem = m.0 document-level span
section_text_browser_visible = yes
local_authoritative_raw_payload_captured = no
safe_for_section_materialization = no
```

TEB-04 hâlâ blokludur. GİB KDV Genel Uygulama Tebliği PDF’i görünür, fakat local hash’lenebilir official raw PDF/text payload henüz yakalanmamıştır.

Bu nedenle Phase 24P-R iki ayrı hatta ilerleyecek:

```text
Phase 24P-R1 — CBY-06-only shadow materialization
Phase 24P-R2 — TEB-04 reproducible official raw capture
```

Live `8000` değişmeyecek.  
Productization kapalı.  
Internal eval kapalı.  
Fine-tuning kapalı.

---

# 1. Kesin Kurallar

Bu faz boyunca:

- live `8000` değişmeyecek
- base/live collection overwrite edilmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- model/prompt/top-k değişmeyecek
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak
- TEB-04 raw capture tamamlanmadan TEB section materialization yapılmayacak
- CBY-06 materialization TEB-04’e bağımlı olmayacak

---

# 2. Phase 24P-R1 — CBY-06-Only Shadow Materialization

## Amaç

CBY-06 için güvenli olduğu doğrulanan 03.04.2026 / RG 33213 / Karar 11153 / m.11 ek fıkra span’ını shadow-only materialize etmek.

## Input

```text
official Resmî Gazete PDF:
https://www.resmigazete.gov.tr/eskiler/2026/04/20260403-7.pdf

raw_sha256:
ee7fb174b947cb3e0b56aec314fd553ad1c4a9edd80c1acd77f5ebde185577ae

normalized_ocr_sha256:
9ffabf7aa48476431298308b2bfd302d017704c8baf734bbfd20ee5c57656fe2
```

## Output

```text
reports/benchmark/phase_24P_R1_cby06_materialization_plan.md
reports/benchmark/phase_24P_R1_cby06_shadow_materialization_report.md
reports/benchmark/phase_24P_R1_shadow_runtime_provenance.json
```

## Target collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
```

## Base collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## Materialization requirements

Create canonical spans for:

```text
Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği m.11 added paragraph
03.04.2026 / RG 33213 / Karar 11153 amendment metadata
```

Must preserve:

```text
source_family = CB_YONETMELIK
effective_state = amended/current
publication_date = 2026-04-03
official_gazette_no = 33213
decision_no = 11153
raw_sha256
normalized_ocr_sha256
```

## Acceptance

```text
target collection created
entity_count >= base entity_count
canonical_key_collision_count = 0
binding_key_collision_count = 0
vector_dimension = 1024
live 8000 unchanged
```

## Commit

```text
Materialize Phase 24P-R1 CBY-06 amendment shadow span
```

Push required.

---

# 3. Phase 24P-R1 Targeted Smoke

Only run after R1 materialization succeeds.

## Runtime

Use non-live candidate port, for example:

```text
http://127.0.0.1:8034/v1
```

## Collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
```

## QIDs

Target:

```text
CBY-06
```

Guard:

```text
MULGA-01
MULGA-05
TEB-06
KANUN-12
YON-04
TUZUK-04
CBG-01
CBKAR-08
UY-01
```

## Acceptance

```text
CBY-06 improves or PASS
MULGA-01 PASS
MULGA-05 PASS
TEB-06 PASS
contract_valid all
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
TUZUK-04 not active-current-law claim
```

## Output

```text
reports/benchmark/phase_24P_R1_cby06_targeted_smoke_report.md
```

## Commit

```text
Run Phase 24P-R1 CBY-06 targeted smoke
```

Push required.

---

# 4. Phase 24P-R2 — TEB-04 Reproducible Official Raw Capture

## Amaç

GİB KDV Genel Uygulama Tebliği için local hash’lenebilir official raw PDF/text payload yakalamak.

## Known official URL

```text
https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf
```

## Output

```text
reports/benchmark/phase_24P_R2_teb04_raw_capture_report.md
reports/benchmark/phase_24P_R2_teb04_raw_capture.csv
```

## Required fields

```text
official_url
download_method
http_status
content_type
file_size_bytes
raw_file_path
raw_file_sha256
text_extractable
section_text_visible
section_boundary_detectable
I_C_2_1_3_present
tevkifat_present
iade_present
safe_for_section_materialization
blocking_reason
```

## Capture rules

Try reproducible methods in this order:

1. direct HTTP download preserving headers
2. browser/user-agent download
3. curl with redirects and content-disposition
4. if server returns wrapper JSON/HTML, save wrapper but mark not authoritative raw PDF
5. if only browser-rendered PDF text is accessible, save text extraction as non-authoritative unless raw binary hash is also captured

## Acceptance

```text
raw_file_path exists
raw_file_sha256 populated
content_type is PDF or authoritative official text
section text extractable
I/C-2.1.3 or relevant tevkifat/iade section visible
safe_for_section_materialization = true
```

## If capture fails

Do not materialize TEB-04.

Create explicit blocker:

```text
reports/benchmark/phase_24P_R2_teb04_capture_blocker.md
```

## Commit

```text
Capture Phase 24P-R2 TEB-04 official raw source
```

Push required.

---

# 5. Optional Phase 24P-R3 — TEB-04 Section Materialization

Only run if R2 says:

```text
safe_for_section_materialization = true
```

## Target collection

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_teb04
```

## Materialize

```text
KDV Genel Uygulama Tebliği relevant section spans
I/C-2.1.3 if present
tevkifat/iade sections
section/table/paragraph keys, not only m.0
```

## Output

```text
reports/benchmark/phase_24P_R3_teb04_section_materialization_report.md
```

## Commit

```text
Materialize Phase 24P-R3 TEB-04 KDV section spans
```

---

# 6. Optional Combined Shadow Benchmark

Only run if either:

```text
CBY-06 targeted smoke improves/PASS
or
TEB-04 section materialization succeeds and targeted smoke passes
```

## Minimum gate

```text
raw_score_proxy >= 816
pass_proxy >= 91
wrong_family <= 6
wrong_document <= 4
hallucinated_identifier <= 4
green_lane = PASS
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
```

## Output

```text
reports/benchmark/phase_24P_R_full_shadow_summary.md
reports/benchmark/phase_24P_R_delta_vs_phase23RE.md
reports/benchmark/phase_24P_R_green_lane_summary.md
```

## Commit

```text
Run Phase 24P-R full shadow benchmark
```

---

# 7. Internal Eval Readiness Recheck

Always run after R1/R2/R3 decisions.

## Output

```text
reports/benchmark/phase_24P_R_internal_eval_readiness_recheck.md
```

## Decision options

```text
internal_eval_ready
limited_legal_review_eval_only
not_ready_continue_residual_closure
```

## Commit

```text
Recheck Phase 24P-R internal eval readiness
```

---

# 8. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24P_R_split_execution_report.md
```

Must include:

1. commit SHA list
2. CBY-06 materialization result
3. CBY-06 targeted smoke
4. TEB-04 raw capture result
5. TEB-04 materialization result or blocker
6. full shadow benchmark result or not-run reason
7. internal eval decision
8. productization decision
9. fine-tuning decision
10. final live 8000 state
11. remaining blockers

## Commit

```text
Report Phase 24P-R split execution outcome
```

Push required.

---

# 9. Stop Rules

Stop or skip unsafe branch if:

```text
live 8000 modified
base collection modified
QID-specific runtime branch introduced
MULGA-01 regresses
MULGA-05 regresses
TEB-06 regresses
contract invalid appears
unsupported confident appears
source_key_v2 collision appears
binding collision appears
TUZUK-04 active-current-law claim returns
TEB-04 raw source not reproducible/hashable
```

---

## Final Note

Do not block CBY-06 on TEB-04.

CBY-06 is ready for shadow materialization now.  
TEB-04 still needs reproducible official raw capture before materialization.
