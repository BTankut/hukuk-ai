# FAZ38 RC-Q Contract-Surface Audit Matrix

| audit_row | expected_value | actual_value_capture_a | actual_value_capture_b | pass | impact_rowset |
| --- | --- | --- | --- | --- | --- |
| candidate_manifest_hash_equal | equal | e3f4db73953ab9ab035af614a6f6d4feee4f1fcd6d50a616ce0ab7abb474ec7b | e3f4db73953ab9ab035af614a6f6d4feee4f1fcd6d50a616ce0ab7abb474ec7b | true | none |
| canonical_topology_hash_equal | equal | 613fee61225ec1de08dcdbdd46165a2797d71b96a53db2cbd155dc6c6c6feb33 | 613fee61225ec1de08dcdbdd46165a2797d71b96a53db2cbd155dc6c6c6feb33 | true | none |
| reference_pack_hash_equal | equal | fa9db7cf2c155c0acfe829345877acb5997e3809b7215c20d5d0b413c3df50aa | fa9db7cf2c155c0acfe829345877acb5997e3809b7215c20d5d0b413c3df50aa | true | none |
| family_pack_hash_equal | equal | 30164887bdf8bd10a18cfb6038633444b394ffbfcdac5d269e113e893d8c871b | 30164887bdf8bd10a18cfb6038633444b394ffbfcdac5d269e113e893d8c871b | true | none |
| frontier_membership_hash_equal | equal | b5a8ffb3b9f0f9f647f5dc4833ca08450aad91eb8d0eeba851ea80051b1eb286 | 4f4120a44b5008f18c8b3da16710fb5a61a4d6d0796aaae9e95910b5ec636f2e | false | frontier_instability_rowset_6 |
| frontier_row_order_hash_equal | equal | 27b7f52e48cad0894d39a5ba28ac5cf7dfd0e2d1880d58e79a82cc85cd6f518d | 27b7f52e48cad0894d39a5ba28ac5cf7dfd0e2d1880d58e79a82cc85cd6f518d | true | none |
| response_envelope_subfrontier_hash_equal | equal | 2006a8a9ec5eac2b6ec97b94dd29c3401eff1482cf52c0b0be8eead07388a8e9 | 94a95ac3fd3b4098978b3ed97faacdcf37e40998cc6af267f822b1da24dc5c0c | false | response_envelope_instability_rowset_3 |
| response_envelope_subfrontier_row_order_hash_equal | equal | 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945 | 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945 | true | none |
| full_family_pack_hash_equal | equal | 5395abbb66a9f7ae36d237ab4b06442c44d1c3c1611a65c893ef89abd7d31e34 | 19dcee891ded85569521fecbbcbf1c3cdd142acbfafba7840ebc46ac52831a53 | false | full_family_instability_rowset_3 |
| preprojection_materialization_contract_hash_equal | equal | 75c60d802d23bbcb5e0198c4f08a8646d5b7edc17b0e22e3721090da3195064f | d69ec4179ab7a3d462fb0edbbf38b9115d469b875c3c3e5b3341242c5db09432 | false | frontier_instability_rowset_6 |
| raw_answer_materialization_contract_hash_equal | equal | b852d94b908ae0672e3f70572316395f633ccc5977f7c5b0336380c5d68d48d9 | 2007fe995a3a89dbde6a2fc1295ebfc1913acc24072db76d82182910e82fe354 | false | frontier_instability_rowset_6 |
| response_envelope_materialization_contract_hash_equal | equal | f314ab9a667c71c4b17164922afba434c3d40218c8cb1a2b7909f278782ea5da | a7462dac1505c9e2e5fe2bd0ace938bd155885836f1d0baf97c27a2297e5fc7d | false | frontier_instability_rowset_6, response_envelope_instability_rowset_3 |
| targeted_acceptance_contract_hash_equal | equal | 8256ab2c6cf3b7ecc0a438e3a4d744f21cabd9efa07460b98d4d6982bbd70e66 | 8256ab2c6cf3b7ecc0a438e3a4d744f21cabd9efa07460b98d4d6982bbd70e66 | true | none |
| retention_contract_hash_equal | equal | 9651c44a52d27b25164510ee417f385216de3746637d13e19ff34dacb1da9485 | 9651c44a52d27b25164510ee417f385216de3746637d13e19ff34dacb1da9485 | true | none |
| final_truth_projection_contract_hash_equal | equal | 1e9d5b8cd84f35183aff747df8622b56238f60313235b5d9ed9c2b92305ba100 | 2b1a4f02846a9b53c3696df7b5e1d947c6c073655c8c06b8b5f13467d593276e | false | frontier_instability_rowset_6, response_envelope_instability_rowset_3, full_family_instability_rowset_3 |
| runtime_override_present | false | false | false | true | none |
