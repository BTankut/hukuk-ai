# Reranker Safe Activation Runner

**Tarih:** 2026-03-20  
**Amaç:** Reranker açık/kapalı varyantlarını canonical 50q / 95q / 170q setleri üzerinde kontrollü biçimde koşturacak tek giriş noktasını repo'ya eklemek.

## Bulgular

- Repo'da fixture tabanlı `evaluation/reranker_ab_eval.py` vardı, fakat canlı API üzerinde baseline-off ve threshold sweep matrisi kuran bir runner yoktu.
- Tarihsel notlar reranker'ın daha önce baseline'ı geçmediğini gösteriyor; bu nedenle yeni araç yalnız `enable` değil, `keep-off / rework` kararına da hizmet etmeli.
- API gateway restart süreci ortam bağımlı olduğu için otomatik restart güvenli değil.

## Uygulanan Çıktılar

- `evaluation/run_reranker_safe_activation.py`
- `docs/reranker-safe-activation-runbook.md`

## Sağlanan Davranış

Runner:

1. `baseline-off` varyantını oluşturur.
2. `thr=0.1..0.5` threshold sweep varyantlarını üretir.
3. `faz1-50`, `phase3-95`, `faz2-170` setleri için tam eval matrisi çıkarır.
4. `--dry-run` modunda env block'ları, komutları ve beklenen report path'lerini yazar.
5. `--live` modunda her variant öncesi kullanıcıdan API restart onayı ister.
6. Summary JSON artefact'ı üretir.

## Doğrulama

```bash
python3 -m py_compile evaluation/run_reranker_safe_activation.py
python3 evaluation/run_reranker_safe_activation.py --dry-run
```

Sonuç:

- Script sentaktik olarak geçerli.
- Dry-run mode env matrix + eval komutlarını doğru çözüyor.
- Canlı mod artık manual restart gereksinimini yalnız belgelemiyor, variant bazında kullanıcı onayıyla zorluyor.

## Sonraki Adım

Plana göre bir sonraki iş canlı koşu:

1. `baseline-off`
2. `reranker-on` thresholds `0.1 0.2 0.3 0.4 0.5`
3. 50q + 95q + 170q raporlarını tek karar tablosunda toplamak
