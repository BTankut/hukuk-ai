# Phase 24X-C Family/Domain Compatibility Gate Design

## Scope
- Purpose: prevent wrong primary-source locks caused by metadata-first source identity, while preserving supporting-source evidence.
- Runtime status: design only; no live `8000` change.
- Constraint: no QID-specific branch, no benchmark answer key use, no answer-surface override.

## feature_flag_name
- `ENABLE_PHASE24X_FAMILY_DOMAIN_COMPATIBILITY_GATE`
- Default: `false`.
- Prototype scope: non-live process only. Live `8000` must remain unchanged.

## compatibility_gate_rules
1. Run the gate only after metadata-first source candidates have been scored and before candidates are converted into primary source locks or rerank focus keys.
2. Treat a candidate as primary-eligible only if at least one primary identity anchor is satisfied: exact identifier requested as primary, strong title/domain overlap, issuer/authority anchor, relation query primary-family anchor, or allowed cross-family relation.
3. For title-only metadata candidates, require domain-specific title terms to be supported by the query. Generic terms such as consumer, rights, regulation, procedure, principles, implementation, law, or management are not enough.
4. If an explicit identifier appears in a support/negative frame such as "sadece X yetmez", "yalnız X eksik", "X'e bakmak neden eksik", or "hangi yönetmelik de devreye girer", that identifier must be demoted to supporting-source role and must not primary-lock the source pool.
5. If the query asks for a source family directly, for example "hangi yönetmelik", "hangi tebliğ", "hangi CBK bağını", or "hangi kanun", candidates from another family cannot become primary unless an allowed cross-family relation marks them as the requested primary or required companion.
6. The gate must not delete evidence. It can block a candidate from primary-source lock, demote it to supporting-source role, or leave it primary-eligible.
7. If all metadata-first candidates are blocked from primary lock, retrieval must fall back to non-metadata dense/family selection rather than returning insufficient evidence immediately.
8. Existing temporal/repealed rules remain authoritative. The gate must not revive repealed sources unless current temporal policy already permits historical or repealed analysis.

## allowed_cross_family_relations
- `kanun -> yonetmelik`: allowed when the query asks for implementing regulation, application detail, or "kanun alone is insufficient"; the kanun is supporting unless the question asks the law as primary.
- `yonetmelik -> kanun`: allowed when the regulation cites a statutory basis or the user asks for dayanak kanun; the regulation remains primary if the requested answer is operational/regulatory.
- `cb_kararname -> yonetmelik`: allowed as institutional authority/supporting chain when the query asks for a primary regulation plus CBK link.
- `yonetmelik -> cb_kararname`: allowed only when the query asks the CBK as the primary institutional source.
- `teblig -> kanun`: allowed for tax/statutory basis support; tebliğ remains primary when the query asks for the applied/consolidated tebliğ.
- `kky -> yonetmelik`: allowed as internal family mapping when the source is regulation-like, but still subject to title/domain support.
- `mulga/historical -> active`: allowed only under existing temporal policy when the user asks historical/repealed applicability or transition analysis.

## blocked_cross_family_relations
- Law-family exact identifier cannot primary-lock a regulation-seeking query when the identifier is framed as insufficient or only supporting.
- Sector-specific regulation cannot primary-lock a title-only metadata match when its sector/domain title terms are absent from the query.
- CBK cannot primary-lock a query that asks for a "temel yönetmelik" and only asks the CBK as a chain/link.
- Generic regulation terms cannot bridge unrelated domains, for example consumer-rights words alone cannot bridge custom furniture/distance-sale issues to electronic-communications regulation.
- Support-family candidates cannot displace an explicitly requested family merely because metadata lookup gives exact identifier or high title score.

## supporting_source_policy
- Supporting sources stay available for evidence assembly, citation chain, and legal context.
- Supporting candidates must carry a trace role: `supporting_source`, `primary_candidate_blocked`, or `primary_candidate_demoted`.
- Demotion is preferred over deletion when the source may still be legally relevant, such as statute basis, CBK institutional basis, or tax code basis.
- Supporting evidence must not satisfy the governing-source slot by itself unless no primary source exists and answer mode explicitly states insufficient/qualified grounding.

## primary_source_preservation_policy
- Preserve the current primary source if it satisfies strong title/domain overlap and family request alignment.
- Preserve exact identifier primary selection when the query asks that identifier directly, not when the identifier is described as incomplete or insufficient.
- Preserve high-confidence metadata-first selection for `KKY-01`-like cases where banking/electronic-banking domain tokens in the query strongly overlap the selected regulation title.
- Preserve `TEB-04`-like tebliğ selection where the query explicitly asks for the main/consolidated tebliğ and includes domain tokens such as KDV, tevkifat, iade, tebliğ.
- Do not preserve `KANUN-08`-like sector-title matches where the selected title's sector terms are absent from the scenario.

## trace_fields_to_add
- `phase24x_family_domain_gate_enabled`
- `phase24x_candidate_primary_role`: `primary_eligible`, `supporting_source`, `primary_candidate_demoted`, `primary_candidate_blocked`
- `phase24x_candidate_block_reason`
- `phase24x_requested_primary_family`
- `phase24x_support_identifier_context`
- `phase24x_title_domain_terms`
- `phase24x_query_domain_terms`
- `phase24x_allowed_cross_family_relation`
- `phase24x_blocked_cross_family_relation`
- `phase24x_fallback_after_all_metadata_candidates_blocked`

## Required Examples
| qid | current failure/protection need | gate behavior |
|---|---|---|
| `KANUN-08` | `24039` electronic-communications regulation wins through generic consumer-regulation title terms while scenario asks custom furniture/distance-sale/cayma exception. | Block/demote `24039` from primary because sector title terms are not query-supported; allow fallback to dense/family selection. |
| `YON-05` | `3194` exact identifier becomes primary even though the query says only 3194 is insufficient and asks which regulation must also be used. | Demote `3194` to supporting-source role; keep regulation-family candidates primary-eligible, including `23722` if present. |
| `CBY-04` | Query asks for the basic regulation and its CBK institutional link; CBK can be over-selected as governing source. | Keep CBK as support chain; primary should remain regulation-family unless the user asks CBK as the primary source. |
| `KKY-01` | Correct regulation-like/banking source has strong banking and electronic-banking domain overlap. | Do not block; high title/domain overlap and requested management/risk context preserve primary selection. |
| `TEB-04` | Query explicitly asks the main consolidated KDV tebliğ instead of older special rulings/circulars. | Do not block; explicit tebliğ family and KDV domain terms preserve primary selection, with statutes only as support if needed. |

## Prototype Safety Decision
- Safe to prototype under a default-off flag because the gate can be applied before source locks are created and can operate only on traceable metadata/family/domain signals.
- Prototype must stop if it requires QID-specific conditions, answer-key inspection, live `8000` modification, or removal of support-source evidence.

