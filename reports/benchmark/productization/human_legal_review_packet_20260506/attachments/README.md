# Attachments

Hukukçu ek resmi kaynak dosyası verirse bu klasöre koymalı.

Beklenen örnekler:

- `TUZUK-05` için resmi kaynak PDF/TXT/DOC veya resmi metin kopyası.
- `TEB-04` için browser'dan kaydedilmiş orijinal GİB KDV Genel Uygulama Tebliği PDF'i veya resmi hashlenebilir metin kopyası.

Dosya eklenirse `return/TO_BE_FILLED_human_legal_review_return.csv` içinde:

- `raw_file_provided=yes`
- `raw_file_path_or_attachment_name=attachments/<dosya_adi>`
- `sha256=<dosyanin_sha256_degeri>`
- `parser_ready=yes/no`

alanları doldurulmalı.

