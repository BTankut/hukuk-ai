# Cross-Law & Eser Sözleşmesi — Hata Analizi ve Düzeltme Planı

**Tarih:** 2026-03-15  
**Eval:** `eval_v2_post_refusal_fix_20260315_202250.json`  
**Hedef:** correct_source_rate 66.5% → 70% (gap: 3.5pp ≈ 3.3 soru tam skor)

Faz 1'de tek kalan engel correct_source_rate. Bu rapor iki yüksek-hallusinasyon kategorisini arkeolojik düzeyde inceler:
- `tmk_cross_law` (n=10): correct_src=36.7%, hal=40%  
- `tbk_eser` (n=5): correct_src=40.0%, hal=40%

---

## BÖLÜM 1: tbk_eser (n=5)

### Per-Soru Durum

| Soru | correct_src | hal | refusal | Retrieval: beklenen/bulunan | Sorun tipi |
|------|------------|-----|---------|---------------------------|------------|
| TBK-084 | 0.50 | ❌ | ✅ (yanlış) | m.471 ✓, **m.474 ✗** (3 aday) | Retrieval miss + false refusal |
| TBK-085 | 0.50 | ❌ | ❌ | m.477 ✓, m.476 ✓ (her ikisi bulundu) | Citation drift |
| TBK-086 | 1.00 | ✅ | ❌ | m.478 ✓ | ✅ GEÇTI |
| TBK-087 | 0.00 | ✅ | ❌ | **m.484 ✓ rank-1** (skor 0.655) | Citation drift (kritis) |
| TBK-088 | 0.00 | ✅ | ❌ | **m.486 ✓ rank-1** (skor 0.5625) | Eval data hatası |

### Kök Neden Analizi

#### TBK-087 — En Kritik: Citation Drift, Right Article Retrieved

**Soru:** "TBK m.484 uyarınca işsahibi eser sözleşmesini herhangi bir nedenle feshedebilir mi?"  
**Beklenen:** `TBK m.484` (tek kaynak)  
**Retrieval:** m.484 rank-1 (0.655), m.483 rank-2 (0.557), m.485 rank-3 (0.557)  
**Alınan:** `TBK m.483, TBK m.485`  

Model, cevap metninde m.484'ün içeriğini **doğru açıkladı** (işsahibinin feshi, tamamlanmamış eser, zarar giderme yükümlülüğü). Ancak son cümlede "diğer haller TBK m.483 ve m.485'e girer" derken **sadece bu yan makaleleri `[Kaynak: ...]` ile cite etti**, m.484'ü etiketsiz bıraktı.

Bu saf bir LLM citation davranışı sorunudur: model "x hakkında m.484 şöyle der, yan haller için m.483/485'e bakılır [Kaynak: m.483], [Kaynak: m.485]" yapısı kurdu. Retrieval hiç sorunlu değil.

---

#### TBK-088 — Eval Data Hatası

**Soru:** "TBK m.486 kapsamında yüklenicinin işi alt yükleniciye devredebilmesinin koşulları..."  
**Beklenen:** `TBK m.486`  
**Retrieval:** m.486 rank-1  
**Modelin okuyuşu:** "TBK m.486: Yüklenicinin **ölümü** ve işsahibinin tamamlanan kısmı kabul etme hakkı."  

Model m.486'yı doğru okumuştur. TBK 6098 sayılı Kanun'da m.486 gerçekten **"Yüklenicinin ölümü ve ehliyetsizliği"** başlığını taşır, alt yükleniciye devir hükmünü değil. Alt yükleniciye devir TBK m.471 (2. fıkra) kapsamındadır. 

**Sonuç: expected_sources yanlış.** Test verisi düzeltilmeli.

---

#### TBK-084 — Retrieval Miss + False Refusal

**Soru:** "TBK m.471 kapsamında yüklenicinin eseri teslim borcu... m.474 bekleniyor"  
**Retrieval:** Yalnızca 3 aday (m.471, m.470, m.472). m.474 hiç gelmedi.  

tbk_eser kategorisi için aday sayısı **sadece 3** — tmk_cross_law için 20'ye kıyasla dramatik fark. m.474 (hasar ve teslim ilişkisi) semantik olarak m.471'den uzak olduğu için 3 adaylık kısa listede yer bulamıyor.

