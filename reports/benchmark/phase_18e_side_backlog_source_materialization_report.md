# Phase 18E Side Backlog Source Materialization Report

Tarih: 2026-04-25

## Karar

Phase 18E yan backlog materyalizasyonu uygulandı. Değişiklik soru/QID odaklı değildir; resmi kaynak supplement satırları canonical source catalog içine family/source-key kimliğiyle bağlandı ve selector/runtime bunları genel mekanizma üzerinden kullanacak şekilde genişletildi.

## Uygulananlar

- `CB_GENELGE 2024/7` Tasarruf Tedbirleri supplement kaynağı eklendi.
- `CB_GENELGE 2019/12` Bilgi ve İletişim Güvenliği supplement kaynağı eklendi.
- `CB_KARAR 9903` Yatırımlarda Devlet Yardımları Hakkında Karar supplement kaynağı eklendi.
- `KANUN 6102` TTK m.595 ve m.598 supplement kaynakları eklendi.
- Supplement kaynakları `load_canonical_source_catalog()` içine merge edildi; böylece metadata-first selector article rows boş olsa bile supplement kaynaklarını görebiliyor.
- Slash-numbered identifiers (`2024/7`, `2019/12`) korunuyor.
- Supplement chunk metadata artık family-specific üretiliyor:
  - `cb_genelge`: Cumhurbaşkanlığı Genelgesi
  - `cb_karar`: Cumhurbaşkanı Kararı
  - `kanun`: Kanun
- Exact identifier bulunan metadata-first seçimlerinde `selected_source_keys` exact candidate setine daraltıldı; audit için tam candidate listesi korunuyor.
- CB_GENELGE document-level cevap seçimi sabit mobbing terimlerinden çıkarıldı; query terim/2-gram/3-gram örtüşmesine dayalı genel clause scoring kullanılmaya başlandı.

## Resmi Kaynak Referansları

- `2024/7`: `https://www.resmigazete.gov.tr/eskiler/2024/05/20240517-5.pdf`
- `2019/12`: `https://www.resmigazete.gov.tr/eskiler/2019/07/20190706-10.pdf`
- `9903`: `https://www.resmigazete.gov.tr/eskiler/2025/05/20250530-2.pdf`
- `6102`: `https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=6102&MevzuatTertip=5`

Not: Resmi Gazete PDF uçları terminal/browser fetch sırasında timeout/403 davranışı gösterebiliyor. TTK m.595/m.598 metni mevcut local full-acquisition Mevzuat artifact'ından alınmıştır.

## Doğrulama

- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/rag/source_supplements.py api-gateway/src/rag/source_catalog.py api-gateway/src/routers/chat.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "source_supplement or cb_genelge_document_level_template or metadata_first_selector_prioritizes_exact_identifier"`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_source_catalog.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "metadata_lookup or metadata_first or source_supplement or cb_genelge_document_level_template"`

Sonuç: Yukarıdaki hedefli koşular geçti.

## Bilinen Kalan Risk

Tam `api-gateway/tests/test_chat_router.py` koşusunda Phase 18A-D öncesinden gelen 5 ayrı başarısızlık hâlâ ayrı risk olarak duruyor. Phase 18E commit kapsamı bu testleri hedeflemedi ve ilgili eski başarısızlıkları maskelemek için soru bazlı bypass eklenmedi.

## Phase 18F Giriş Notu

Phase 18F tam benchmark koşusunda özellikle şu metrikler izlenecek:

- `corpus_materialization_required_count`
- `CB_GENELGE pass`
- `source-key v2 collision`
- `wrong_document`
- `hallucinated_identifier`
