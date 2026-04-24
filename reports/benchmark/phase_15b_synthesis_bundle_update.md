# Phase 15B Synthesis Bundle Update

- change: add `[KANIT-CEVAP SLOT TALİMATI]` to the RAG answer query after article/span selection.
- purpose: force the model to answer required task slots from selected evidence instead of giving a generic but confident conclusion.
- scope: systemic task-type slot guidance; no QID-specific rules.

## Runtime Behavior

- The hint is built from `_answer_template_for_query` and `_must_have_fact_slots_for_query`.
- The hint carries selected article, support span count, and selector evidence sufficiency when available.
- The model is instructed to state insufficient source support for missing slots rather than infer beyond selected evidence.

## Expected Impact

- Better answer-slot completeness where the correct document/span is already selected.
- More explicit qualified answers when selected evidence is weak.
- No intended change to retrieval routing or family/document selection.
