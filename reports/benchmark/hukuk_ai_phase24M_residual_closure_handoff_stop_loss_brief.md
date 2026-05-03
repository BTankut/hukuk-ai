# Hukuk-AI — Phase 24M Residual Closure Handoff and Stop-Loss Brief

## Karar

Phase 24J-R2 tamamlandı ve karar şudur:

```text
Option B — TARGET clean but no improvement
```

Bu şu anlama gelir:

- Phase24J target collection guard regresyonu üretmiyor.
- Önceki Phase24J-D hatası collection içerik regresyonu değil, normalized olmayan runtime/load/provenance koşusundan kaynaklanmış görünüyor.
- Ancak residual targeted smoke’ta anlamlı iyileşme yok.
- Phase 24K-R2 full shadow benchmark yetkili değil.
- Phase24J collection diagnostic-only kalmalı.
- Productization kapalı.
- Internal eval kapalı.
- Fine-tuning kapalı.

Bu fazın amacı daha fazla runtime denemesi yapmak değil; kalan işi net bir blocker/handoff paketine bağlamak ve stop-loss kararı üretmektir.

---

## 1. Kesin Kurallar

Phase 24M boyunca:

- live `8000` değiştirilmeyecek
- Phase24J collection live/candidate olarak kullanılmayacak
- full benchmark koşulmayacak
- shadow remediation yapılmayacak
- prompt/model/top-k değiştirilmeyecek
- productization açılmayacak
- internal eval açılmayacak
- fine-tuning açılmayacak
- QID-specific runtime branch yok
- benchmark answer key kullanılmayacak

Bu faz audit/handoff/finalization fazıdır.

---

## 2. Phase 24M-A — Diagnostic Collection Disposition

## Amaç

Phase24J target collection’ın durumunu resmi olarak diagnostic-only şeklinde kaydetmek.

## Output

```text
reports/benchmark/phase_24M_diagnostic_collection_disposition.md
```

## İçerik

```text
base collection
phase24j target collection
entity counts
load state
reason full benchmark not authorized
reason collection should not be cut over
whether collection should be retained or released
```

## Commit

```text
Record Phase 24M diagnostic collection disposition
```

Push required.

---

## 3. Phase 24M-B — Residual Blocker Consolidation

## Amaç

Kalan residual rows için son durum ve kapatma yolunu tek tabloda toplamak.

## Rows

```text
CBY-04
CBY-06
KANUN-12
KKY-01
KKY-03
TEB-04
TUZUK-04
TUZUK-05
YON-04
```

## Output

```text
reports/benchmark/phase_24M_residual_blocker_consolidation.md
reports/benchmark/phase_24M_residual_blocker_consolidation.csv
```

## Fields

```text
qid
current_score
current_failure_class
current_status
blocks_internal_eval
blocks_productization
legal_review_required
source_acquisition_required
scorer_rubric_review_required
corpus_backfill_required
latest_attempt
latest_attempt_result
safe_next_action
owner
```

## safe_next_action enum

```text
await_legal_scorer_review
await_source_acquisition
manual_acceptance_required
scorer_rubric_review_required
corpus_backfill_required
do_not_patch_runtime
```

## Commit

```text
Consolidate Phase 24M residual blockers
```

Push required.

---

## 4. Phase 24M-C — Required Human Return Files Check

## Amaç

İlerlemenin hangi dış dönüş dosyalarına bağlı olduğunu netleştirmek.

## Expected files

```text
reports/benchmark/legal_review_returns/filled_phase_24H_legal_scorer_review_return.csv
reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_checklist.csv
```

## Output

```text
reports/benchmark/phase_24M_required_human_returns_check.md
```

## Decision

### If files exist and are complete

```text
Open new intake phase.
```

### If files are missing/incomplete

```text
Do not run runtime work.
Prepare final human-action packet.
```

## Commit

```text
Check Phase 24M required human return files
```

Push required.

---

## 5. Phase 24M-D — Human Action Packet

## Amaç

Master planner / kullanıcı / uzman için tam olarak ne bekleniyor dosyasını üretmek.

## Output

```text
reports/benchmark/phase_24M_human_action_packet.md
```

## İçerik

1. Doldurulması gereken dosyalar
2. Hangi rol dolduracak
3. Hangi QID’ler kaldı
4. Hangi QID internal_eval blocker
5. Hangi QID productization blocker
6. Hangi QID source acquisition blocker
7. Hangi QID scorer/legal review blocker
8. Runtime tarafında neden artık devam edilmemesi gerektiği
9. Dönüş geldikten sonra açılacak faz

## Commit

```text
Create Phase 24M human action packet
```

Push required.

---

## 6. Phase 24M-E — Final Stop-Loss Decision

## Output

```text
reports/benchmark/phase_24M_stop_loss_decision.md
```

## Decision options

### Option A — Wait for human returns

```text
No runtime work.
Live 8000 remains benchmark-only.
Await human/legal/source files.
```

### Option B — Accept benchmark-only as final technical milestone

```text
Freeze technical work.
Keep productization/internal_eval closed.
Archive remaining residuals.
```

### Option C — Open intake if human returns are now complete

```text
Open next intake phase.
```

## Commit

```text
Record Phase 24M stop-loss decision
```

Push required.

---

## 7. Mandatory Final Report

Always produce:

```text
reports/benchmark/phase_24M_residual_closure_handoff_report.md
```

Must include:

1. commit SHA list
2. diagnostic collection disposition
3. residual blocker consolidation
4. human return file check
5. human action packet
6. stop-loss decision
7. productization decision
8. internal eval decision
9. fine-tuning decision
10. final live 8000 state

## Commit

```text
Report Phase 24M residual closure handoff
```

Push required.

---

## Final Note

Phase24J-R2 proved the latest shadow collection is not harmful under normalized provenance, but also not useful enough to continue.

The project is now blocked by external legal/scorer/source closure, not by safe runtime engineering.

Do not continue runtime experimentation until the required human return files are complete or a manual stop-loss decision is accepted.
