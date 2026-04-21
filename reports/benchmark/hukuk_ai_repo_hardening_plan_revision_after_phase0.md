# hukuk-ai — Phase 0 Sonrası Plan Revizyonu

**Tarih:** 2026-04-21
**Temel plan:** `hukuk_ai_repo_hardening_plan.md`
**Bu dokümanın amacı:** Phase 0 raporu görüldükten sonra mevcut plana küçük ama kritik sıra/priorite revizyonları eklemek.

---

## 1. Kısa Karar

Phase 0 başarılı kabul edilmeli. Benchmark artık tekrar koşulabilir, trace üretiyor ve private key güvenliği sağlanmış durumda. Bu nedenle ana plan çöpe atılmamalı; ancak aşağıdaki dört revizyon uygulanmalı:

1. **Yeni bir Phase 0.5 eklenmeli:** benchmark için ayrı bir “green lane” test hattı kurulmalı.
2. **Eski Phase 8 öne çekilmeli:** `answer contract` hardening çok geçte kalmış; yeni sırada ilk teknik fazlardan biri olmalı.
3. **Weak family routing daha erken gelmeli:** özellikle `CB_GENELGE`, `CB_KARAR`, `CB_YONETMELIK`, `MULGA`, `YONETMELIK`, `KANUN` aileleri source resolver ile birlikte erken ele alınmalı.
4. **Proxy scorer kalibrasyonu eklenmeli:** insan/judge ile proxy metrik aynı şey olmadığı için Phase 1 sonuna küçük bir calibration adımı eklenmeli.

---

## 2. Neden Revizyon Gerekli?

Phase 0 raporundan çıkan en kritik sinyaller:

- Benchmark koşusu 100/100 tamamlanmış, `trace rows=100` ve `missing retrieval trace id=0`. Yani trace-first altyapı zaten ayakta; bu işi çok daha sonra derinleştirmek mümkün. Buna karşılık `confidence_0_100` ve `final_reason` alanları **100/100 eksik**. Bu nedenle `answer contract` fazını Phase 8'de bırakmak doğru değil. fileciteturn2file0
- Repo test hattı halen kırmızı. Global ortam `fastapi` eksikliğiyle düşüyor, venv altında ise 6 failure var. Bu durum benchmark gelişimini kirletir; benchmark için ayrı bir yeşil hat tanımlanmalı. fileciteturn2file0
- En zayıf aileler `CB_GENELGE`, `CB_KARAR`, `CB_YONETMELIK`, `MULGA`, `YONETMELIK`, `KANUN`. Bu yüzden family-specific routing ve source catalog hardening geç faz değil, retrieval resolver ile aynı kümeye alınmalı. fileciteturn2file0
- En zayıf task alanları `temporal_validity`, `hierarchy_conflict`, `document_selection`, `precise_retrieval`, `compliance_checklist`. Sorun sadece generation değil; document family selection + temporal status + answer grounding zincirinde. fileciteturn2file0
- `missing_gold_document_signal=28` ve `missing_required_content_signal=99` birlikte düşünüldüğünde iki kök neden öne çıkıyor: (a) doğru belgeye gidememe / doğru belgeyi seçememe, (b) doğru context gelse bile contract-grounding üretememe. fileciteturn2file0

---

## 3. Güncellenmiş Faz Sırası

Aşağıdaki sıra, mevcut planın **revize edilmiş** icra sırasıdır.

### Phase 0 — Baseline Freeze
Zaten tamamlandı. Korunacak.

### **Yeni Phase 0.5 — Benchmark Green Lane ve Test Debt Quarantine**
Bu faz eski planda yoktu. Phase 1'den önce eklenmeli.

**Amaç:** Benchmark geliştirme akışını unrelated repo test borcundan ayırmak.

**Yapılacaklar:**
- Benchmark için tek resmi test komutu tanımla.
- Global Python yerine yalnızca proje venv/poetry/uv ortamı üzerinden koş.
- Mevcut 6 failing test için “known baseline debt” listesi oluştur.
- CI’de iki ayrı lane tanımla:
  - `benchmark-green-lane`
  - `legacy-suite-observe-only`
- Benchmark faz raporlarında şu iki sonucu ayrı yaz:
  - benchmark green lane durumu
  - legacy suite durumu
- `--resume`, trace completeness ve private-key guard bu lane’de mandatory kalsın.