Ek sorun: Model m.471'i buldu, cevabın büyük bölümünü yazdı, sonra m.474 hakkında "kaynaklarda bulunmamaktadır" diyerek refusal tetikledi. Bu refusal yanlış çünkü `refusal_expected=False`.

---

#### TBK-085 — Eval Data Şüphesi

**Soru:** "TBK m.477 uyarınca eserdeki gizli ayıpları geç bildiren işsahibinin durumu..."  
**Beklenen:** `TBK m.477 + TBK m.476`  
**Retrieval:** m.477 rank-1 ✓, m.476 rank-2 ✓ (her ikisi bağlamda)  
**Alınan:** Sadece m.477  

Model m.476'yı görmezden geldi. Ancak soru yalnızca "gizli ayıp + geç bildirim" soruyor — bu tam olarak m.477'nin konusu. m.476 genel ayıp muayenesi hakkında. m.476'nın beklenen kaynak olması **kısmen hatalı olabilir**: soru m.476'yı zorunlu kılmıyor.

**Durum:** Eval data gözden geçirilmeli. m.476 expected_sources'tan çıkarılırsa +0.5 puan.

---

### tbk_eser Özet: Ne Oldu, Ne Değil

| Tip | Sorular | Etki |
|-----|---------|------|
| Eval data hatası | TBK-088 | +1.0 puan (düzeltme ile) |
| Citation drift | TBK-087 | +1.0 puan (prompt ile) |
| Citation drift | TBK-085 | Şüpheli (eval data gözden geçir) |
| Retrieval miss (3 aday) | TBK-084 | +0.5 puan (aday sayısı artışıyla) |

---

## BÖLÜM 2: tmk_cross_law (n=10)

### Per-Soru Durum

| Soru | correct_src | hal | TBK/TMK in ret | Expected retrieved | Sorun tipi |
|------|------------|-----|----------------|-------------------|------------|
| TMK-CL-001 | 1.00 | ❌ | 18/2 | 2/2 ✓ | ✅ GEÇTI |
| TMK-CL-002 | 0.50 | ❌ | 5/15 | 2/2 ✓ (m.185 rank-9) | Citation drift |
| TMK-CL-003 | 0.33 | ❌ | 5/15 | 2/3 (TBK m.299 ✗) | Retrieval miss + citation drift |
| TMK-CL-004 | 1.00 | ❌ | 14/6 | 2/2 ✓ | ✅ GEÇTI |
| TMK-CL-005 | 0.00 | ✅ | 14/6 | **0/2** (her ikisi ✗) | Tam retrieval miss |
| TMK-CL-006 | 0.33 | ❌ | 9/11 | 1/3 (m.27 ✗, m.1023 ✗) | Retrieval miss × 2 |
| TMK-CL-007 | 0.50 | ❌ | 5/15 | 2/2 ✓ (m.49 rank-20) | Citation drift (prefix hatası) |
| TMK-CL-008 | 0.00 | ✅ | 8/12 | 1/2 (TBK m.207 ✗) | Retrieval miss + citation drift |
| TMK-CL-009 | 0.00 | ✅ | 4/16 | 1/2 (TBK m.323 ✗) | Retrieval miss |
| TMK-CL-010 | 0.00 | ✅ | **0**/20 | 1/3 (TBK m.386 ✗, TMK m.223 ✗) | TBK tamamen yok |

### Kök Neden Analizi

#### Birincil Sorun: TBK Retrieval Körlüğü

Sorular TMK-heavy kavramlar içerdiğinde (boşanma, mal rejimi, aile konutu, paylı mülkiyet), embedding uzayı TMK makalelerine yöneliyor ve beklenen TBK makaleleri retrieval'a girmiyor:

| Soru | TBK (expected) | Neden retrieval miss? |
|------|---------------|----------------------|
| CL-003 | TBK m.299 | Sorgu "paylı mülkiyet kiraya verme" → TMK odaklı |
| CL-005 | TBK m.299 | Sorgu "malik olmayan kişi + kiracı koruması" → semantik karışıklık |
| CL-006 | TBK m.27 | Sorgu "aile konutu şerhi + alıcı" → TMK aile hukuku baskın |
| CL-008 | TBK m.207 | Sorgu "önalım hakkı + paylı mülkiyet" → TMK mülkiyet baskın |
| CL-009 | TBK m.323 | Sorgu "boşanma + kira devri" → m.349 (ölüm/fesih) geldi, m.323 (devir) gelmedi |
| CL-010 | TBK m.386 | Sorgu "mal rejimi + borç" → %100 TMK mal rejimi makaleleri |

