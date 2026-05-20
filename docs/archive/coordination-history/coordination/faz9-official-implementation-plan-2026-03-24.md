# FAZ9 Official Implementation Plan

Tarih: 2026-03-24

Referans:
- [FAZ9-ROTASYON-RC-J-MODEL-VISIBLE-SURFACE-PARITY-FORENSICS-VE-CUTOVER-REOPEN-TALIMATI-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ9-ROTASYON-RC-J-MODEL-VISIBLE-SURFACE-PARITY-FORENSICS-VE-CUTOVER-REOPEN-TALIMATI-2026-03-24.md)
- [FAZ8-RELEASE-CONTROLS-PARITY-RESTORATION-VE-CUTOVER-REOPEN-RAPORU-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ8-RELEASE-CONTROLS-PARITY-RESTORATION-VE-CUTOVER-REOPEN-RAPORU-2026-03-24.md)

## Resmi Hedef

Bu fazin tek hedefi:

- `RC-G` answer-path hakikatini degistirmeden
- retained release-controls kapsamini koruyarak
- model-visible surface parity sapmasini stage-level lokalize etmek
- `RC-J` isimli parity-safe release candidate uretmek
- ve yalniz resmi karar zincirini yeniden acmaktir

Bu fazda yeni retrieval, training, corpus, prompt veya release-control kapsam genislemesi acilmayacak.

## Uygulama Stratejisi

- taban: `RC-G`
- diagnostic karsilastirma: `RC-I`
- yeni candidate: `RC-J`
- yontem: release-controls katmanlarini `RC-G` ustune bind ladder sirasi ile yeniden eklemek
- her adim: witness replay ile first-divergence kontrolu

## Work Packages

### WP-1

- `RC-G` refreeze
- `RC-I` diagnostic freeze
- `RC-J` build contract + manifest
- runtime lane contract

### WP-2

- 13-stage model-visible surface trace schema
- allowed primary reason taxonomy
- release-control bind ladder dokumani
- parity trace kodu ve testleri

### WP-3

- `TBK-005` witness forensic replay
- `RC-G` vs `RC-I` first-divergence localization
- unexplained `0`

### WP-4

- `RC-G` tabanindan bind ladder replay
- `L0..L6` witness hash zinciri
- ilk sapma ureten katmanin resmi atanmasi

### WP-5

- repair mapping
- `RC-J` build
- allowed diff surface disina cikmadan onarim

### WP-6

- witness pack A gate (`faz1-50-witness`)

### WP-7

- sentinel-12 gate

### WP-8

- full-family preprojection gate

### WP-9

- full-family output parity gate

### WP-10

- retained release-controls regression/retention gate

### WP-11

- cutover / rollback reopen only if parity ve retention kapandiysa

### WP-12

- resmi sonuc raporu

## Ajan Organizasyonu

- `Beauvoir`: mevcut witness artefact’larinda TBK-005 diff / visible mismatch / primary reason sinyal audit’i
- `Hilbert`: parity trace seam ve test coverage audit’i
- `Hooke`: FAZ8 reuse zinciri, builder/template haritasi
- ana ajan: uygulama, verification, lane koordinasyonu ve resmi artefact entegrasyonu

## Bu Turda Acilan Kod Yuzeyleri

- [config.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/config.py)
- [client.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/llm/client.py)
- [orchestrator.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/rag/orchestrator.py)
- [chat.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/routers/chat.py)
- [scripts/faz9](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz9)

## Ilk Kabul Cizgisi

Bu plan fazi ancak su durumda ileri tasinir:

- `RC-J` allowed diff surface resmi olarak dondurulmus olacak
- 13-stage trace zinciri unit testlerle sabitlenecek
- `TBK-005` icin first divergence unexplained birakilmayacak

Bu cizgi kapanmadan full-family parity veya cutover reopen acilmayacak.
