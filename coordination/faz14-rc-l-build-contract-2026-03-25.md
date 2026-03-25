# FAZ14 RC-L Build Contract

Tarih: 2026-03-25

Build zinciri:
- `RC-J freeze -> RC-L build`

Zorunlu kurallar:
- `RC-L` yalniz `RC-J` dondurulmus manifesti uzerinden insa edilir.
- `RC-L answer_path_delta = []`.
- `RC-L` icin yalniz su uc mantik katmaninda degisiklik serbesttir:
  - `final_mode_mapping`
  - `blocked_reason_set` projection
  - `response_envelope` projection
- `serialized_output_hash` degisimi yalniz bu projection zincirinin sonucu olarak kabul edilir.
- Retrieval, prompt, model request payload, generation contract, preprojection anchor, cited projection, citation set projection, answer body, citation body, refusal body degismeyecektir.
