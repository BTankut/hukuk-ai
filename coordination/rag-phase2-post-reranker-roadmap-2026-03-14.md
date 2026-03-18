# Hukuk-AI Phase 2 — Post-Reranker Roadmap

**Tarih:** 2026-03-14  
**Durum:** ACTIVE PLAN  
**Temel bağlam:** Hardened clean reranker sweep tamamlandı. BGE reranker hiçbir threshold'ta baseline'ı geçemedi. Hybrid BM25 + dense de correct_source'u artırmadı. Bu nedenle retrieval trick odaklı dalga durduruluyor; öncelik tekrar **chunking / document structure / context assembly** katmanına dönüyor.

---

## 1. VERDICT

- **Mevcut veri üzerinde retrieval trick hattı tükenmiş durumda.** Hybrid BM25 ve BGE reranker, ikisi de clean ölçümde `correct_source` metriklerini iyileştirmedi.
- **Reranker net-destructive.** Hardened clean sweep sonucunda OFF baseline `correct_source=76.93%` iken tüm reranker threshold'ları bunun altında kaldı.
- **Ana sorun retrieval algoritması değil, retrieval birimi.** Off-by-one article confusion ve cross-article eksik context, embedding/reranker tuning'den çok **article granularity + context assembly** problemine işaret ediyor.
- **BGE-M3'ün mutlak kazanan olduğu henüz ispatlanmış değil.** Yeni chunking ile **e5 vs BGE-M3 A/B** yapılmadan embedding kararı finalize edilmeyecek.
- **Yeni yön:** article-level chunking'i ana retrieval birimi yap, embedding modelini veriyle seç, aynı-article dedup/context assembly'yi sertleştir, eval setini büyüt, ardından tekrar ölç.

---

## 2. WHAT WE LEARNED

- Hardened eval harness artık güvenilir; reranker kararı artık ölçüm hatasıyla kirli değil.
- Hybrid BM25 bu küçük ve yapısal corpus'ta net fayda sağlamadı; tek başına promote edilmeyecek.
- Structured query parsing faydalı ama düşük frekanslı; yüksek ROI ana kaldıraç değil.
- Off-by-one article confusion en önemli düzeltilebilir hata sınıfı.
- Article-context özelliği kodda var ama index etkisi zayıf; current article-level coverage pratikte çok düşük.
- 50 soruluk eval setinde yaklaşık 2-3 puan varyans var; küçük delta'lar karar verdirici sayılmayacak.

---

## 3. NEW PRIORITY ORDER

1. **Unconditional article-level chunking**
   - Her article için full-text article chunk üret.
   - Article-context artık istisna değil, ana retrieval birimi olacak.

2. **Embedding A/B: e5 vs BGE-M3**
   - Aynı chunking ile iki embedding modeli head-to-head ölçülecek.
   - Kazanan model veriyle seçilecek.

3. **Same-article dedup + parent promotion**
   - Birden fazla fıkra aynı article'dan geliyorsa context assembly'de article parent'a yükselt.

4. **Eval set expansion (50 → 60-65+)**
   - Off-by-one, cross-article, terminology-only, TMK/other-kanun soruları eklenecek.

5. **Corpus expansion**
   - TBK dışına çık: önce TMK, sonra HMK/TCK öncelikli.

6. **HyDE (feature-flag)**
   - Ancak chunking + embedding + dedup stabilize olduktan sonra.

7. **Reranker re-evaluation**
   - Ancak reranker OFF baseline `correct_source >= 82%` seviyesine yaklaşırsa yeniden denenir.

---

## 4. 7-DAY EXECUTION PLAN

### Day 1 — Chunking overhaul
- `article_context` üretimini conditional olmaktan çıkar.
- Her article için parent/full-text chunk üret.
- Article chunk size limitini pratik corpus'a göre yükselt.
- Shadow reindex al.
- Eval al: `chunking-v2` baseline.

### Day 2 — Embedding A/B
- Aynı chunking ile:
  - e5 collection
  - BGE-M3 collection
- İkisini aynı eval setiyle karşılaştır.
- Sonucu `coordination/embedding-ab-2026-03-15.md` benzeri karar notuna yaz.

### Day 3 — Context assembly refinement
- Same-article dedup / parent promotion uygula.
- Fıkra fragment'leri yerine article-level context'i tercih et.
- Eval setine 10-15 hedefli yeni soru ekle.

### Day 4 — TMK full index
- TMK loader/index hattını TBK pattern'inden türet.
- Reindex + eval.

### Day 5 — HMK / TCK expansion
- Öncelikli ikinci dalga kanunlarını ekle.
- Reindex + eval.

### Day 6 — Error analysis + targeted fixes
- 60-65+ soruluk sette failure bucket analizi yap.
- En sık 3 hata sınıfına nokta düzeltme uygula.
- Final weekly eval al.

### Day 7 — Checkpoint
- Haftalık checkpoint notu yaz.
- Hedef kapıları ölç.
- Week 2 kararı ver:
  - `correct_source >= 82%` ise HyDE + reranker re-check
  - değilse deeper chunk/embedding adaptation

---

## 5. ADOPT / BORROW / IGNORE

### ADOPT
- **TBK loader pattern reuse** → TMK/HMK/TCK loader genişletmesi
- **Shadow collection workflow** → güvenli A/B ve migration standardı
- **Current hardened eval harness** → bundan sonra tüm kritik eval sweep'lerde standart

### BORROW
- **HyDE pattern** → düşük riskli query reformulation, feature-flag ile
- **sentence-transformers contrastive FT path** → ancak embedding A/B sonrası gerçekten gerekirse

### IGNORE / SHELVE FOR NOW
- **Hybrid BM25** → şu an shelve
- **BGE reranker** → şu an shelve, default-off
- **ColBERT / RAGatouille** → bu corpus boyutunda erken
- **GraphRAG / full-stack frameworks** → hâlâ gereksiz karmaşıklık
- **Zemberek/BM25 tokenization yatırımı** → BM25 shelve edildiği için ertelendi

---

## 6. STOP DOING

- Reranker threshold denemeleriyle oyalanma
- Hybrid BM25'yi şu haliyle promote etmeye çalışma
- Structured query parsing'i ana kaldıraç sanma
- BGE-M3'ü veriyle kıyaslamadan kalıcı kazanan ilan etme
- 50 soruluk sette 2-3 puanlık oynamaları anlamlı breakthrough sayma

---

## 7. SUCCESS GATES — NEXT CHECKPOINT

| Gate | Metric | Hedef |
|------|--------|-------|
| G1 | correct_source_rate | **>= 0.82** |
| G2 | hallucination_rate | **<= 0.05** |
| G3 | citation_rate | **>= 0.86** |
| G4 | refusal_accuracy | **>= 0.95** |
| G5 | Embedding A/B | **karar verilmiş olmalı** |
| G6 | Corpus breadth | **>= 2 tam kanun indexlenmiş** |
| G7 | Off-by-one confusion | **bariz düşmüş olmalı** |
| G8 | Eval set size | **>= 60 soru** |

---

## 8. Immediate Next Action

**İlk uygulanacak iş:**
1. chunker'ı article-level primary unit olacak şekilde değiştir
2. shadow reindex al
3. aynı chunking ile e5 vs BGE-M3 A/B eval yap

Bu üçlü tamamlanmadan yeni retrieval trick dalgası açılmayacak.
