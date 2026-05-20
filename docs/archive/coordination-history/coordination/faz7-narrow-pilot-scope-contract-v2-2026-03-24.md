# FAZ7 Narrow Pilot Scope Contract v2

Tarih: 2026-03-24

Karar tipi:
- `internal narrow pilot`

Topology:
- mevcut DGX-backed pilot topology korunur
- `RC-G` accepted reference ve `RC-H` candidate release-control lane ayrımı korunur
- default serving lane ancak final steering `NARROW GO - Internal Pilot` olursa değiştirilebilir

Kapsam:
- mevcut mevzuat ve mevcut evaluation family setleri dışına çıkılmaz
- retrieval, reranker, prompt, model, corpus ve answer-path logic genişletilmez
- mevcut veri kapsamı genişletilmeyecektir

Kullanıcı tipi:
- yalnız kontrollü iç pilot kullanıcıları
- customer appliance, bundled device veya dağıtılabilir single-device paket kapsam dışıdır

Davranış sınırları:
- unsupported / out-of-scope alanlarda refusal zorunludur
- parity kapanmadan `RC-H` default lane yapılamaz
- narrow pilot gözlemi yalnız release-controls davranışını doğrulamak içindir

Rollback koşulları:
- parity mismatch `> 0`
- auth bypass
- audit write kaybı
- PII redaction leak
- Redis session continuity kaybı
- token accounting fallback
- rollback proof başarısızlığı
- backup / restore başarısızlığı

Success koşulları:
- `RC-H` allowed diff dışında değişiklik içermez
- must-close release controls `PASS`
- output parity mismatch count `0`
- family metric delta `0`
- p95 latency regression `<= 20%`
- refreshed cutover rehearsal ve rollback proof `PASS`

Abort koşulları:
- yukarıdaki rollback koşullarından herhangi biri
- final steering kararı `NO-GO - Release Controls`

Not:
- bu contract full production, customer rollout veya appliance/productization kararı değildir
