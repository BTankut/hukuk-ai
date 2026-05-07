# Phase 24HT-C Non-Live Prototype Report

## Prototype

Implemented a feature-flagged same-family source identity lock:

- flag: `ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true`
- implementation: `api-gateway/src/rag/article_span_selection.py`
- runtime bridge: `api-gateway/src/routers/chat.py`
- tests: `api-gateway/tests/test_chat_router.py`

The prototype passes the existing `source_identity_reranker` trace into article span selection. If the user did not explicitly ask for a law/article, and source identity has a strong same-family dual-lane document signal, article selector may replace a weaker selected-source lock with `same_family_domain_identity_lock`.

## Guard Conditions

The override is blocked when any of these are present:

- explicit article token
- explicit law/source identifier token
- numbered law mention
- explicit article reference
- relation query
- legacy/historical scope arbitration
- source identity not applied
- target source identity score below `45`
- no dual-lane confirmation
- target document absent from article candidate pool
- target document lacks span-level support
- target/current documents are not same-family compatible
- source identity margin below `20`

## Tests

Passed targeted unit test command:

```bash
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k 'phase24ht or article_span_selector_keeps_requested_family_ahead_of_cross_family_article_hit'
```

Result: `3 passed, 326 deselected`.

Added coverage:

- natural same-family query can move from a generic KANUN selected-source lock to the stronger domain KANUN source identity document.
- explicit `TBK m.255` query remains locked to TBK and is not overridden.

Full `api-gateway/tests/test_chat_router.py` was also run. It currently reports `319 passed, 10 failed`. The failing tests are outside the Phase24HT change path and also fail when representative failures are run in isolation. They are recorded as residual repository test debt, not as Phase24HT-specific failures.

## Production Safety

No live `8000` change was made. The flag defaults to off, and the prototype was exercised only on non-live candidate port `8042`.
