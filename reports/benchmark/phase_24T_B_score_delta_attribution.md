# Phase 24T-B Score Delta Attribution

Generated at UTC: `2026-05-05T10:23:18Z`  
Git HEAD before B commit: `6e3a7dc53f4d889e20f9e16d2f74855ae9cc1798`

## Compared Runs

```text
phase23RE_good = reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full
phase24R_base = reports/benchmark/runs/phase_24R_D_base_full_20260504T2035Z
rows_compared = 100 / 100
```

## Aggregate Delta

```text
phase23RE_raw_score_proxy = 816.86
phase24R_base_raw_score_proxy = 725.40
raw_delta = -91.46
phase23RE_pass_proxy = 91
phase24R_base_pass_proxy = 72
pass_delta = -19
```

## Delta Type Counts

- fail_to_pass: `3`
- pass_to_fail: `22`
- score_drop_no_pass_change: `11`
- score_gain_no_pass_change: `3`
- unchanged: `61`

## Suspected Root Cause Counts

- trace_artifact_missing: `100`

## Top 20 Score-Loss Rows

| QID | Phase23R-E | Phase24R BASE | Delta | Type | Root cause | Phase24R failure classes |
| --- | ---: | ---: | ---: | --- | --- | --- |
| KKY-11 | 9.66 | 3.25 | -6.41 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-08 | 7.55 | 1.45 | -6.10 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_family \| wrong_document \| partial_grounding_only |
| KKY-04 | 9.32 | 3.25 | -6.07 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-08 | 9.55 | 3.70 | -5.85 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| CBY-02 | 8.65 | 3.25 | -5.40 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-02 | 8.65 | 3.25 | -5.40 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-05 | 8.17 | 2.77 | -5.40 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-11 | 8.65 | 3.25 | -5.40 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-13 | 8.65 | 3.25 | -5.40 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-14 | 8.24 | 2.84 | -5.40 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-18 | 8.65 | 3.25 | -5.40 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-20 | 8.99 | 3.59 | -5.40 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-06 | 9.32 | 3.93 | -5.39 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-04 | 8.00 | 3.70 | -4.30 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-16 | 7.55 | 3.25 | -4.30 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-17 | 7.55 | 3.25 | -4.30 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| MULGA-04 | 7.55 | 3.25 | -4.30 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| UY-07 | 8.09 | 3.79 | -4.30 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-07 | 7.18 | 3.25 | -3.93 | pass_to_fail | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| YON-05 | 9.55 | 5.75 | -3.80 | pass_to_fail | trace_artifact_missing | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |

## Pass-to-Fail Rows

| QID | Phase23R-E | Phase24R BASE | Delta | Root cause | Phase24R failure classes |
| --- | ---: | ---: | ---: | --- | --- |
| CBY-02 | 8.65 | 3.25 | -5.40 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-02 | 8.65 | 3.25 | -5.40 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-04 | 8.00 | 3.70 | -4.30 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-05 | 8.17 | 2.77 | -5.40 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-06 | 9.32 | 3.93 | -5.39 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-07 | 7.18 | 3.25 | -3.93 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-08 | 7.55 | 1.45 | -6.10 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_family \| wrong_document \| partial_grounding_only |
| KANUN-11 | 8.65 | 3.25 | -5.40 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-13 | 8.65 | 3.25 | -5.40 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-14 | 8.24 | 2.84 | -5.40 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-16 | 7.55 | 3.25 | -4.30 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-17 | 7.55 | 3.25 | -4.30 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-18 | 8.65 | 3.25 | -5.40 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-20 | 8.99 | 3.59 | -5.40 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-04 | 9.32 | 3.25 | -6.07 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-08 | 9.55 | 3.70 | -5.85 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-11 | 9.66 | 3.25 | -6.41 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| MULGA-04 | 7.55 | 3.25 | -4.30 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| MULGA-05 | 7.10 | 4.00 | -3.10 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| UY-07 | 8.09 | 3.79 | -4.30 | trace_artifact_missing | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| YON-05 | 9.55 | 5.75 | -3.80 | trace_artifact_missing | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |
| YON-08 | 7.25 | 6.80 | -0.45 | trace_artifact_missing | missing_required_content_signal \| partial_grounding_only |

## New Wrong-Document Rows

