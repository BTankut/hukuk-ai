# Mevzuat Faz-2C Gercek Insan Review Protokolu 2026-04-17

## Binding Rules
- `review_format = APPROVE_REVISE_REJECT`
- `corrected_answer_required_if_revise = true`
- `human_reviewer_name_required = true`
- `model_name_as_reviewer_forbidden = true`

## Human Reviewer Constraint
- `reviewer_name` gercek insan adi olmak zorundadir.
- `GPT-5.4 Pro`, `model`, `assistant`, bos deger veya tool adi reviewer olarak kabul edilmez.
- `REVISE` ise `corrected_answer` bos birakilamaz.

## Second Reviewer Constraint
- `second_reviewer_required = true` olan satirlarda ikinci avukat review'u zorunludur.
- tum `REJECT` satirlari ikinci avukata gider.
- tum `cross_type_disambiguation = true` satirlari ikinci avukata gider.
- tum `excluded_source_unsupported_source_refusal` satirlari ikinci avukata gider.
- tum problem core satirlari ihtilafli satir kabul edilerek ikinci review alanina acilir.
