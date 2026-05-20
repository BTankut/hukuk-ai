# Phase 2 - First Lawyer Review Batch (100 items)

Bu klasör, avukat incelemesi için hazırlanan ilk 100 kayıtlık paketi içerir.

## Dosyalar

- `batch1_first100_master.csv`: Referans ana paket (değiştirmeyin).
- `batch1_first100_lawyerA.csv`: Avukat A için çalışma kopyası.
- `batch1_first100_lawyerB.csv`: Avukat B için çalışma kopyası.
- `batch1_first100_stats.json`: Paket dağılım özeti (difficulty/category/source).

## Kullanım

1. Her avukat kendi dosyasını (`lawyerA` / `lawyerB`) açsın.
2. Her satır için `lawyer_decision` alanına yalnızca `APPROVE`, `REVISE` veya `REJECT` yazılsın.
3. `REVISE` verilen satırlarda `corrected_answer` doldurulsun.
4. İnceleme bitince doldurulan dosyalar geri toplansın ve `scripts/calculate_approval_rate.py` ile quality gate ölçülsün.

> Not: Bu paket **pending_review** adaylarından hazırlanmıştır; satırların hiçbiri avukat onaylı değildir.
