# Eval50 & Verification Calibration Raporu (2026-03-08)

## 1. Dosya Değişiklikleri
- `configs/evaluation/test_questions.json`: Soru seti 20 sorudan 50 soruya çıkarıldı. Yeni sorular TBK (Satış, Eser, Kefalet) ve TMK (Eşya, Aile) özelinde genişletildi. TMK soruları "YİM hazırlık" kapsamında değerlendirilerek uygun `refusal_expected` ayarlarına sahip oldu.
- `evaluation/metrics.py`: LLM'nin gerçek red (refusal) yanıtlarıyla Verification Engine kalibrasyonu yapıldı. "bilgi bulunmamaktadır", "yanıtlanamaz", "yer almamaktadır" gibi gerçek yanıtlarda rastlanan ifadeler `REFUSAL_PATTERNS` içine eklendi.
- `evaluation/run_eval.sh`: Bash script üzerindeki `$MOCK_MODE || true` şeklindeki syntax hatası düzeltildi, böylece `eval_runner.py`'nin düzgün çalışması sağlandı.

## 2. Soru Seti Büyüklüğü & Kapsamı
- **Önceki:** 20 Soru (Sadece TBK pilot).
- **Yeni:** 50 Soru.
- **Kapsam:** TBK (Genel, Kira, Haksız Fiil, Hizmet, Vekalet, Satış, Eser, Kefalet) + TMK (Eşya, Aile - Out of Scope / YİM hazırlık). "Faz 1 frozen scope" korunarak TMK için red (refusal) beklentisi işlendi.

## 3. Doğrulama Yöntemi (Mock Data Kuralına Uyum)
- **Soru Seti Genişletmesi:** Gerçek TBK ve TMK mevzuat maddeleri analiz edilerek hazırlandı.
- **Verification Kalibrasyonu:** Önceki canlı evaluation denemelerinden elde edilen *gerçek LLM çıktıları* incelenerek `metrics.py` güncellendi. Hiçbir mock veri üzerinden assumption yapılmadı.
- **Evaluation Koşusu:** İşlem tamamen canlı hat üzerinden çalıştırıldı. API Gateway, Milvus (gerçek embed edilmiş 657 vektor) ve DGX vLLM (Qwen3.5-35B-A3B-FP8) zinciri aktif olarak kullanıldı.
- Canlı Eval komutu: `./evaluation/run_eval.sh --live`

## 4. Önce/Sonra Metrikler (Faz 1 Kabul Kriterleri)
| Metrik | Eski (20 Soru - 20260308_reindex) | Yeni (50 Soru - 20260308_080601) | Hedef Threshold | Sonuç |
|--------|-----------------------------------|----------------------------------|-----------------|-------|
| Citation Rate | 90.0% | **88.0%** | ≥ 80% | ✅ GEÇTİ |
| Correct Source Rate | 80.17% | **77.1%** | ≥ 70% | ✅ GEÇTİ |
| Hallucination Rate | 5.0% | **8.0%** | ≤ 10% | ✅ GEÇTİ |
| Refusal Accuracy | 95.0% | **90.0%** | ≥ 80% | ✅ GEÇTİ |

*Not:* Genişletilen setle birlikte "zorluk" derecesi artan sorulardan ötürü metriklerde ufak dalgalanmalar görülmüş olsa da, hepsi "Faz 1 Go/No-Go" kabul sınırlarının üzerinde kalmıştır. ✅ **FAZ 1 KABULEDİLDİ**

## 5. Kalan Riskler ve Notlar
- **TMK Hallüsinasyon Riski:** Kapsam dışı beklenen bazi TMK sorularında, model `❌REFUSAL_MISS` vererek yanıt üretmeye veya halüsinasyon (`⚠️HAL`) oluşturmaya meyilli. İlerideki YİM fazında veya tam TMK indexlemesinde bu konuların detaylı kapsama alınması veya RAG filtresinin sistem promptunda daha agresif sınırlandırılması gerekebilir.
- **Doğru Kaynak Oranı:** %80'den %77'ye gerilemesi, daha karmaşık "Eser" veya "Satış" sözleşmesi sorularında retrieved bağlamın spesifik maddeleri getirmede (Top-5 Reranking esnasında) zorlandığını gösterebilir. Çözüm olarak Reranker eşikleri tekrar gözden geçirilebilir.
