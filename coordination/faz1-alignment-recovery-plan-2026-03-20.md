# Faz 1 Hizalama ve Kontrollü Faz 2 Geçiş Planı

**Tarih:** 2026-03-20  
**Hazırlayan:** Codex koordinatör  
**Referanslar:** `docs/FAZ1-FINAL-RAPOR.md`, `docs/faz2-rev1-plan.md`, `coordination/status.md`, `docs/finetune/TRAINING_LOG.md`

---

## 1. Durum Tespiti

Repo bugün iki farklı gerçeği aynı anda taşıyor:

1. **Resmi baseline hâlâ Faz 1 / Phase 3 hardening kapanışı.**
   - Faz 1 kabul çizgisi: canlı, kaynaklı, mevzuat-first RAG sistemi.
   - Faz 1 kapanış referansı: `cf930ce` civarı Phase 3 hardening ve raporda belgelenen kabul metrikleri.

2. **Kod tabanı bunun üstünde kontrolsüz biçimde fine-tuning hattına ilerlemiş.**
   - `7225ae2..HEAD` aralığında büyük hacimli training/review artefact'ları eklenmiş.
   - `docs/finetune/TRAINING_LOG.md` eğitim v1'in yanlış veriyle başlatıldığını, v2'nin ise lawyer-reviewed veriyle doğrudan çalıştırıldığını söylüyor.
   - Ancak Faz 1 raporundaki ana öğrenimlerle uyumlu zorunlu geçiş kapıları net biçimde uygulanmamış:
     - küçük eval yerine zor setlerde tekrar ölçüm,
     - tek değişkenli deney disiplini,
     - retrieval/model ayrımının açık audit'i,
     - training öncesi veri ve değerlendirme kapılarının sabitlenmesi.

Sonuç: proje ilerlemiş, fakat **resmi baseline, deneysel eğitim hattı ve üretim için güvenilen kalite kapıları birbirine karışmış** durumda.

---

## 2. Ana Karar

Bu noktadan sonra çalışma şu ilkeye göre yürütülecek:

- **Training-first değil, gate-first ilerleme.**
- Yeni model eğitimi veya deploy kararı, Faz 1 raporundaki kalite disiplinini yeniden kurmadan alınmayacak.
- RAG baseline, eval altyapısı ve training hattı birbirinden net ayrılacak.

Bu, eğitim çalışmalarını tamamen reddetmek değildir. Anlamı şudur:

1. Önce ölçüm ve baseline tekrar güvenilir hale getirilecek.
2. Sonra Faz 2 P0 işleri kontrollü şekilde tamamlanacak.
3. Fine-tuning ancak açık kalite kapılarından sonra “hazır” sayılacak.

---

## 3. Çalışma İlkeleri

`docs/FAZ1-FINAL-RAPOR.md` ile uyumlu olarak aşağıdaki ilkeler zorunludur:

- **Tek değişken prensibi:** Aynı dalgada birden çok davranışsal değişiklik yapılmayacak.
- **Eval-before-claim:** Her önemli değişiklik 50q / 95q / 170q seviyelerinde izlenebilir olacak.
- **Retrieval audit önce:** Sorun retrieval mı model davranışı mı ayrıştırılmadan training'e kaçılmayacak.
- **Lawyer-reviewed veri önceliği:** Synthetic veya pending-review veri, açık etiketsiz şekilde “production-quality” kabul edilmeyecek.
- **Track ayrımı:** Üretim baseline ile deneysel LoRA hattı aynı başarı anlatısı altında raporlanmayacak.

---

## 4. Yürütme Planı

### Wave 0 — Baseline ve Training Freeze Disiplini

Amaç: resmi doğruluk çizgisini ve deneysel hattı birbirinden ayırmak.

Çıktılar:
- Faz 1 baseline referans commit ve metrik matrisi
- Training readiness checklist
- Hangi veri setinin hangi amaçla kullanılacağına dair kaynak-doğruluk tablosu
- “training running” bilgisinin tek başına ilerleme sayılmayacağına dair koordinasyon kaydı

