# FAZ9 Steering Decision Table

| decision | meaning | trigger | selected |
| --- | --- | --- | --- |
| `NARROW GO - Internal Pilot` | parity, retention, cutover and rollback zinciri tam kapanir | `WP-8`, `WP-9`, `WP-10`, `WP-11` hepsi `PASS` | no |
| `NO-GO - Preprojection Parity` | full-family preprojection hash gate acilamadi veya kapatilmadi | `normalized_request`, `model_request_payload`, `generation_contract`, `preprojection` veya `raw_answer` mismatch | yes |
| `NO-GO - Output Parity` | preprojection kapanir ama normalized visible output parity kapanmaz | `WP-9 FAIL` | no |
| `NO-GO - Release Controls Retention` | output parity kapanir ama must-close release controls korunamaz | `WP-10 FAIL` | no |
| `NO-GO - Cutover / Rollback` | parity ve retention kapanir ama rehearsal/rollback zinciri acilamaz | `WP-11 FAIL` | no |

Secim nedeni:
- `faz1-50 = PASS`
- `v2-95 = PASS`
- `v3-170 = FAIL`
- blocker yalniz `raw_answer_hash_mismatch_count = 32` ve `preprojection_hash_mismatch_count = 32`
- upstream stage mismatch yok