**CL-010 uç vaka:** 20 adayın tamamı TMK. TBK m.386 (ödünç sözleşmesi adi) semantik olarak "eşler arasında mal rejimi" sorgusuna hiç karışmıyor.

#### İkincil Sorun: Citation Drift (Beklenen Makale Bağlamda Var, Model Cite Etmiyor)

**TMK-CL-007 — Prefix Hallusinasyonu:**  
- TBK m.49 bağlamda var ama rank-20 (en sonda)
- Model içeriği doğru bildi, fakat **"TMK m.49"** yazdı (yanlış prefix)
- TBK m.49 Türk Borçlar Kanunu haksız fiil → TMK m.49 diye bir madde yok
- Scoring sistemi prefix'i doğru check ediyor, yanlış olarak işaretlendi
- Context window'un sonundaki makalelerde prefix karışımı riski yüksek

**TMK-CL-002 — Rank-9 Makale Ignore:**  
- TMK m.185 (aile birliğinin korunması) bağlamda rank-9 var
- Model TBK m.584 (kefalet) + TBK m.603 cite etti, TMK m.185'i atladı
- 20 adaylık listede rank-9 hâlâ görece erişilebilir, bu saf citation drift

**TMK-CL-008 — Rank-1 Makale Ignore:**  
- TMK m.732 bağlamda rank-1 (en üstte!) 
- Model TBK m.240, m.237, m.241, TMK m.733, m.734 cite etti — m.732 yok
- Sorgu "paylı mülkiyet önalım" → TBK satış hükümlerine ve TMK komşu makalelere kayma
- Bağlamda olduğu halde rank-1 makaleyi görmezden geliyor — ciddi citation drift

#### Üçüncül Sorun: Eval Data Şüpheleri

**TMK-CL-005:** Expected `TBK m.299` (taşınmaz satış vaadi) + `TMK m.683` (eşya hukuku mülkiyet tanımı).  
Soru: "Malik olmayan kişinin taşınmazı kiraya vermesi + kiracı koruması."  
Bu soru için TBK m.299 satış vaadine neden referans gösterilmiş? Daha uygun kaynaklar TBK m.301 (kira sözleşmesi) + TMK m.1007 (tapu sicili) olabilir. Eval data gözden geçirilmeli.

**TMK-CL-009:** Expected `TBK m.323` (kiracının devretme hakkı).  
Retrieval, "boşanma + aile konutu kira devri" sorgusunda TBK m.349 getirdi (kiracının ölümü → aile konutu). Bu kira hükümleri kategorisi içinde mantıklı bir konfüzyon. Ancak "boşanma" bağlamında TBK m.349 de gerçekten ilgili olabilir — expected_sources'ın yalnızca m.323 göstermesi tamamlanmamış olabilir.

---

## BÖLÜM 3: Fark Hesabı ve Hedef

Mevcut durum:
- Toplam puan: 62.50 / 95 = 65.79% (sorgu: 66.5%... hesap 65.79% gösteriyor, JSON summary 66.49%)
- Hedef: 70% = 66.5 puan
- Fark: ~4.0 puan = ~4 soruyu tam düzeltmek veya eşdeğer kısmi iyileştirmeler

Her +1.0 puan = **+1.05pp** sistem genelinde.

---

## BÖLÜM 4: Öneriler (Öncelik Sırasına Göre)

### P1: Eval Data Düzeltmeleri (Kod yok, Hızlı, Yüksek ROI)

**EV-1: TBK-088 expected_sources düzeltme** *(Etki: +1.0 puan / +1.05pp)*

TBK m.486 "Yüklenicinin ölümü ve ehliyetsizliği" başlığını taşır. Alt yükleniciye devir TBK m.471/2. fıkrasında (veya yoksa genel borçlar hükümleri). Test sorusu TBK m.486 olarak tanımlıyor ama bu maddede o içerik yok. İki seçenek:
- Soruyu TBK m.486'nın gerçek içeriğine (ölüm) göre yeniden yaz
- Soruyu TBK m.471 fıkra 2'ye atıf yapacak şekilde düzelt

