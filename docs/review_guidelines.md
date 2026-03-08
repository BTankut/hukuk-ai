# Hukuk AI - Avukat İnceleme Kılavuzu (Phase 2 Fine-Tuning)

Bu kılavuz, AI Hukuk Asistanı'nın fine-tuning (eğitim) sürecinde kullanılacak olan soru-cevap veri setlerinin avukatlar tarafından incelenmesi ve onaylanması sürecini tanımlar. Eğitime başlanabilmesi için incelenen verilerin **en az %80 oranında onay alması** (Quality Gate) zorunludur.

## 1. İnceleme Süreci (Workflow)

1. **Hazırlık:** Geliştirme ekibi, modelin ürettiği (veya sentetik olarak üretilmiş) taslak soru-cevap çiftlerini `data/review_sheets/` dizini altında CSV dosyaları olarak hazırlar. (Örn: `batch1_reviewer1.csv`)
2. **Atama:** Her paket (batch), birbirinden bağımsız olarak değerlendirilmesi için en az 2 avukata atanır.
3. **Değerlendirme:** Avukatlar kendilerine atanan CSV/Excel dosyasını açar ve her bir satırı (soru, bağlam, üretilen cevap) değerlendirir.
4. **Onay/Red/Düzeltme:** Avukat, kararlarını `lawyer_decision` sütununa girer ve gerekiyorsa `corrected_answer` sütununu doldurur.
5. **Toplama ve Ölçüm:** Doldurulan dosyalar geri toplanır. `scripts/calculate_approval_rate.py` aracıyla otomatik ölçüm yapılır. %80 barajı aşılırsa veriler eğitime dahil edilir.

## 2. Değerlendirme Kriterleri ve Kararlar

Her bir kayıt için aşağıdaki üç karardan **yalnızca biri** seçilmelidir (büyük harflerle yazılmalıdır):

- **APPROVE (Onaylandı):** Soru, verilen bağlam (context) dahilinde doğru ve eksiksiz yanıtlanmıştır. Format doğrudur (örn. `[Kaynak: TBK md. 49]` gibi referanslar mevcuttur). Yanıt, hukuki olarak kullanılabilir niteliktedir.
- **REVISE (Düzeltildi):** Yanıt genel olarak doğru yöndedir ancak ufak hatalar veya format eksiklikleri içermektedir. Avukat bu durumu düzeltip doğrusunu `corrected_answer` sütununa yazmıştır. (REVISE edilen kayıtlar, düzeltilmiş halleriyle eğitime dahil edilir ve "Onaylanmış" sayılır).
- **REJECT (Reddedildi):** Yanıt hukuki olarak tamamen yanlıştır, hallüsinasyon (uydurma) içermektedir veya verilen bağlamla alakası yoktur. Ufak bir düzeltme ile kurtarılamayacak kadar kötüdür.

### 2.1. İnceleme Sırasında Dikkat Edilecekler
- **Kaynak Doğruluğu:** Modelin gösterdiği kaynakların (Madde numaraları, kanun adları) bağlam metniyle örtüşüp örtüşmediğine mutlaka dikkat edilmelidir.
- **Format:** Fine-tuning hedeflerinden biri modelin `[Kaynak: X]` formatını öğrenmesidir. Eğer format eksikse ve cevap doğruysa, kararı **REVISE** yapıp `corrected_answer` kısmında formatı ekleyerek düzeltiniz.

## 3. İnceleme Dosyası (CSV) Sütunları

Yeni paketlerde satır başına triage için ek metadata sütunları bulunur. Avukatların odaklanması gereken zorunlu alanlar yine `lawyer_decision`, gerektiğinde `corrected_answer` ve `reviewer_name` sütunlarıdır.

| Sütun Adı | Açıklama | Avukat Dolduracak mı? |
| :--- | :--- | :--- |
| `batch_item_no` | Paket içi sıra numarası. Değiştirmeyiniz. | Hayır |
| `candidate_id` | Aday kaydın benzersiz kimliği. Değiştirmeyiniz. | Hayır |
| `question_id` | Soru kimliği (örn. TBK-044). | Hayır |
| `difficulty` | Zorluk etiketi (`easy`, `medium`, `hard`). Segment bazlı kalite analizi için kullanılır. | Hayır |
| `category` | Hukuki konu kategorisi (örn. `tbk_genel`, `tbk_kira`). | Hayır |
| `source_file` | Cevabın geldiği evaluation raporu. | Hayır |
| `source_record_id` | Kaynak rapordaki kayıt kimliği. | Hayır |
| `split` | Adayın extraction split'i (`train_pending_review` / `heldout_pending_review`). | Hayır |
| `refusal_expected` | Soruda refusal beklenip beklenmediği sinyali. | Hayır |
| `is_hallucination` | Kaynak metadata'daki hallüsinasyon işareti. | Hayır |
| `has_citation` | Cevapta kaynak atfı bulunduğu sinyali. | Hayır |
| `response_time_ms` | Üretim sırasında ölçülen yanıt süresi. | Hayır |
| `question` | Kullanıcının sorduğu hukuki soru. | Hayır |
| `context` | Sistemin soruya cevap bulmak için getirdiği hukuki mevzuat/içtihat metni. | Hayır |
| `generated_answer` | AI tarafından üretilmiş taslak cevap. | Hayır |
| `lawyer_decision` | Avukat kararı: `APPROVE`, `REVISE` veya `REJECT`. | **Evet** |
| `lawyer_comment` | Kararınızın kısa nedeni (özellikle REJECT durumunda faydalıdır). | Opsiyonel |
| `corrected_answer` | Karar `REVISE` ise, cevabın sizin tarafınızdan düzeltilmiş hali. | **Evet (Karar REVISE ise)** |
| `reviewer_name` | İncelemeyi yapan avukatın ad ve soyadı (veya rumuzu). | **Evet** |

## 4. Onay Oranı (Quality Gate) Hesaplaması

Sistem onay oranını aşağıdaki formülle hesaplar:
`Onay Oranı = (APPROVE Sayısı + REVISE Sayısı) / Toplam İncelenen Kayıt Sayısı`

Eğer bu oran **>= %80** olursa, paket "Geçti" kabul edilir ve SFT (Supervised Fine-Tuning) eğitim setine (`data/finetune/sft/`) JSONL formatında otomatik dönüştürülür. Oran %80'in altındaysa, reddedilen kayıtlar üzerinde geliştirme ekibi tarafından yeni prompt/context düzeltmeleri yapılır ve paket yeniden incelemeye gönderilir.