Exit criteria:
- Baseline commit/metric referansı repo içinde tek anlamlı kaynak haline gelsin
- Training için zorunlu kapılar yazılı hale gelsin

### Wave 1 — Eval ve Ölçüm Katmanının Yeniden Sabitlenmesi

Amaç: metrikler tekrar güvenilir olmadan model/ürün kararları alınmamasını sağlamak.

Çıktılar:
- Faz 1 50q, Phase 3 95q ve Faz 2 170q setlerinin resmi rol tanımı
- Reproducible eval komut matrisi
- Training öncesi zorunlu değerlendirme listesi
- Baseline ile HEAD arasındaki ölçüm boşluklarının görünür kaydı

Exit criteria:
- Bir değişikliğin “iyileşme” sayılması için hangi eval setinde neyin geçmesi gerektiği net olsun

### Wave 2 — Faz 2 P0 İşlerinin Kontrollü Yürütülmesi

Amaç: raporda zaten Faz 2’ye devredilmiş ama eğitimle gölgelenmiş kritik işleri kapatmak.

Öncelik sırası:
1. Reranker gerçek A/B ve threshold sweep
2. Guardrails facts-only / latency kalibrasyonu
3. Retrieval kapsamı ve özellikle TMK / diğer kanun genişleme gereksiniminin netleştirilmesi

Exit criteria:
- Reranker için açık “enable / keep-off / rework” kararı
- Guardrails için kalite-latency kararı
- Retrieval genişleme gereksinimi training’den ayrı bir iş kolu olarak tanımlansın

### Wave 3 — Training Readiness Gate

Amaç: fine-tuning’i “çalıştı” seviyesinden “haklı ve denetlenebilir” seviyesine taşımak.

Zorunlu kontroller:
- dataset provenance
- held-out leakage kontrolü
- synthetic vs lawyer-reviewed ayrımı
- training config doğrulaması
- hedef kategori gerekçesi
- pre-train baseline eval kaydı
- post-train eval zorunluluğu

Exit criteria:
- Bu kapılar geçilmeden yeni training run başlatılmamalı veya geçerli sayılmamalı

### Wave 4 — Kontrollü Fine-Tuning ve Karar

Amaç: yalnızca gerçekten training gerektiren kategoriler için eğitim kararı almak.

Uygulama kuralı:
- Training ancak Wave 0-3 kapandıktan sonra karar adayıdır.
- Özellikle `tmk_cross_law` gibi retrieval ile çözülemeyen model misuse sorunları için gerekçe dosyası tutulur.
- Deploy kararı yalnızca post-train eval ile verilir; training loss tek başına yeterli değildir.

---

## 5. Bugünden İtibaren İş Bölümü

İlk ajan dalgası şu işleri üstlenecek:

1. **Training gate / veri yönetişimi**
   - Eğitim hattı için açık readiness kuralları çıkarılacak.
   - Yanlış veriyle başlatılan eğitim gibi hataları tekrar etmemek için repo içi kontrol noktaları yazılacak.

2. **Baseline + eval audit**
   - Hangi commit/metrik kombinasyonunun resmi referans olduğu netleştirilecek.
   - Eval setlerinin rolü ve tekrar üretim komutları tek belgede toplanacak.

3. **P0 execution map**
   - Reranker, guardrails ve retrieval genişleme işleri; eğitimden önce hangi sırayla yürütüleceği somutlaştırılacak.

Ben koordinatör olarak bu çıktıları birleştirip tek bir yürütme çerçevesine dönüştüreceğim.

---

## 6. Beklenen Sonuç

Bu planın amacı projeyi geri almak değil; **ölçülebilir güvenilirliği tekrar merkez yapmak**. Repo’da faz2/faz3 artefact’ları kalabilir, fakat bundan sonra:

- resmi baseline bellidir,
- training deneysel bir workstream olarak izlenir,
- kalite kapıları yazılıdır,
- ajan çalışması rastgele değil, kontrollü dalgalar halinde yürür.
