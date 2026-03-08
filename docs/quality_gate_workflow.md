# Fine-Tuning Veri Kalite Kapısı (Quality Gate) İş Akışı

Bu belge, **Faz 2 P1 (Fine-Tuning)** aşamasına geçmeden önce uyulması zorunlu olan **Veri Kalite Kapısı (Quality Gate)** süreçlerini tanımlar. Amaç, hatalı veya düşük kaliteli verilerin modelin ince ayar sürecine (fine-tuning) sızarak halüsinasyonları artırmasını veya format tutarlılığını bozmasını önlemektir.

## 1. Veri Üretim Aşamaları

Fine-tuning (SFT) veri setini oluşturmak için kullanılan kaynaklar şunlardır:

*   **Aşama 1 (Otomatik):** `scripts/extract_qa_from_logs.py` betiği ile Faz 1'in üretim loglarından (gerçek kullanıcı soruları ve RAG çıktıları) potansiyel soru-cevap (QA) adaylarının çekilmesi.
*   **Aşama 2 (Sentetik Üretim):** Mevcut mevzuat üzerinden LLM yardımıyla oluşturulan soru-cevap çiftleri.

Bu aşamalardan elde edilen veriler doğrudan eğitime **SÖKÜLMEZ**. Sadece "aday (candidate)" olarak kabul edilirler.

## 2. Avukat İnceleme Süreci (Lawyer Review)

Tüm aday veriler (RAG çıktıları, dilekçe örnekleri, sentetik üretim) aşağıdaki adımlarla avukatlar tarafından incelenmek zorundadır:

1.  **Aday Veri Seti Havuzu:** Çıkarılan aday veriler bir ön izleme klasöründe tutulur (örneğin `data/finetune/sft/candidates/`).
2.  **İnceleme:** 2 ila 3 uzman avukat danışman, her bir QA çiftini manuel olarak inceler.
3.  **Düzeltme ve Format Uyumlaştırma:**
    *   Hukuki muhakeme hataları düzeltilir.
    *   Sıfır halüsinasyon ilkesine göre yanıtlar yeniden şekillendirilir.
    *   Tüm örneklerin `[Kaynak: ...]` formatına tam uyumu sağlanır (özellikle SFT için kritik).
4.  **Onay (Approval Tracking):**
    *   Onaylanan ve düzeltilen veriler nihai dosyalara aktarılır (`legal_qa.jsonl`, `rag_corrected.jsonl`, `petition_examples.jsonl`, `refusal_examples.jsonl`).
    *   Onay oranının **≥ %80** olması **zorunludur**.

## 3. Held-out Set (Eğitim Dışı Test Seti) Ayrımı

Eğitime (Fine-Tuning) başlanmadan önce, avukat onayından geçmiş olan veri setinin içinden rastgele seçilmiş ve en az **100 soru** içeren bir **Held-out Test Seti (Eğitim Dışı Test Seti)** ayrılmalıdır.

*   Bu veriler (`data/finetune/eval/held_out_test.jsonl` altına kaydedilir) kesinlikle eğitim (SFT) ya da hizalama (DPO) setlerine dahil edilmez.
*   Fine-tuning tamamlandıktan sonra, Base model ile Fine-tuned modelin "Catastrophic Forgetting" (yetenek yıkımı) yaşayıp yaşamadığını tespit etmek için kullanılacaktır.

## 4. Format Doğrulaması (Validation Tests)

Veriler avukat onayından ve ayrıştırmadan (held-out) geçtikten sonra, otomatik bir şema kontrolünden geçer:
*   Bütün jsonl dosyaları `scripts/validate_ft_data.py` ile denetlenir.
*   Örnek olarak, SFT verilerinin `instruction`, `input` ve `output` anahtarlarını barındırdığı, DPO verilerinin ise `prompt`, `chosen` ve `rejected` anahtarlarını içerdiği sistem üzerinden teyit edilir.

## 5. Gate Onayı (Go/No-Go)

**Eğitime Geçiş İçin Zorunlu Şartlar:**
- [ ] Minimum 1.000 adet onaylı SFT örneği oluşturuldu.
- [ ] Avukat danışman onay oranı ≥%80 seviyesinde.
- [ ] 100 soruluk Held-out test seti güvenli bir şekilde ayrıldı.
- [ ] `validate_ft_data.py` testleri başarıyla geçti.

**Sadece yukarıdaki 4 şart sağlandığında `dgxnode2` üzerindeki Fine-Tuning (Unsloth/LLaMA Factory) başlatılabilir.**
