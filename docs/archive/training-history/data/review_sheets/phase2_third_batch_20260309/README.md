# Phase 2 - Third Lawyer Review Batch (remaining pool)

Bu klasör, ilk iki batch dışında kalan pending-review adaylarının tamamını içerir.

## Dosyalar

- `batch3_remaining76_master.csv`: Referans ana paket (değiştirmeyin).
- `batch3_remaining76_lawyerA.csv`: Avukat A için çalışma kopyası.
- `batch3_remaining76_lawyerB.csv`: Avukat B için çalışma kopyası.
- `batch3_remaining76_stats.json`: Paket + overlap/remaining havuz özeti.

## Seçim Notları

- Kaynak havuz: `sft_train_pending_review.jsonl` (phase1_eval_reports_20260308).
- İlk batch (`phase2_first_batch_20260308`) ve ikinci batch (`phase2_second_batch_20260309`) candidate_id kayıtları dışlandı.
- Dışlama sonrası kalan havuz: **76** kayıt.
- Bu batch'te üretilen kayıt: **76** (kalanların tamamı).
- Bu batch sonrası kalan havuz: **0** kayıt.

## Kullanım

1. Her avukat kendi dosyasını (`lawyerA` / `lawyerB`) açsın.
2. Her satır için `lawyer_decision` alanına yalnızca `APPROVE`, `REVISE` veya `REJECT` yazılsın.
3. `REVISE` verilen satırlarda `corrected_answer` doldurulsun.
4. İnceleme bitince doldurulan dosyalar geri toplansın ve quality gate ölçülsün.
