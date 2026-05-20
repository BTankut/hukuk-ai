# FAZ 2B Official Implementation Plan

Tarih: 2026-03-23

Referans:
- [FAZ2B-CUTOVER-READINESS-CLOSURE-VE-KALITE-KORUMALI-SERTLESTIRME-ENTEGRASYON-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2B-CUTOVER-READINESS-CLOSURE-VE-KALITE-KORUMALI-SERTLESTIRME-ENTEGRASYON-TALIMATI-2026-03-23.md)
- [faz2b-rc-freeze-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-rc-freeze-2026-03-23.md)

## Yürütme İlkesi

Bu plan yalnız resmi planner talimatını uygular. Daha önce resmi planner dışında açılmış `FAZ2B/FAZ2C` işleri steering kaynağı değildir; yalnız teknik yeniden kullanım yüzeyi olarak ele alınacaktır.

## Sabitler

- `RC-A`: kalite ankrajı
- `RC-B`: acceptance-only hardening branch
- `RC-C`: `RC-A + canonical citation normalization + delivery-controller v2 + release controls`
- model, adapter, retrieval, reranker, corpus ve source-locking mantığı değiştirilmeyecek

## Uygulama Sırası

1. `WP-1`: RC freeze ve manifest sözleşmesi
2. `WP-2`: RC-A vs RC-B regresyon ayrıştırması
3. `WP-3`: delivery-controller v2
4. `WP-4`: RC-C family-level quality-preserving eval
5. `WP-5`: must-close release controls
6. `WP-6`: narrow pilot cutover paketi ve rehearsal
7. `WP-7`: resmi steering raporu

## Ajan Organizasyonu

- `Russell`:
  - resmi talimat ile eski unofficial 2B/2C yüzeyleri arasındaki çakışmayı ayırır
  - dış API `blocked` sızıntısı ve minimal patch yüzeyini denetler
- `Bohr`:
  - `chat.py` / `faz2a_hardening.py` seam haritasını çıkarır
  - retrieval/model stack’e dokunmadan deterministic controller v2 sınırını dar tutar
- `Sartre`:
  - family eval, manifest ve rapor artefact zincirini çıkarır
  - mevcut eval/report script’lerinin yeniden kullanımını haritalar

Kritik path kod değişiklikleri ana rollout tarafından yapılacaktır. Ajan çıktıları yalnızca bounded analysis ve audit girdisi olarak kullanılacaktır.

## Çatışma Çözüm Kuralı

- [FAZ2B-CUTOVER-READINESS-CLOSURE-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2B-CUTOVER-READINESS-CLOSURE-RAPORU-2026-03-23.md) ve [FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md) resmi karar yüzeyi değildir.
- Bu dosyalardaki release controls, session store, backup/restore ve monitoring script’leri ancak `WP-5/WP-6` sonrasında ve resmi gate kapanırsa yeniden kullanılabilir.

## Başarı Ölçütü

Bu planın başarı koşulu yalnız acceptance değildir. `WP-4` kalite kapısı kapanmadan:

- serving default değişmeyecek
- yeni cutover iddiası kurulmayacak
- planner dışı yeni faz açılmayacak

## Durum

- `WP-1`: hazır
- `WP-2`: hazır
- `WP-3`: aktif
- `WP-4+`: `WP-3` sonucu bekliyor
