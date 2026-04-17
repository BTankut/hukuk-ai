# Mevzuat Faz-2B Gercek Uzman Avukat Review Protokolu 2026-04-17

## Binding Rules
- `review_format = APPROVE_REVISE_REJECT`
- `corrected_answer_required_if_revise = true`
- `human_reviewer_name_required = true`
- `model_name_as_reviewer_forbidden = true`
- `second_reviewer_required_for_reject = true`
- `second_reviewer_required_for_cross_type = true`
- `second_reviewer_required_for_refusal = true`

## Human Review Rules
- `reviewer_name` alani gercek insan adiyla doldurulacaktir.
- `second_reviewer_name` gerekiyorsa gercek insan adiyla doldurulacaktir.
- `APPROVE` icin corrected answer zorunlu degildir.
- `REVISE` icin corrected answer zorunludur.
- `REJECT` satirlari ikinci avukata zorunlu gider.
- `cross_type_disambiguation = true` satirlari ikinci avukata zorunlu gider.
- `excluded_source_unsupported_source_refusal` satirlari ikinci avukata zorunlu gider.
- problem core satirlari provisional ihtilafli satir kabul edilir ve ikinci review alaninda `REQUIRED` ile isaretlenir.
