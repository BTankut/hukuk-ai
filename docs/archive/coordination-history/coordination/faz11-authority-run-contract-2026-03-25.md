# FAZ11 Authority Run Contract

Tarih: 2026-03-25

Referans zinciri:
- `coordination/faz7-rc-g-manifest-2026-03-24.json`
- `coordination/faz9-rc-j-manifest-2026-03-24.json`
- `coordination/faz9-runtime-lane-contract-2026-03-24.md`
- `coordination/faz9-rc-j-build-2026-03-24.md`
- `evaluation/reports/faz9-rc-j-preprojection-v3-170-2026-03-24.md`

## Resmi Kural

FAZ11 authority kosusu, FAZ9 `v3-170` mismatch ureten kanonik runtime contract'i esas alir.

Bu nedenle authority pair yalniz su launcher zinciri ile acilir:

- reference lane: `scripts/faz7/launch_local_rc_g_reference_gateway.sh`
- diagnostic lane: `scripts/faz9/launch_local_rc_j_candidate_gateway.sh`

## Authority Pair

- reference side = `RC-G`
- candidate side = `RC-J`
- family = `v3-170`
- question order = canonical source order, sharding yok, reordering yok
- include trace = `true`
- report role = `evaluation`
- delay seconds = `0.5`
- timeout seconds = `180`

## Canonical Generation Contract

- streaming = `off`
- retry_count = `0`
- fallback lane = `disabled`
- enable_thinking = `false`
- seed = `3407`
- max_tokens = `512`
- timeout budget = `180`
- sampler parity = `RC-G` ile ayni

## Canonical Runtime Topology

- `RC-G` gateway port = `8119`
- `RC-J` gateway port = `8118`
- `RC-G` tunnel port = `30016`
- `RC-J` tunnel port = `30128`
- `RC-G` release controls = `off`
- `RC-J` release controls = `on`
- `RC-G` session store = `memory`
- `RC-J` session store = `redis`
- `RC-G` token accounting fallback = `approximate`
- `RC-J` token accounting fallback = `runtime tokenizer`

## First-Run Authority Rule

- her lane icin tek full-run authority kosusu alinacak
- `runtime_error = 0` olan kayitlar icin rerun yapilmayacak
- sadece gercek runtime error varsa, yalniz error veren kayitlar icin tek error-rerun dusunulebilir
- error-rerun authority kaydinin yerine gecmez
