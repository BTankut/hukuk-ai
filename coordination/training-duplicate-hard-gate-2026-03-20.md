# Training Duplicate Hard Gate

Date: 2026-03-20
Scope: training readiness hardening
Decision: `duplicate-question-excess = hard-fail`

## Bulgular

`data/finetune/sft/final_train.jsonl` üzerinde yapılan scan:

- total records: `923`
- unique questions: `807`
- duplicate question groups: `24`
- duplicate excess rows: `116`

En yoğun örnekler:

- `10x` `TBK'ya göre konut kiralarında kira sözleşmesinin sona erdirilmesi (tahliye) hangi koşullara bağlıdır?`
- `9x` `TBK'ya göre genel zamanaşımı süresi kaç yıldır ve bu süre hangi tarihten itibaren işlemeye başlar?`
- `8x` `Faiz oranı sözleşmede belirlenmemişse TBK'ya göre hangi faiz oranı uygulanır?`

## Karar

Bu durum artık yalnızca raporlanmayacak. Training readiness gate, duplicate question excess sıfır değilse `NOT READY` döndürecek.

## Uygulama

- `scripts/check_training_readiness.py` içine `Question duplicate check` eklendi
- yeni parametre: `--max-question-duplicate-excess`
- varsayılan: `0`

## Neden Hard Gate

- Aynı sorunun çok sayıda tekrar etmesi fine-tuning dengesini bozabilir
- Train set kalitesi ölçülmeden yapılan yeni run'lar karşılaştırılabilir olmaz
- Bu problem temizlenmeden training'e dönmek plan dışı bir hızlanma olur

## Temizleme Stratejisi

Bu milestone, duplicate'ları otomatik silmez. Önce gate konur, sonra temizleme yapılır.

Temizleme için düşük riskli sıra:

1. Duplicate soru gruplarını inventory olarak çıkar
2. Her grup için aynı cevabın exact tekrarlarını güvenle sil
3. Aynı soruya farklı lawyer-corrected cevaplar varsa merge / canonicalization kararı ver
4. Ancak sonra `final_train.jsonl` yeniden üret ve readiness gate'i tekrar çalıştır
