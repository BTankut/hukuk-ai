# Phase 8 Selector/Scorer Semantics

## Canonical Article Alignment Enum

`article_alignment = exact | neighbor | title_only | clause_only | none | unknown`

## Metric Definitions

| metric | measurement point | input source | comparison | boundary |
| --- | --- | --- | --- | --- |
| selector_exact_article_hit_rate | pre-generation selector | trace.retrieval.article_span_selector.selector_exact_article_hit | query explicit article vs selected evidence article | true only when the query explicitly names an article and selector chooses that article |
| query_article_alignment | pre-generation selector | trace.retrieval.article_span_selector | query article tokens vs selected evidence article | exact/neighbor/title_only/clause_only/none/unknown |
| article_alignment | post-generation benchmark extraction | candidate/scored CSV | selected evidence article vs answer_contract claimed article | exact/neighbor/title_only/clause_only/none/unknown |
| selected_article_equals_claimed_article | post-generation benchmark extraction | selected_article + article_or_section_claimed | canonical token equality | equality signal; exact semantic excludes article 0 title-only rows |
| avg_article_match_score | scorer | private answer key + answer contract | gold article vs claimed article | only applies when gold key has article signal; otherwise document hit drives score |
| wrong_article | scorer | private answer key + answer contract | gold article vs claimed article | emitted only when gold article exists and claimed article differs/missing |
| right-document wrong-article/span backlog | coverage/backlog forensics | scored CSV + trace | document visible but content/rubric/span still incomplete | backlog owner signal, not equivalent to wrong_article |

## Boundary Rules

- `exact`: canonical article tokens match and are not article `0`.
- `neighbor`: both sides have numeric article tokens with distance 1.
- `title_only`: article `0`, title-only source support, or source-local support without exact span lock.
- `clause_only`: paragraph/bent/clause signal exists but article token is absent.
- `none`: both sides expose article tokens but they are not equal or neighbor.
- `unknown`: no comparable article signal exists.

## Phase 7 Mismatch Resolution

The apparent Phase 7 contradiction is resolved by separating measurement points. `selector_exact_article_hit_rate=0.0` measures explicit query article locks before generation. `avg_article_match_score=0.82` measures claimed article against sparse private gold article keys. `right-document wrong-article/span backlog=74` measures broader content/span incompleteness. These are related but not interchangeable metrics.
