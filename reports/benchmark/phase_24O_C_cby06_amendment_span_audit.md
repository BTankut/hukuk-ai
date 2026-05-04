# Phase 24O-C CBY-06 Amendment Span Audit

Final targeted run:

```text
reports/benchmark/runs/phase_24O_targeted_shadow_smoke_20260504T094600Z
```

## Audit

Legal review expects the 2026 amendment chain:

```text
RG 03.04.2026 / 33213
Karar Sayısı 11153
Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği
m.11 added paragraph
```

Final targeted runtime selected:

```text
source = 20046801 / Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği
article = m.14
score = 6.80 FAIL
failure = missing_required_content_signal | partial_grounding_only
```

The selected evidence does not contain the required 2026 `11153` amendment span or the m.11 added paragraph. Trace evidence shows the runtime is now on the correct broad document family, but it still lands on existing base regulation spans such as m.14, m.12, m.5, m.4 and m.18.

## Decision

No runtime patch was applied. A deterministic selector rule cannot safely synthesize a missing or unmaterialized amendment paragraph. The correct next step is source/span acquisition and materialization for the amendment chain.

Created companion packet:

```text
reports/benchmark/phase_24O_C_cby06_source_acquisition_packet.md
```