**Acceptance criteria:**
- Tek komutla green lane koşuyor.
- Benchmark lane yeşil, legacy failure’lar ayrı raporlanıyor.
- Venv dışı pytest resmi yol olmaktan çıkarılıyor.

**Commit mesajı:**
```bash
git commit -m "benchmark: phase 0.5 isolate green lane from legacy test debt"
```

---

### Phase 1 — Evaluation Metrics Schema Upgrade
Korunacak, ama bir ek madde gelecek.

**Yeni ek:** Phase 1 sonunda `proxy-vs-judge calibration` yapılmalı.

**Ek yapılacaklar:**
- 15–20 soruluk sabit bir calibration subset tanımla.
- Bu subset için proxy scorer ile insan/judge skorunu yan yana raporla.
- Aşağıdaki farklar gözlensin:
  - document family match sapması
  - temporal validity sapması
  - hallucinated source false positive/false negative sapması
- Phase 1 raporuna “proxy reliability note” bölümü ekle.

**Acceptance criteria eki:**
- Calibration subset raporu üretildi.
- Proxy scorer yön gösterici olarak güvenilebilir ama judge yerine geçmediği açıkça ölçülmüş oldu.

**Commit mesajı:**
```bash
git commit -m "benchmark: phase 1 extend metrics and calibrate proxy scorer"
```

---

### **Yeni Phase 2 — Answer Contract ve Grounded Output Hardening**
Bu faz eski plandaki **Phase 8’den buraya taşınmalı**.

**Neden öne alındı?**
Çünkü `answer_contract_missing=100`, `confidence_0_100=100 missing`, `final_reason=100 missing`. Bu problem çözülmeden ara skorların büyük kısmı sisli kalır. fileciteturn2file0

**Amaç:** Her cevabı denetlenebilir, parse edilebilir ve scorer-friendly hale getirmek.

**Yapılacaklar:**
- Gateway cevabında şu alanları zorunlu doldur:
  - `answer`
  - `citations`
  - `source_titles`
  - `source_ids`
  - `doc_types`
  - `confidence_0_100`
  - `final_reason`
  - `retrieval_trace_id`
- `final_reason` için serbest metin yerine kontrollü şablon kullan:
  - selected source
  - temporal status
  - article/section basis
  - uncertainty note
- Contract eksikse response finalize edilmesin veya explicit degraded-mode ile işaretlensin.
- Scorer tarafında contract eksikliği ayrı operational fail olarak kalsın.

**Acceptance criteria:**
- `confidence_0_100` eksikliği <= 2/100
- `final_reason` eksikliği <= 2/100
- `retrieval_trace_id` eksikliği = 0
- Contract parse başarısı >= %98

**Commit mesajı:**
```bash
git commit -m "benchmark: phase 2 enforce answer contract before deeper retrieval tuning"
```

---

### Phase 3 — Trace-First Failure Forensics
Eski planın Phase 2’si burada devam eder.

**Not:** Trace zaten mevcut olduğundan bu fazın odağı artık “trace üretmek” değil, “trace üzerinden hata sınıflandırmasını doğrulamak” olmalı.

**Yeni vurgu:**
- Özellikle şu alanlara stage attribution çıkar:
  - `missing_gold_document_signal`
  - `missing_required_content_signal`
  - `auto_fail_triggered`
- Her fail için kök neden şu sınıflardan birine zorla bağlanmalı:
  - `family_routing_miss`
  - `identity_match_miss`
  - `temporal_status_miss`
  - `grounding_contract_miss`
  - `verification_miss`

---

### Phase 4 — Metadata Normalization ve Index Audit
Korunacak.

**Ek vurgu:**
- `official_title_normalized`
- `law_no_or_decision_no`
- `article_no`
- `official_gazette_date`
- `effective_start/effective_end`
- `is_repealed`
- `issuing_authority`

özellikle `CB_KARAR`, `CB_GENELGE`, `CB_YONETMELIK`, `TEBLIGLER`, `MULGA` için audit edilmeli.

---

### **Yeni Phase 5 — Legal Source Resolver + Weak Family Routing**
Bu, eski planın `Phase 4` ve `Phase 7` bileşenlerini aynı paket altında erkene çekilmiş şekilde birleştirir.

**Amaç:** En zayıf ailelerde yanlış family / yanlış belge seçimini erken düşürmek.

