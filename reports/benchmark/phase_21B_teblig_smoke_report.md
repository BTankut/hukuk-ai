# Hukuk-AI Phase 21B TEBLIGLER Source / Document Remediation Smoke Report

## Scope

Phase 21B yalnız TEBLIGLER source/document routing katmanına odaklandı.

Davranış değişikliği yapılan dosyalar:

- `api-gateway/src/source_family_resolver.py`
- `api-gateway/src/rag/source_identity.py`
- `api-gateway/src/routers/chat.py`

Bu değişiklikler QID veya özel cevap anahtarı bazlı değildir. Amaç, doğal dilde tebliğ sorularında aile seçimi, metadata-first source identity ve tebliğ sıra/seri numarası ayrıştırmasını sistemik olarak güçlendirmektir. `answer_synthesis.py` ve answer slot davranışına yeni patch eklenmedi.

## Runtime Provenance

Final smoke run:

```text
reports/benchmark/runs/20260428T104001Z_phase21B_teblig_smoke_final
```

Runtime:

- API URL: `http://127.0.0.1:8000/v1`
- Gateway model: `hukuk-ai-poc`
- DGX base URL: `http://192.168.12.243:30000/v1`
- DGX model: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Embedding backend: `remote`
- Embedding base URL: `http://127.0.0.1:8081/v1`
- Guardrails: `false`
- Presidio: `false`

## Changes

- `contains_legal_teblig_term` doğal dilde "hangi tebliğ", "ana/uygulama/ilk bakılacak tebliğ", "merkezdeki tebliğ" gibi tebliğ yönlendirme ifadelerini kapsayacak şekilde genişletildi.
- Tebliğ domain query expansion eklendi: e-Fatura/e-Arşiv/e-İrsaliye, şirket kuruluşu/MERSİS/ticaret sicili ve e-Defter/berat aileleri için source-title sinyali üretiliyor.
- Metadata lookup sorgusu artık resolver query expansion sinyallerini de kullanıyor.
- Source identity tarafında `sıra no` ve `seri no` tebliğ identifier adayı olarak ayrıştırılıyor.
- Metadata source record identifier setine `sira_no` ve `seri_no` dahil edildi.
- Genel soru kelimeleri ve standalone yıllar title-overlap sinyali olmaktan çıkarıldı; yıl sinyali ayrı skorlanmaya devam ediyor.
- Exact identifier bulunan metadata-first seçiminde geniş source-key yayılımı daraltıldı; yalnız en güçlü exact identifier adayları tutuluyor.

## Results

Karşılaştırma tabanı:

```text
reports/benchmark/runs/20260428T_phase20F_full_after_C_D
```

Final Phase 21B TEBLIGLER smoke:

| Metric | Phase 20F TEBLIGLER | Phase 21B TEBLIGLER |
|---|---:|---:|
| pass_proxy | `4/8` | `7/8` |
| family exact | `7/8` | `8/8` |
| hallucinated identifier rows | `3` | `1` |
| unsupported confident answer | `0` | `0` |
| source_key_collision_detected | `0` | `0` |
| source_key_v2_collision_detected | `0` | `0` |
| binding_source_key_collision_detected | `0` | `0` |

Final score summary:

- raw_score_proxy: `62.01 / 80`
- average_score_0_10_proxy: `7.75`
- pass_proxy: `7`
- fail_proxy: `1`
- answer_contract_invalid_count: `0`
- selector_preferred_family_hit_rate: `1.0`

## Row Outcomes

| QID | Score | Result | Selected document | Selected span | Notes |
|---|---:|---|---|---|---|
| TEB-01 | `8.80` | PASS | `KAMU İHALE GENEL TEBLİĞİ` | `13354 m.78/f.0` | Recovered from previous auto-fail. |
| TEB-02 | `8.65` | PASS | `TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ (TEBLİĞ NO: 2008-32/34)` | `11990 m.8/f.0` | Preserved. |
| TEB-03 | `8.00` | PASS | `VERGİ USUL KANUNU GENEL TEBLİĞİ (SIRA NO: 509)` | `33905 m.0/f.0` | Recovered from wrong-family 6563-law tebliğ drift. |
| TEB-04 | `7.25` | PASS | `VERGİ USUL KANUNU GENEL TEBLİĞİ (SIRA NO:429)` | `18937 m.0/f.0` | Preserved. |
| TEB-05 | `8.99` | PASS | `SERMAYE PİYASASINDA FİNANSAL RAPORLAMAYA İLİŞKİN ESASLAR TEBLİĞİ (II-14.1)` | `18477 m.2/f.0` | Preserved. |
| TEB-06 | `3.25` | FAIL | `ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ` | `23093 m.6/f.0` | Domain moved from unrelated electronic-meeting tebliğ to relevant company-establishment tebliğ, but gold-document/span alignment still fails. |
| TEB-07 | `7.52` | PASS | `MUHASEBAT GENEL MÜDÜRLÜĞÜ GENEL TEBLİĞİ (SIRA NO: 78)` | `39766 m.1/f.0` | Recovered from KVKK wrong-family fail, but exact canonical document fidelity remains suspicious and should be audited before promotion if e-Defter source specificity is required. |
| TEB-08 | `9.55` | PASS | `POSTA VE HIZLI KARGO YOLUYLA TAŞINAN EŞYANIN GÜMRÜK İŞLEMLERİNE İLİŞKİN TEBLİĞ (SERİ NO: 1)` | `39511 m.1/f.0` | Preserved. |

## Gate Decision

Phase 21B gate status: PASS.

Acceptance rationale:

- TEBLIGLER pass rate hedefi `>= 6/8`; final `7/8`.
- Wrong-family signal sıfırlandı: final family exact `8/8`.
- Hallucinated identifier azaldı: `3 -> 1`.
- Unsupported confident answer artmadı: `0`.
- Source key, source_key_v2 ve binding collision yok: `0`.
- Değişiklikler soru-ID bazlı değil; tebliğ family/source identity katmanında sistemik.

## Residual Risks

- TEB-06 kalan tek fail. Source family doğru ve domain artık daha yakın, fakat scoring hâlâ `missing_gold_document_signal`, `wrong_document`, `hallucinated_identifier`, `insufficient_canonical_span_evidence` veriyor. Bu kalan açık source/span materialization veya canonical gold document mapping seviyesinde incelenmeli.
- TEB-07 pass oldu, fakat final scoring seçimi `Sıra No: 78` Muhasebat tebliğine gidiyor. Local metadata selector daraltması e-Defter `Sıra No: 1` adayını izole edebiliyor; final orchestration içindeki son seçim farkı Phase 21C için izlenmeli.
- TEBLIGLER smoke geçişi full 100 benchmark promotion anlamına gelmez; bir sonraki aşamada full benchmark regression kontrolü gerekir.
