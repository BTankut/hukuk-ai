# Phase 24R-E CBY Merge Decision

## Decision

```text
selected_option = Option A - CBY collection is merge-safe
open_future_controlled_cutover_or_merge_brief = true
auto_cutover = false
live_8000_modified = false
```

Phase24R produced a clean matched BASE-vs-CBY A/B pair. The only material runtime difference was `MILVUS_COLLECTION`.

## Evidence

```text
BASE_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
CBY_COLLECTION = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
BASE raw_score_proxy = 725.40
CBY raw_score_proxy = 727.18
raw_score_delta = +1.78
BASE pass_proxy = 72
CBY pass_proxy = 73
pass_delta = +1
```

Changed row:

```text
CBY-06 = 6.80 FAIL -> 8.58 PASS
```

No unrelated full-run regression was observed in the matched A/B delta.

## Guard Checks

```text
CBY wrong_family <= BASE wrong_family = true
CBY wrong_document <= BASE wrong_document = true
CBY hallucinated_identifier <= BASE hallucinated_identifier = true
CBY contract_valid = 100/100
CBY unsupported_confident_answer = 0
CBY answer_contract_invalid = 0
CBY source_key_v2_collision = 0
CBY binding_collision = 0
```

## Scope Boundary

This decision only says the CBY collection is merge-safe relative to the current matched BASE lane. It does not reopen productization, internal eval, fine-tuning, or live `8000` cutover.

## Required Next Step

Open a future controlled cutover/merge brief if the product owner wants to promote the CBY collection. That future brief must include rollback, live binding verification, post-switch smoke, and trace artifact compliance.
