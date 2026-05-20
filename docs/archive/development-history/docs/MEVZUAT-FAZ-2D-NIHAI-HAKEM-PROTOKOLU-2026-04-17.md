# Mevzuat Faz-2D Nihai Hakem Protokolu 2026-04-17

## Binding Format
- `final_decision`
- `final_comment`
- `final_corrected_answer`
- `final_reviewer_name`

## Allowed Values
- `APPROVE`
- `REVISE`
- `REJECT`

## Binding Rules
- `REVISE` ise `final_corrected_answer` bos birakilamaz.
- `final_reviewer_name` gercek insan adi olmak zorundadir.
- `GPT`, `assistant`, `model`, `GPT-5.4 Pro` benzeri degerler yasaktir.
- Nihai hakem karari bu 5 satir icin baglayici son karardir.
