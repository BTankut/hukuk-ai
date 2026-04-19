# Merged Vs Baseline Matched Parity Contract 2026-04-19

## Official Rule Freeze

- `merged_first_rule = true`
- `baseline_second_parity_rule = true`
- `acceptance_without_model_line_label = forbidden`

## Execution Order

1. `merged-first integration`
2. `merged acceptance`
3. `baseline second matched parity rerun`
4. `delta decision = better | same | worse`

Bu sira kirilmayacak.

## Matched Pack Requirements

- same question pack
- same refusal pack
- same citation expectations
- same temporal / mulga probes
- same runtime smoke surface
- same collection identity
- same gateway behavior contract except explicit model-line difference

## Mandatory Reporting Fields

Her parity raporunda asagidaki alanlar exact yazilacak:

- `lane_label`
- `upstream_model_id`
- `runtime_host`
- `gateway_port`
- `collection_name`
- `eval_pack_name`
- `source_correct_count`
- `wrong_source_count`
- `runtime_error_count`
- `unexplained_count`
- `delta_decision = better | same | worse`

## Acceptance Rule

- merged lane uzerinde same-pack acceptance alinmadan baseline parity rerun closure verilmeyecek
- baseline parity raporu merged run ile matched degilse acceptance delili sayilmayacak
- baseline PASS tek basina yeni major acceptance yetkisi vermeyecek

## Governance Meaning

- baseline lane bundan sonra kontrol ve karsilastirma lane'idir
- merged lane bundan sonra authoritative target lane'dir
- major acceptance iddialari ancak merged run ve ayni pack baseline rerun birlikte yazildiginda savunulabilir kabul edilecektir
