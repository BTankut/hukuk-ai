# Phase 2 - Second Lawyer Review Batch (up to 100 items)

Bu klasör, ilk batch'te kullanılmayan pending-review adaylarından hazırlanan ikinci avukat inceleme paketini içerir.

## Dosyalar

- `batch2_second100_master.csv`: Referans ana paket (değiştirmeyin).
- `batch2_second100_lawyerA.csv`: Avukat A için çalışma kopyası.
- `batch2_second100_lawyerB.csv`: Avukat B için çalışma kopyası.
- `batch2_second100_stats.json`: Paket + kalan havuz dağılım özeti.

## Seçim Notları

- Kaynak havuz: `sft_train_pending_review.jsonl` (phase1_eval_reports_20260308).
- İlk batch (`phase2_first_batch_20260308`) içindeki candidate_id kayıtları dışlandı.
- Selection modu: `balanced` (difficulty/category oranını korumaya çalışır).
- Dışlama sonrası havuz: **176** kayıt.
- Bu batch'te üretilen kayıt: **100**.
- Bu batch sonrası tahmini kalan havuz: **76** kayıt.

## Kullanım

1. Her avukat kendi dosyasını (`lawyerA` / `lawyerB`) açsın.
2. Her satır için `lawyer_decision` alanına yalnızca `APPROVE`, `REVISE` veya `REJECT` yazılsın.
3. `REVISE` verilen satırlarda `corrected_answer` doldurulsun.
4. İnceleme bitince doldurulan dosyalar geri toplansın ve quality gate ölçülsün.

> Not: Bu paket **pending_review** adaylarından hazırlanmıştır; satırların hiçbiri avukat onaylı değildir.