**Öncelik sırası:**
1. `CB_GENELGE`
2. `CB_KARAR`
3. `CB_YONETMELIK`
4. `MULGA`
5. `YONETMELIK`
6. `KANUN`

**Yapılacaklar:**
- Aile bazlı alias map
- Number/title/date aware resolver
- Authority-aware routing
- “Mülga mı / yürürlükte mi / değişiklik sonrası mı?” ön filtreleri
- Exact title / decision no / OG date boost

**Acceptance criteria:**
- Yukarıdaki 6 ailede average proxy score anlamlı artmalı.
- `wrong_document_family` ve `missing_gold_document_signal` birlikte düşmeli.

**Commit mesajı:**
```bash
git commit -m "benchmark: phase 5 harden source resolver for weak legal families"
```

---

### Phase 6 — Hybrid Retrieval, Lexical Boost ve Reranker A/B
Korunacak.

**Ek not:**
`test_reranker_ab.py` zaten kırmızı olduğu için bu faz başlamadan önce Phase 0.5 lane izolasyonu tamamlanmış olmalı.

---

### Phase 7 — Temporal Validity Controller
Korunacak, fakat Phase 5 ve 6’dan hemen sonra uygulanmalı.

**Neden?**
`temporal_validity` tasklerinde 19 soruda yalnızca 1 PASS var; ayrıca `MULGA` ailesi 0 PASS. Bu, temporal logic’in orta-üst öncelikte olduğunu gösteriyor. fileciteturn2file0

**Ek yapılacaklar:**
- `effective_start <= query_date <= effective_end` mantığı
- mülga belge fallback yasağı
- geçiş hükmü / geçici madde / değişiklik tarihi zinciri
- “current_update” taskleri için query date explicit taşıma

---

### Phase 8 — Verification Gate ve Legal Consistency Checks
Eski Phase 9 burada kalabilir.

**Ek vurgu:**
Verification sadece citation var mı diye bakmasın; ayrıca:
- cited family = selected family mi?
- cited source yürürlükte mi?
- article / section support ediyor mu?
- authority chain tutarlı mı?

---

### Phase 9 — Regression Matrix, Promotion Candidate ve Final Report
Korunacak.

**Ek promotion gate:**
Aşağıdaki üç gösterge aynı anda iyileşmeden aday promote edilmesin:
- `answer_contract_missing`
- `missing_gold_document_signal`
- `temporal_validity avg`

---

### Phase 10 — Fine-Tuning Only After Retrieval Stabilization
Korunacak. Fine-tuning yine en sonda kalmalı.

---

## 4. Kod Asistanı İçin Net Sonraki Adım

Şu anda en doğru sıra:

1. **Phase 0.5** uygula.
2. **Phase 1** uygula ve calibration ekle.
3. **Yeni Phase 2** olarak answer contract zorunluluğunu çöz.
4. Sonra failure forensics ve source resolver katmanına geç.

Bu sıranın gerekçesi basit:
- Ölçüm sistemi önce güvenilir olmalı.
- Üretim contract’ı sonra zorunlu olmalı.
- Ondan sonra retrieval/family/temporal tuning yapılmalı.

Aksi halde sonraki fazlarda görülen iyileşme ile “daha iyi açıklanmış hata” birbirine karışır.

---

## 5. Faz Sonu Raporuna Eklenecek Yeni Alanlar

Bundan sonraki tüm faz raporlarına şu alanlar da eklensin:

```text
12. Benchmark green lane status
13. Legacy suite status
14. Proxy-vs-judge calibration note (Phase 1 ve sonrası)
15. Answer contract completeness
   - missing confidence_0_100
   - missing final_reason
   - missing source_ids
   - missing source_titles
   - missing doc_types
16. Failure stage distribution
   - family_routing_miss
   - identity_match_miss
   - temporal_status_miss
   - grounding_contract_miss
   - verification_miss
```

---

## 6. Son Hüküm

Ana plan doğru yolda. Sadece sıralama düzeltilmeli.

**En kritik revizyon:** `Answer Contract` fazını çok öne al.
**İkinci kritik revizyon:** benchmark için legacy test borcundan bağımsız green lane kur.
**Üçüncü kritik revizyon:** weak family routing’i retrieval resolver ile aynı blokta erkene çek.

Bu üç değişiklik yapılırsa sonraki fazlarda görülen kazanımlar çok daha temiz ve ölçülebilir olur.
