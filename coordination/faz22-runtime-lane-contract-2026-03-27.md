# FAZ22 Runtime Lane Contract

- `RC-G` launcher = `scripts/faz7/launch_local_rc_g_reference_gateway.sh`
- `RC-J` launcher = `scripts/faz9/launch_local_rc_j_candidate_gateway.sh`
- `RC-M` launcher = `scripts/faz16/launch_local_rc_m_candidate_gateway.sh`
- embedding dependency = `127.0.0.1:8081`
- milvus dependency = `127.0.0.1:19530`
- model lane = remote merged serving tunnel carried by launcher scripts

## Port Policy

- `RC-G` default gateway/tunnel = `8119 / 30016`
- `RC-J` default gateway/tunnel = `8118 / 30128`
- `RC-M` default gateway/tunnel = `8148 / 30158`
- lanes run sequentially and must leave no live port residue between runs
