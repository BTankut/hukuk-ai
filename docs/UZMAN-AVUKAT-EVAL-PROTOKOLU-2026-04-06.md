# Uzman Avukat Eval Protokolu 2026-04-06

## Review Format

- review_format = `APPROVE / REVISE / REJECT`
- `REVISE` ise `corrected_answer` zorunludur.
- `source_class` etiketi zorunludur.
- `cross_law_disambiguation` etiketi zorunludur.

## Second Lawyer Rule

- tum tartismali satirlarda ikinci avukat incelemesi zorunludur.
- tum `cross_law_disambiguation = true` satirlarinda ikinci avukat incelemesi zorunludur.
- `REJECT` verilen her satir ikinci incelemeye gider.

## Canonical Review Boundary

- bu protokol Hat-A canonical acceptance pack icindir.
- Hat-B ve Hat-C bu fazda review execution acmaz.
- Hat-D retrieval governance only contractual olarak baglidir.