**EV-2: TBK-085 expected_sources kontrolü** *(Etki: +0.5 puan / +0.53pp)*

"Gizli ayıpları geç bildirme" sorusu için TBK m.476 (genel muayene) zorunlu mu? Hukuk eksperi doğrulaması: sadece m.477 yeterli ise expected_sources'tan m.476 çıkar.

**EV-3: TMK-CL-005 expected_sources kontrolü** *(Etki: değişken)*

"Malik olmayan kişinin kiraya vermesi + kiracı koruması" için TBK m.299 (taşınmaz satış vaadi) gerçekten ilgili makale mi? Muhtemelen hayır. Daha doğru kaynak: TBK m.301-302 + TMK m.1007/1023 aralığı.

**EV-4: TMK-CL-009 expected_sources tamamlama** *(Etki: +0.5 puan)*

"Boşanma + aile konutu + kira devri" için yalnızca TBK m.323 beklenmesi eksik. TBK m.349 (aile konutu kirasının sona erdirilmesi) da ilgili — expected_sources'a ekle.

---

### P2: Prompt Engineering (Kod değişikliği yok, Hızlı)

**PE-1: Explicit Citation Grounding — Asked Article** *(Etki: +1.0 puan / TBK-087)*

TBK-087'de model m.484'ün içeriğini biliyor ama cite etmiyor. Sistem prompt'una ekle:

```
Soru belirli bir maddeye atıfta bulunuyorsa (örn. "TBK m.484 uyarınca") ve bu madde kaynaklarda mevcutsa, cevabında o maddeyi mutlaka [Kaynak: ...] ile cite et. Yan maddeleri sadece tamamlayıcı olarak ekle.
```

**PE-2: Law Prefix Doğruluğu** *(Etki: +0.5 puan / TMK-CL-007)*

TBK m.49 bağlamda olduğu halde model "TMK m.49" yazdı (yanlış prefix). Sistem prompt'una:

```
Kaynaklarda TBK maddelerine 'TBK m.XXX', TMK maddelerine 'TMK m.TMX' olarak atıfta bulun. Kanun prefixini asla karıştırma.
```

**PE-3: Cross-Law Citation Zorunluluğu** *(Etki: +0.5 puan / TMK-CL-002)*

TMK m.185 bağlamda rank-9'da bulunuyordu fakat ignore edildi. Cross-law sorularda:

```
Soru hem TBK hem TMK hükümlerine değiniyorsa, cevabında her iki kanundan da kaynak göster. Yalnızca bir kanunu cite etmek yetersizdir.
```

**PE-4: Context Tail Grounding** *(Etki: +0.5 puan / TMK-CL-008)*

TMK m.732 rank-1'de var ama model m.733, m.734 cite etti. Bu, "soruda adı geçen kavrama en yakın makaleyi atla, komşu makaleleri al" davranışı. Yukarıdaki PE-1 bunu da kısmen çözebilir.

---

### P3: Retrieval Düzeltmeleri (Kod değişikliği, Orta Efor)

**RE-1: tbk_eser Aday Sayısını Artır** *(Etki: +0.5-1.0 puan)*

tbk_eser sorularına sadece 3 aday geliyor (vs. 20 cross-law). Bu neden? Retrieval config'inde kategori bazlı limit varsa artırılmalı. En az 10 aday olsa m.474 TBK-084'e girebilir.

Kontrol: `retriever/config.py` veya retrieval_profile='shadow' parametrelerinde `top_k` ya da `max_candidates` tbk_eser için neden 3?

**RE-2: Cross-Law Parallel Query (Split Retrieval)** *(Etki: +2-3 puan)*

TMK-CL-010'da TBK adayı sıfır, CL-009'da 4, CL-008'de 8. "Mal rejimi + borç" gibi TMK-heavy sorgularda TBK retrieval tamamen bastırılıyor.

Çözüm: `query_classifier` CROSS_LAW döndürdüğünde iki paralel sorgu yap:
- Sorgu A: Orijinal + `law_filter=TBK`
- Sorgu B: Orijinal + `law_filter=TMK`
- Her birinden top-k/2 al, birleştir

