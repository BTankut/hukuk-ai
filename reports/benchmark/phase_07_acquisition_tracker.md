# Phase 7A Acquisition Tracker

- input: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/phase_06_corpus_acquisition_targets.csv`
- tracker_rows: 18
- missing_owner_rows: 0
- missing_action_rows: 0

## Family Counts
- YONETMELIK: 5
- CB_YONETMELIK: 4
- CB_KARAR: 3
- KANUN: 2
- KKY: 2
- UY: 1
- TUZUK: 1

## Action Counts
- source_acquisition_or_reindex: 12
- index_visibility_or_metadata_filter_repair: 6

## Initial Resolution Status
- pending_visibility_probe: 18

## Tracker Rows
- CBKAR-01: family=CB_KARAR; identifier=3350; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=İthalat Rejimi Kararı (Karar Sayısı: 3350)
- CBKAR-05: family=CB_KARAR; identifier=32; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar
- CBKAR-08: family=CB_KARAR; identifier=9903; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903)
- CBY-01: family=CB_YONETMELIK; identifier=none; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmelik
- CBY-04: family=CB_YONETMELIK; identifier=none; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Devlet Arşiv Hizmetleri Hakkında Yönetmelik
- CBY-05: family=CB_YONETMELIK; identifier=2024/7; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği
- CBY-06: family=CB_YONETMELIK; identifier=11153; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği
- KANUN-06: family=KANUN; identifier=6102; action=index_visibility_or_metadata_filter_repair; status=pending_visibility_probe; title=6102 sayılı Türk Ticaret Kanunu
- KANUN-19: family=KANUN; identifier=7201; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=7201 sayılı Tebligat Kanunu
- YON-01: family=YONETMELIK; identifier=7201; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Elektronik Tebligat Yönetmeliği
- YON-02: family=YONETMELIK; identifier=6502; action=index_visibility_or_metadata_filter_repair; status=pending_visibility_probe; title=Mesafeli Sözleşmeler Yönetmeliği
- YON-05: family=YONETMELIK; identifier=3194; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Planlı Alanlar İmar Yönetmeliği
- YON-06: family=YONETMELIK; identifier=2004; action=index_visibility_or_metadata_filter_repair; status=pending_visibility_probe; title=Konkordato Komiserliği Yönetmeliği
- YON-08: family=YONETMELIK; identifier=none; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=Yükseköğretim Kurumlarında Ön Lisans ve Lisans Düzeyindeki Programlar Arasında Geçiş, Çift Anadal, Yan Dal ile Kurumlar 
- UY-07: family=UY; identifier=2547; action=source_acquisition_or_reindex; status=pending_visibility_probe; title=ilgili üniversitenin Ön Lisans ve Lisans Eğitim-Öğretim ve Sınav Yönetmeliği
- TUZUK-05: family=TUZUK; identifier=none; action=index_visibility_or_metadata_filter_repair; status=pending_visibility_probe; title=ilgili yürürlükteki tüzük hükümleri
- KKY-02: family=KKY; identifier=none; action=index_visibility_or_metadata_filter_repair; status=pending_visibility_probe; title=Bankalarca Kullanılacak Uzaktan Kimlik Tespiti Yöntemlerine ve Elektronik Ortamda Sözleşme İlişkisinin Kurulmasına İlişk
- KKY-10: family=KKY; identifier=5809; action=index_visibility_or_metadata_filter_repair; status=pending_visibility_probe; title=Elektronik Haberleşme Sektöründe Tüketici Hakları Yönetmeliği

## Interpretation
- This file is a control table only; live Milvus/index visibility is measured by the Phase 7A probe artifact.
- `pending_visibility_probe` means the item has not yet been proven available, absent, or retrieval-visible in the current serving collection.
- Every open row must keep a non-empty owner, action type, and next action before Phase 7B work starts.
