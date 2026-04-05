# RC-S Full Corpus Integrated Retrieval Contract 2026-04-05

## Active Retrieval Surface

- active_source_set = `[TMK core corpus, TCK, HMK, CMK, TTK, İK]`
- source_priority_rules = `question must stay inside its matched source-class scope; primary source must come from the matched active source set; no fallback to excluded source classes`
- cross_law_separation_expectation = `cross-law bleed is not allowed; source routing and citation scope must remain law-local`
- citation_visibility_required = `true`
- refusal_visibility_required = `true`
- answer_path_changed = `false`

## Measurement Method

- official_base = `RC-R`
- evaluation_surface = `frozen RC-R runtime + accepted source-class canary retrieval surfaces only`
- new_execution_authorized = `false`
- embedding_generation_started = `false`
- index_build_started = `false`
- vector_db_write_started = `false`

## Integrated Gate Expectations

- integrated_behavior_question = `Does the accepted six-source set preserve source correctness, usable citation behavior, and zero-delta invariants under frozen RC-R?`
- wrong_primary_source_allowed = `false`
- cross_law_confusion_allowed = `false`
- runtime_error_allowed = `false`
- silent_refusal_on_supported_question_allowed = `false`

## Excluded Inputs

- excluded_source_classes = `[Yargıtay İçtihat Merkezi (YİM), customer/private documents, external internet-derived ad hoc content]`
