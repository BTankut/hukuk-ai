# Phase 10D Document Identity Reliability Summary

## Change
- Source identity reranker now gives materially higher weight to exact identifiers, exact title phrases, and strong title overlap.
- Single-token title overlap is no longer treated as a weak title match.
- Generic same-family candidates without title, identifier, or year anchors receive a stronger penalty for the high-risk families.
- Official Gazette date match is surfaced as a positive identity signal.
- Answer contract suppresses selected-evidence identifiers when the user did not request an identifier and the source-identity trace is weak.

## Verification
- `python3 -m py_compile api-gateway/src/routers/chat.py api-gateway/src/answer_contract_v2.py`
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_identity_reranker" -q`
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_answer_contract_v2.py -q`

## Expected Effect
- `title_match_type=weak_overlap` should decrease.
- `hallucinated_identifier` should decrease because low-confidence selected evidence identifiers are no longer promoted into `source_identifier_claimed`.
- Wrong-document rows should shift toward either stronger exact/strong title matches or explicit insufficient-evidence handling.
