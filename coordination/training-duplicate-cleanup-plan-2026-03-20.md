# Training Duplicate Cleanup Plan

Date: 2026-03-20
Scope: post-gate cleanup strategy
Decision: `inventory-first`, no blind auto-delete

## Inventory Özeti

Kaynak: `coordination/training-duplicate-inventory-2026-03-20.json`

- duplicate question groups: `24`
- duplicate excess rows: `116`
- `all_rows_unique_outputs`: `13`
- `mixed_repeat_and_variant_outputs`: `11`
- `exact_answer_repeats_only`: `0`

## Sonuç

Bu veri yapısında güvenli bir "aynı satırı sil" temizliği yok. Duplicate grupların hiçbiri salt exact-answer tekrarından oluşmuyor.

Yani sonraki iş:

- blind dedupe değil
- cluster bazlı canonicalization
- gerekirse lawyer-reviewed merge kararı

## Temizleme Sırası

1. En yüksek hacimli mixed gruplar
2. En yüksek hacimli all-unique gruplar
3. Düşük hacimli kuyruk gruplar

İlk odak:

- `10x / 4 outputs` tahliye sorusu
- `9x / 9 outputs` genel zamanaşımı sorusu
- `8x / 8 outputs` faiz oranı sorusu
- `8x / 7 outputs` aşırı ifa güçlüğü sorusu
- `8x / 7 outputs` vekâlet özen/hesap verme sorusu

## Uygulama Notu

Bir sonraki güvenli milestone, bu cluster'ları review packet olarak dışa vurmak ve her cluster için canonical answer seçimini izlenebilir hale getirmektir. `final_train.jsonl` bu karar verilmeden otomatik yeniden yazılmayacaktır.
