# FAZ 6 Official Implementation Plan

Tarih: 2026-03-23

Referans:
- [FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md)

## Hedef

FAZ 5 sonrasi tekrar eden citation/source-attribution kaybini yeni planner katmani eklemeden lokalize etmek, yalniz plannerin acik izin verdigi durumda `RC-G` onarimini acmak.

## Baglayici Kisitlar

- Tek resmi taban `RC-D`
- `RC-E` ve `RC-F` serving/default path'ten cikacak, diagnostic-only kalacak
- retrieval, reranker, model, prompt, corpus, query parser, source-locking degismeyecek
- decomposition kapanmadan yeni aday acilmayacak

## Is Paketi Sirasi

1. `WP-1`: `RC-D` freeze, manifest ve runtime rollback
2. `WP-2`: attribution trace schema v1
3. `WP-3`: attribution loss taxonomy v1
4. `WP-4`: exact tracked attribution pack
5. `WP-5`: `RC-D` decomposition replay
6. `WP-6`: reconciliation ve repair gate
7. Yalniz gate acilirse `RC-G` build, blocker invariance, family eval ve delta proof
8. Resmi FAZ 6 sonuc raporu

## Ajan Organizasyonu

- `Russell`: tracked frontier exact-count audit ve dominant omission frontier kontrolu
- `Bohr`: runtime seam audit, `RC-D` freeze ve diagnostic-only ayrimi
- `Sartre`: replay/builder reuse zinciri, `RC-G` offline eval builder minimizasyonu

## Basari Kriteri

- `trace_complete = 100%`
- reconciliation tam kapanacak
- dominant reason planner mapping ile tekil onarim yuzeyi gosterecek
- gate acilmazsa faz `NO-GO`, acilirse yalniz izinli `RC-G` degisiklik alani kullanilacak

## Plan Sonucu

Bu plan uygulanmis ve resmi FAZ 6 paketine donusturulmustur. Nihai karar, resmi sonuc raporunda yazilidir.
