# Phase 25A Judicial Decisions Corpus Architecture

Generated: 2026-05-08

## Core Principle

Judicial decisions must not be mixed into the mevzuat corpus through the same source identity field.

Use a separate corpus, separate metadata schema, separate retrieval lane, and separate citation/verification policy. Judicial decisions can support interpretation and court-practice answers, but they must not override the primary legal rule from mevzuat unless the user explicitly asks for case-law interpretation, court practice, precedent, or application examples.

## Target Architecture

```text
User Query
  -> Legal Query Router
  -> Mevzuat Retriever
  -> Judicial Decision Retriever
  -> Evidence Role Merger
  -> Claim-Level Verifier
  -> Answer Synthesizer
```

## Corpus Separation

| dimension | mevzuat corpus | judicial decisions corpus |
| --- | --- | --- |
| primary function | controlling statutory/regulatory rule | interpretation, application, precedent, conflict signal |
| source identity | statute/regulation/communique/decree identity | court, chamber, date, case no, decision no |
| retrieval lane | mevzuat retrieval lane | judicial retrieval lane |
| citation policy | legal source title + article/span + effective status | court/chamber + date + case/decision no + publication source |
| verification focus | article/source family/effective-state consistency | case identity, holding relevance, topic/statute linkage, outlier/conflict marking |
| default priority | primary source for legal rule | supporting source unless user asks for case-law/court practice |

## Judicial Metadata Schema

| field | requirement |
| --- | --- |
| `court` | Court name, normalized and raw-preserved. |
| `chamber` | Chamber/department/board identifier where available. |
| `decision_date` | ISO date when extractable; raw date retained separately if parse confidence is low. |
| `case_no` | Case/docket number, raw and normalized. |
| `decision_no` | Decision number, raw and normalized. |
| `legal_topic` | Controlled topic labels, initially dry-run generated and manually sampled. |
| `statute_refs` | Referenced statute/source identifiers extracted from decision text. |
| `article_refs` | Referenced article numbers linked to statute refs when possible. |
| `precedent_weight` | `binding`, `strong_persuasive`, `persuasive`, `weak`, `unknown`, or `outlier`. |
| `finality_status` | `final`, `not_final`, `unknown`, or source-specific status. |
| `publication_source` | Official or acquired publication location and acquisition channel. |
| `raw_sha256` | SHA-256 of raw source file/text used for provenance. |
| `document_id` | Stable internal document id. |
| `canonical_case_key` | Deterministic key from court/chamber/date/case_no/decision_no. |
| `citation_label` | Human-readable citation label used in answer output. |

## Judicial Evidence Roles

| role | meaning | serving rule |
| --- | --- | --- |
| `precedent` | A decision used as precedent or strong legal authority. | Requires high identity confidence and relevance. |
| `interpretation` | Explains how a statutory/regulatory text is interpreted. | Must be linked to a mevzuat primary rule. |
| `application_example` | Shows how courts applied a rule to facts. | Must not be phrased as the rule itself. |
| `conflict_signal` | Shows conflict, split, reversal, or instability in practice. | Must trigger qualified answer language. |
| `court_practice` | Describes recurring court practice. | Requires multiple decisions or explicit caveat if single decision. |
| `minority_or_outlier` | Isolated or low-weight authority. | Cannot drive conclusion unless user explicitly asks for outliers. |

## Mevzuat Evidence Roles

| role | meaning |
| --- | --- |
| `primary_rule` | Main statutory/regulatory rule governing the answer. |
| `definition` | Definition provision. |
| `procedure` | Procedural rule or required step. |
| `exception` | Exception or carve-out. |
| `temporal_validity` | Effective-state, amendment, repeal, or transitional rule. |
| `current_law_basis` | Current-law source that anchors the answer. |
| `historical_source` | Repealed or historical source used only when appropriate. |

## Query Routing Policy

| query intent | mevzuat retriever | judicial retriever | answer posture |
| --- | --- | --- | --- |
| asks legal rule only | required | optional only if confidence requires interpretation context | cite mevzuat as controlling source |
| asks court practice | required for underlying rule | required | separate rule from court practice |
| asks precedent / içtihat | required for legal basis | required | answer with precedent role and caveats |
| asks historical legal state | required with temporal role | optional | state effective period and uncertainty |
| asks factual lawsuit strategy | required if legal source exists | optional with caution | legal-information only; no attorney-client advice |

## Evidence Role Merger

The merger must preserve corpus identity:

- mevzuat evidence can satisfy `primary_rule`, `definition`, `procedure`, `exception`, `temporal_validity`, `current_law_basis`, and `historical_source`
- judicial evidence can satisfy `precedent`, `interpretation`, `application_example`, `conflict_signal`, `court_practice`, and `minority_or_outlier`
- one evidence item must not be recast into another corpus role without explicit verifier approval
- every synthesized answer must expose which claims are mevzuat-grounded and which are judicial-decision-grounded

## Claim-Level Verification Policy

Verification must check:

- case identity fields match the cited judicial document
- cited judicial decision actually supports the interpretation or application claim
- statute/article references in the decision do not become primary mevzuat authority by themselves
- outlier/conflict signals downgrade confidence rather than being hidden
- repealed/historical mevzuat remains separate from judicial interpretation of current law

## Required Warning

Do not let judicial decision source override mevzuat primary legal rule unless the answer explicitly asks for court practice, case-law interpretation, precedent, or application examples.

## Phase25A Status

Architecture status: `designed`.

Ingestion status: `dry_run_only`.

Production index status: `not_authorized`.

Live retrieval status: `not_authorized`.

Merge with mevzuat status: `not_authorized`.
