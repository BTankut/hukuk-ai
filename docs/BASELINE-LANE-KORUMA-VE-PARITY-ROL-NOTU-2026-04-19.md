# Baseline Lane Koruma Ve Parity Rol Notu 2026-04-19

## Required Fields

- `baseline_lane_status = preserved_but_non_authoritative_for_new_major_acceptance`
- `baseline_lane_authoritative = false`
- `baseline_lane_fallback = true`
- `baseline_lane_parity_role = true`
- `baseline_lane_retained = true`

## Frozen Operational Meaning

- Baseline lane silinmedi.
- Baseline lane aktif authoritative lane olarak korunmadi.
- Baseline lane `8004` uzerinde parity ve fallback amaciyla tutuldu.
- Baseline lane yeni major acceptance closure icin tek basina yeterli delil olmayacak.

## Exact Allowed Usage

- merged run sonrasinda same-pack parity rerun
- fallback smoke
- regression comparison
- emergency rollback hazirlik yuzeyi

## Exact Forbidden Usage

- yeni major acceptance'i baseline lane uzerinde kapatmak
- merged acceptance yerine baseline PASS'i authoritative sonuc gibi yazmak
- model-line label olmadan baseline run'i ana closure delili yapmak