Bu CL-003, CL-006, CL-008, CL-009, CL-010'u etkileyebilir → potansiyel +2-3 puan.

**RE-3: Article-ID Force-Include** *(Etki: +1-2 puan)*

Sorgu metni açık madde numarası içerdiğinde (örn. "TBK m.323"), o maddeyi semantik skora bakılmaksızın context'e ekle. Özellikle:
- CL-009: "TBK m.323" sorgu metninde var ama retrieval getirmedi
- Bu trivial bir retrieval override: query_parser madde regex'lerini parse etsin, force-add etsin

---

## BÖLÜM 5: Kümülatif Etki Tahmini

Aşağıdaki fixler **sırasıyla** uygulandığında beklenen kümülatif etki:

| # | Fix | Tip | +Puan | Kümülatif Rate |
|---|-----|-----|-------|----------------|
| EV-1 | TBK-088 expected_sources düzelt | Eval data | +1.00 | 67.5% |
| PE-1 | Citation grounding (asked article) | Prompt | +1.00 | 68.6% |
| PE-2 | Law prefix doğruluğu | Prompt | +0.50 | 69.1% |
| PE-3 | Cross-law citation zorunluluğu | Prompt | +0.50 | 69.6% |
| EV-2 | TBK-085 m.476 beklenti kontrolü | Eval data | +0.50 | 70.1% ✅ |
| RE-1 | tbk_eser aday sayısı artışı | Retrieval | +0.50 | 70.6% |
| RE-3 | Article-ID force-include | Retrieval | +1.00 | 71.7% |
| RE-2 | Parallel cross-law retrieval | Retrieval | +2.00 | 73.8% |

**Threshold geçiş noktası:** EV-1 + PE-1 + PE-2 + PE-3 + EV-2 kombinasyonu (~70.1%)  
Bu kombinasyon: 2 eval data düzeltmesi + 3 sistem prompt eklentisi. Kod değişikliği yok.

---

## BÖLÜM 6: Mevcut Analizle Örtüşme (v2-failure-analysis-20260315.md)

Önceki rapordaki bulgular şimdi doğrulandı ve rafine edildi:

| Bulgu | Önceki Rapor | Bu Rapor |
|-------|-------------|----------|
| tmk_cross_law correct_src | 40% | 36.7% (daha güncel eval) |
| tbk_eser yoktu | Listede yok | Yeni kategori — eklendi |
| Cause A: Semantic mismatch | ✓ Doğrulandı | Detaylı: 6 soruda TBK miss |
| Cause B: Adjacent hallucination | ✓ Doğrulandı | CL-008 m.732 vs m.733/734 |
| Fix önerisi: Parallel retrieval | ✓ Doğrulandı | RE-2 olarak önceliklendirildi |
| TBK-088 eval data hatası | **Yoktu** | YENİ: kritik düzeltme |
| TBK-087 citation drift | **Yoktu** | YENİ: PE-1 ile çözülür |
| tbk_eser candidate_count=3 | **Yoktu** | YENİ: RE-1 gerekli |

---

## BÖLÜM 7: Acil Eylem Listesi (Öncelikli)

1. **[Hızlı]** TBK-088 sorusunu düzelt: TBK m.486'nın gerçek içeriğine (yüklenicinin ölümü) uygun yeniden yaz veya expected_sources'u güncelle. → +1.05pp garanti
2. **[Hızlı]** Sistem prompt'una PE-1 + PE-2 + PE-3 ekle. → +1.5pp beklenen
3. **[Hızlı]** TBK-085 için m.476 gerekliliğini hukuki olarak doğrula. → +0.53pp potansiyel
4. **[Orta]** tbk_eser için neden sadece 3 aday geldiğini araştır; retrieval config'ini kontrol et. → +0.53pp
5. **[Orta]** RE-3 (article-ID force-include): query metnindeki madde numaralarını parse et. → +1.05pp
6. **[Uzun Vade]** RE-2 (parallel cross-law retrieval): tmk_cross_law için kalıcı çözüm. → +2.1pp

**Faz 1 geçiş için minimum:** Adım 1+2+3 yeterli (koşullu) veya 1+2+4.

---

*Subagent: hukuk-ai-cross-law-eser-debug | 2026-03-15*
