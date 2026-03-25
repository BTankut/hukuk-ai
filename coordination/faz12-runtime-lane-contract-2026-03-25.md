# FAZ12 Runtime Lane Contract

Tarih: 2026-03-25

Referans:
- `coordination/faz11-runtime-lane-contract-2026-03-25.md`
- `scripts/faz7/launch_local_rc_g_reference_gateway.sh`
- `scripts/faz9/launch_local_rc_j_candidate_gateway.sh`

## Lane Dagilimi

- `RC-G`
  kabul edilmis kalite ve answer-path referansi
- `RC-J`
  tek diagnostic parity adayi

## Port ve Launcher Contract

- reference lane launcher:
  `scripts/faz7/launch_local_rc_g_reference_gateway.sh`
- candidate lane launcher:
  `scripts/faz9/launch_local_rc_j_candidate_gateway.sh`
- FAZ12 pair runner:
  `scripts/faz12/run_output_parity_lane.sh`

Varsayilan portlar:

- `RC-G gateway = 8119`
- `RC-G tunnel = 30016`
- `RC-J gateway = 8118`
- `RC-J tunnel = 30128`

## Sabit Runtime Kurallari

- `PARITY_TRACE_ENABLED=true`
- `DGX_SEED=3407`
- `DGX_RETRY_COUNT=0`
- timeout budget reference/candidate eslenik tutulacak
- eval aile sirasi:
  1. `faz1-50`
  2. `v2-95`
  3. `v3-170`

## Ozel Not

`v3-170` icin lane contract yalniz post-preprojection replay builder'larinda kullanilacak; yeni authority toplama amaciyla canli canonical rerun acilmayacak.
