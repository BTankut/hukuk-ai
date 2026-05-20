# FAZ12 Output Parity Taxonomy v1

Tarih: 2026-03-25

FAZ12 primary reason kumesi kapali bir reason set olarak tanimlanir.

## Kapali Reason Set

- `citation_projection_drop`
- `citation_projection_format_only`
- `final_mode_mapping_delta`
- `answer_body_mutation_after_projection`
- `refusal_body_mutation_after_projection`
- `blocked_reason_set_delta`
- `response_envelope_delta`
- `serialized_output_only_delta`
- `unexplained_post_preprojection_drift`

## Yorumu

- `citation_projection_drop`
  visible citation projection cevabinda semantic kayip var
- `citation_projection_format_only`
  citation body/set farki var, answer semantic olarak kaymiyor
- `final_mode_mapping_delta`
  answer/refusal mode veya refusal_mode eslesmesi kayiyor
- `answer_body_mutation_after_projection`
  projection sonrasi visible answer body mutasyona ugrayor
- `refusal_body_mutation_after_projection`
  refusal body projection sonrasi mutasyona ugrayor
- `blocked_reason_set_delta`
  guardrail/block sebep kumesi drift uretiyor
- `response_envelope_delta`
  envelope mapping seviyesinde drift var
- `serialized_output_only_delta`
  envelope ayni kalirken son serialized visible output drift uretiyor
- `unexplained_post_preprojection_drift`
  yukaridaki kapali reason set ile aciklanamayan drift
