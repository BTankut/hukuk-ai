# FULL SOURCE INVENTORY VE PROVENANCE 2026-04-06

## Kapsam

Bu envanter, mevcut partial source paketlerini ve bunların yerine alınması gereken resmi full source origin'lerini aynı tabloda bağlar.

| source_class | current_raw_status | current_coverage_status | official_source_origin | official_source_locator | full_source_acquired | action_needed |
| --- | --- | --- | --- | --- | --- | --- |
| `cmk` | `data/primary_sources/raw/cmk` altında partial raw paket mevcut (`kanun_source.xml`, `article_index.jsonl`, `source_manifest.json`, `checksums.sha256`) | `PARTIAL_OR_SUSPICIOUS` | `mevzuat.gov.tr resmi mevzuat kaydı - Ceza Muhakemesi Kanunu (5271)` | `source_page_url=https://mevzuat.gov.tr/mevzuat?MevzuatNo=5271&MevzuatTur=1&MevzuatTertip=5` ; `detail_url=https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=5271&MevzuatTertip=5` | `false` | Official full source acquisition yapılacak; mevcut partial paket primary scope'tan çıkarılacak. |
| `hmk` | `data/primary_sources/raw/hmk` altında partial raw paket mevcut | `PARTIAL_OR_SUSPICIOUS` | `mevzuat.gov.tr resmi mevzuat kaydı - Hukuk Muhakemeleri Kanunu (6100)` | `source_page_url=https://mevzuat.gov.tr/mevzuat?MevzuatNo=6100&MevzuatTur=1&MevzuatTertip=5` ; `detail_url=https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=6100&MevzuatTertip=5` | `false` | Official full source acquisition yapılacak; mevcut partial paket primary scope'tan çıkarılacak. |
| `ik` | `data/primary_sources/raw/ik` altında partial raw paket mevcut | `PARTIAL_OR_SUSPICIOUS` | `mevzuat.gov.tr resmi mevzuat kaydı - İcra ve İflas Kanunu (2004 / tertip 3)` | `source_page_url=https://mevzuat.gov.tr/mevzuat?MevzuatNo=2004&MevzuatTur=1&MevzuatTertip=3` ; `detail_url=https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=2004&MevzuatTertip=3` | `false` | Official full source acquisition yapılacak; mevcut partial paket primary scope'tan çıkarılacak. |
| `tck` | `data/primary_sources/raw/tck` altında partial raw paket mevcut | `PARTIAL_OR_SUSPICIOUS` | `mevzuat.gov.tr resmi mevzuat kaydı - Türk Ceza Kanunu (5237)` | `source_page_url=https://mevzuat.gov.tr/mevzuat?MevzuatNo=5237&MevzuatTur=1&MevzuatTertip=5` ; `detail_url=https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=5237&MevzuatTertip=5` | `false` | Official full source acquisition yapılacak; mevcut partial paket primary scope'tan çıkarılacak. |
| `tmk_core_corpus` | `data/primary_sources/raw/tmk_core_corpus` altında çekirdek partial raw paket mevcut | `PARTIAL_OR_SUSPICIOUS` | `mevzuat.gov.tr resmi mevzuat kaydı - Türk Medeni Kanunu (4721)` | `source_page_url=https://mevzuat.gov.tr/mevzuat?MevzuatNo=4721&MevzuatTur=1&MevzuatTertip=5` ; `detail_url=https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=4721&MevzuatTertip=5` | `false` | `TMK core corpus` full TMK yerine kullanılamaz; official full source acquisition yapılacak. |
| `ttk` | `data/primary_sources/raw/ttk` altında partial raw paket mevcut | `PARTIAL_OR_SUSPICIOUS` | `mevzuat.gov.tr resmi mevzuat kaydı - Türk Ticaret Kanunu (6102)` | `source_page_url=https://mevzuat.gov.tr/mevzuat?MevzuatNo=6102&MevzuatTur=1&MevzuatTertip=5` ; `detail_url=https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=6102&MevzuatTertip=5` | `false` | Official full source acquisition yapılacak; mevcut partial paket primary scope'tan çıkarılacak. |

## Resmi Envanter Hükmü

- Mevcut altı source_class için de full source henüz acquire edilmiş değildir.
- Official provenance yalnız `mevzuat.gov.tr` resmi mevzuat origin'idir.
- Mevcut partial raw paketler yalnız audit/baseline amaçlı korunacaktır; full corpus iddiası için kullanılamaz.
