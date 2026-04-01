# RC-R Canli Test Runbook 2026-04-01

## Kontrat

- candidate_under_test = `RC-R`
- shadow_control = `RC-G`
- diagnostic_control = `RC-J`
- operation_mode = `offline_only`
- immutable_audit_required = `true`
- citation_visible_required = `true`
- refusal_visible_required = `true`
- rollback_target = `RC-G canonical answer lane`
- hard_fail_trigger = `any_authority_breach_or_any_model_visible_delta_or_any_runtime_error`

## Exact Calistirma Sirasi

1. Pre-run authority/parity/retention check calistir.
   - `RC-G vs RC-J current authority check`
   - `RC-G vs RC-R full-family model-visible surface parity`
   - `RC-R release-controls retention check`
   - Bu uc adimda herhangi bir mismatch veya retention fail varsa teste baslama.

2. `RC-R` answer lane aktif olsun.
   - Active answer lane `RC-R` olarak dogrulanacak.
   - Frozen corpus disina cikan hicbir source acilmayacak.

3. `RC-G` shadow control paralel kayit alsin.
   - Her tek-turn soruda `RC-G` shadow cevabi ayni oturum kaydina alinacak.
   - Hash eslesmesi anlik kontrol edilecek.

4. Her soru tek tek elle girilsin.
   - BT blogu exact `12` soru, sira degismeden.
   - Ic operator blogu exact `18` soru, atanan operator ve sira degismeden.
   - Tum oturumlar `single_turn_only`.

5. Her oturum sonunda su artefact'lar zorunlu uretilsin:
   - raw response export
   - citation capture
   - refusal capture varsa refusal snapshot
   - immutable audit record id
   - replay token

6. Her oturum sonunda shadow parity kontrol edilsin.
   - `model_request_payload_hash`
   - `retrieval_request_hash`
   - `assembled_context_hash`
   - `preprojection_hash`
   - `raw_answer_hash`
   - `response_envelope_hash`
   - Herhangi biri mismatch ise test aninda durdur.

7. Herhangi bir hard-fail olursa test aninda durdurulsun.
   - any_authority_breach = true
   - any_model_visible_delta = true
   - any_runtime_error = true
   - supported soruda visible citation yok
   - refusal beklenen soruda supported cevap dondu
   - legal_overreach_present = true

8. Test bittikten sonra full-family parity yeniden kosulsun.
   - `faz1-50`
   - `v2-95`
   - `v3-170`
   - Tum mismatch count alanlari exact `0` olmali.

9. Retention check yeniden kosulsun.
   - `must_close_release_controls_pass = true`
   - `retained_after_family_eval = true`
   - `retained_after_restart = true`
   - `retained_after_restore = true`

10. Final kabul raporu doldurulsun.
   - `live_test/rc_r_insan_skorkarti_2026_04_01.md`
   - `live_test/rc_r_gercek_dunya_testi_final_kabul_raporu_2026_04_01.md`
   - Karar yalniz su ikisinden biri olacak:
     - `PASS - RC-R Observed Real-World Acceptance Closed`
     - `NO-GO - RC-R Observed Real-World Acceptance Failed`
