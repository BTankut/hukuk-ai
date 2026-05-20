# Mevzuat Model-Line Divergence Forensic Raporu 2026-04-19

## Official Finding

- root_cause_class = `model_line_governance_drift`

## Chronology

1. `2026-03-21`: `dgx1` merged endpoint repo-native bridge olarak kabul edildi.
2. `2026-03-22`: `dgx1` merged lane resmi olarak `primary post-train candidate serving lane` ilan edildi.
3. `2026-03-23`: `dgx1` merged lane'in `active 8000 lane` oldugu resmi cutover raporuna yazildi.
4. `2026-04-16`: mevzuat Faz-1 shadow integration PASS kapandi, fakat mevzuat faz script zinciri baseline launcher referansiyla ilerledi.
5. `2026-04-18` ve `2026-04-19`: mevzuat controlled cutover, rerun ve post-cutover stabilization zinciri baseline upstream `.236` ve `Qwen/Qwen3.5-35B-A3B-FP8` env'i ile kapandi.

## Decisive Repo Evidence

- merged preferred-lane decision = `coordination/dgx1-merged-serving-decision-2026-03-22.md`
- merged active-8000 execution evidence = `docs/FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md`
- mevzuat active runtime PASS evidence = `docs/MEVZUAT-POST-CUTOVER-STABILIZATION-GATE-RAPORU-2026-04-19.md`
- live process evidence on 2026-04-19:
  - `DGX_BASE_URL=http://127.0.0.1:30011/v1`
  - `DGX_MODEL=Qwen/Qwen3.5-35B-A3B-FP8`
  - `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- mevzuat cutover script evidence:
  - `scripts/mevzuat_cutover/run_controlled_cutover_execution_rerun_v4_phase.py`
  - `scripts/mevzuat_cutover/run_collection_binding_divergence_remediation_phase.py`
  - `scripts/mevzuat_cutover/run_retrieval_runtime_parity_phase.py`
  all bind to `scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh`

## Divergence Statement

- merged lane repo'da kurulmus ve promoted edilmis durumda idi.
- buna ragmen mevzuat retrieval/runtime/cutover acceptance zinciri merged authoritative lane'e kilitlenmedi.
- acceptance artefact'lari runtime collection'i ve smoke sonucunu dogruladi; fakat ayni closure paketleri model-line label'i tasimadan baseline lane uzerinde kapandi.

## Exact Drift Surface

| surface | expected | observed | divergence |
| --- | --- | --- | --- |
| new major integration authority | `merged-first` | `baseline live lane` | YES |
| model-line label on acceptance | `mandatory` | `absent` | YES |
| same-pack baseline parity after merged | `required` | `not bound` | YES |
| major acceptance claim on baseline | `forbidden` | `de facto allowed` | YES |
| data-plane corpus build | `model-independent` | `model-independent` | NO |

## Forensic Conclusion

- mevzuat corpus / Milvus / human review / cutover mekanigi gercek ve gecerlidir.
- ancak bu closure zinciri `merged model acceptance` olarak yorumlanamaz.
- bu zincir en fazla `baseline lane uzerinde kapanmis mevzuat runtime integration` olarak okunabilir.
- bu nedenle bundan sonraki resmi yon gereksinimi `retrieval tekrar yapmak` degil, `model-line authority reset` olarak tanimlanmistir.
