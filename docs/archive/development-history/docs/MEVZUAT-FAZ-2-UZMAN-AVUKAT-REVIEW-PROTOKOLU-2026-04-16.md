# Mevzuat Faz-2 Uzman Avukat Review Protokolu 2026-04-16

## Binding Review Decisions
- `APPROVE`
- `REVISE`
- `REJECT`

## Mandatory Rules
- `REVISE` verilirse `corrected_answer` zorunludur.
- `cross_type_disambiguation = true` olan tum satirlar ikinci review icin isaretlidir.
- `REJECT` verilen tum satirlar ikinci avukata gonderilecektir.
- `second_reviewer_name = REQUIRED` olan satirlar ikinci review zorunlulugunu gosterir.

## CSV Column Meaning
- `question` = avukatin degerlendirecegi review-ready soru
- `model_answer` = shadow collection’a anchor edilmis acceptance-draft cevap
- `source_citation` = supported sorularda gorunur citation
- `expected_source_type` = beklenen mevzuat turu
- `expected_display_citation` = beklenen exact gosterim
- `expected_yururluk_state` = beklenen temporal durum

## Review Boundary
- Bu fazda runtime cutover veya production switch yoktur.
- Bu fazda lawyer review hazirligi acilmistir; filled CSV execution sonraki resmi istir.