| QID | Delta | Phase23R-E selected source | Phase24R selected source | Phase24R failure classes |
| --- | ---: | --- | --- | --- |
| CBY-02 | -5.40 | KAMU İHALE KURUMU TEŞKİLATI VE PERSONELİNİN ÇALIŞMA USUL VE ESASLARI HAKKINDA YÖNETMELİK :: fam=cb_yonetmelik\|id=200915611\|title=03313dd5e27d\|start=2009-12-01\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-02 | -5.40 | İŞ KANUNU :: fam=kanun\|id=4857\|title=a9ce1f5ad459\|start=unknown\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-04 | -4.30 | KİŞİSEL VERİLERİN KORUNMASI KANUNU :: fam=kanun\|id=6698\|title=f34b2908d3d3\|start=2016-04-07\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-05 | -5.40 | KİŞİSEL VERİLERİN KORUNMASI KANUNU :: fam=kanun\|id=6698\|title=f34b2908d3d3\|start=2016-04-07\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-06 | -5.39 | TÜRK TİCARET KANUNU :: fam=kanun\|id=6102\|title=112da0af0802\|start=unknown\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-07 | -3.93 | TÜRK TİCARET KANUNU :: fam=kanun\|id=6102\|title=112da0af0802\|start=unknown\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-08 | -6.10 | TÜRK BORÇLAR KANUNU :: fam=kanun\|id=6098\|title=c3e804a02699\|start=2011-02-04\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_family \| wrong_document \| partial_grounding_only |
| KANUN-11 | -5.40 | BELEDİYE KANUNU :: fam=kanun\|id=5393\|title=f7eac8e8a214\|start=unknown\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-13 | -5.40 | TÜRK BORÇLAR KANUNU :: fam=kanun\|id=6098\|title=c3e804a02699\|start=2011-02-04\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-14 | -5.40 | TÜRK BORÇLAR KANUNU :: fam=kanun\|id=6098\|title=c3e804a02699\|start=2011-02-04\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-16 | -4.30 | SENDİKALAR VE TOPLU İŞ SÖZLEŞMESİ KANUNU :: fam=kanun\|id=6356\|title=b17f9c81e846\|start=2012-11-07\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-17 | -4.30 | İCRA VE İFLAS KANUNU :: fam=kanun\|id=2004\|title=d3515e76d48e\|start=unknown\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-18 | -5.40 | İŞ KANUNU :: fam=kanun\|id=4857\|title=a9ce1f5ad459\|start=unknown\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-20 | -5.40 | TÜRK MEDENİ KANUNU :: fam=kanun\|id=4721\|title=671c04dcb41c\|start=unknown\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-04 | -6.07 | SOSYAL SİGORTA İŞLEMLERİ YÖNETMELİĞİ :: fam=yonetmelik\|id=13973\|title=258e26fdb556\|start=2010-05-12\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-08 | -5.85 | ELEKTRONİK HABERLEŞME SEKTÖRÜNE İLİŞKİN YETKİLENDİRME YÖNETMELİĞİ :: fam=yonetmelik\|id=13078\|title=da4558aa8a65\|start=2009-05-28\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-11 | -6.41 | BANKA KARTLARI VE KREDİ KARTLARI HAKKINDA YÖNETMELİK :: fam=yonetmelik\|id=11180\|title=b72d3bcd34ed\|start=2007-03-10\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| MULGA-04 | -4.30 | COĞRAFİ İŞARETLERİN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME :: fam=khk\|id=555\|title=2eba082ec897\|start=1995-06-27\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| MULGA-05 | -3.10 | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ :: fam=mulga_kanun\|id=6570\|title=751be76b867f\|start=1955-05-27\|state=repealed | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| UY-07 | -4.30 | DİCLE ÜNİVERSİTESİ DİŞ HEKİMLİĞİ FAKÜLTESİ EĞİTİM-ÖĞRETİM SINAV VE KLİNİK DERS YÜKÜ PRATİK UYGULAMA YÖNETMELİĞİ :: fam=uy\|id=18872\|title=b5d7c841346a\|start=2013-09-23\|state=active | - | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |

## New Hallucinated-Identifier Rows

| QID | Delta | Phase23R-E identifier | Phase24R identifier | Phase24R failure classes |
| --- | ---: | --- | --- | --- |
| CBY-02 | -5.40 | 200915611 m.17 | 200915611 m.17 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-02 | -5.40 | IK m.41 | IK m.41 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-04 | -4.30 | KVKK m.6 | KVKK m.6 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-05 | -5.40 | KVKK m.6 | KVKK m.6 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-06 | -5.39 | TTK m.595 | TTK m.595 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-07 | -3.93 | TTK m.1527 | TTK m.1527 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-11 | -5.40 | 5393 m.47 | 5393 m.47 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-13 | -5.40 | TBK m.417 | TBK m.417 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-14 | -5.40 | TBK m.227 | TBK m.227 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-16 | -4.30 | 6356 m.52 | TTK m.4 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-17 | -4.30 | İİK m.290 | İİK m.290 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-18 | -5.40 | IK m.56 | IK m.56 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KANUN-20 | -5.40 | TMK m.571 | TMK m.571 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-04 | -6.07 | 13973 m.2 | 20334 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-08 | -5.85 | 13078 m.1 | 14387 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| KKY-11 | -6.41 | 11180 | 31039 m.6 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| MULGA-04 | -4.30 | 555 | 555 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| MULGA-05 | -3.10 | 6570 m.gec1 | 6570 m.gec1 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| TUZUK-04 | -1.80 | 859727 m.4 | 859727 m.4 | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |
| UY-07 | -4.30 | 18872 m.20 | 18872 m.20 | missing_gold_document_signal \| missing_required_content_signal \| wrong_document \| hallucinated_identifier \| partial_grounding_only |
| YON-05 | -3.80 | 23722 m.1 | 3194 m.18 | missing_required_content_signal \| wrong_family \| hallucinated_identifier \| partial_grounding_only |

## Diagnostic Interpretation

The dominant attribution is `trace_artifact_missing`: Phase23R-E has populated trace-derived selected source/document keys, while Phase24R BASE was run with trace disabled and has empty selected-source fields across the compared rows. This explains why wrong-document and hallucinated-identifier counts can spike without a corresponding model/productization change.

This is an attribution result, not a remediation. Runtime remains unchanged.
