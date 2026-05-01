# Phase 22F-R Relation Metadata Audit

Date: 2026-05-01

## Scope

This audit checks whether the Phase 22F shadow collection contains enough relation metadata to build a deterministic source chain for historical/repealed applicability questions.

Target collection:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

Candidate runtime:

```text
http://127.0.0.1:8018/v1
```

Live `8000` was not modified.

## Sources Audited

Required chain:

- Historical source: `16532` / 2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği
- Repeal instrument: `rg20230311-4`
- Current-law basis: `2547 m.54`

CSV detail:

```text
reports/benchmark/phase_22F_R_relation_metadata_audit.csv
```

## Milvus Payload Findings

Historical source row example:

```text
source_identifier=16532
madde_no=22
effective_state=historical_repealed
bridge_role=historical_repealed_source
relation_type=historical_repealed_to_current_bridge
repealed_by_source_id=yok_disc_2023_repeal
current_law_basis_source_id=law_2547_current
```

Repeal instrument rows:

```text
source_identifier=rg20230311-4
effective_state=repeal_instrument
bridge_role=repeal_instrument
relation_type=repeals_historical_regulation
repealed_source_id=yok_disc_2012_regulation
```

Current-law basis row:

```text
source_identifier=2547
madde_no=54
effective_state=active
bridge_role=current_law_basis
relation_type=current_law_basis_for_repealed_discipline_regulation
historical_source_id=yok_disc_2012_regulation
repeal_source_id=yok_disc_2023_repeal
```

## Retrievability

The relation graph exists in the Milvus payload and is queryable through nested JSON metadata:

```text
metadata["relation_metadata"]["repealed_source_id"] == "yok_disc_2012_regulation"
metadata["relation_metadata"]["historical_source_id"] == "yok_disc_2012_regulation"
metadata["bridge_role"] == "repeal_instrument"
metadata["bridge_role"] == "current_law_basis"
```

Direct source retrieval is also available by public identifiers:

```text
metadata["source_identifier"] == "16532"
metadata["source_identifier"] == "rg20230311-4"
metadata["source_identifier"] == "2547" && metadata["madde_no"] == "54"
```

The internal relation IDs (`yok_disc_2023_repeal`, `law_2547_current`, `yok_disc_2012_regulation`) are relation-local IDs, not direct `source_identifier` values. Runtime expansion must therefore use relation metadata lookup, not only source-key lookup.

## Evidence Bundle Use

Current evidence bundle behavior:

- Initial Phase 22F smoke selected unrelated `832 m.98`; the YOK source chain was not used.
- Non-law routing mini-patch smoke selected the correct historical YOK regulation document, but did not promote `rg20230311-4` or `2547 m.54` into the controlling evidence bundle.
- No `relation_chain_*` trace fields are present yet.

## Acceptance

Relation graph existence:

```text
CONFIRMED
```

Relation metadata available in Milvus payload:

```text
CONFIRMED
```

Relation metadata used in current evidence assembly:

```text
DENIED
```

Decision:

```text
Proceed to Phase 22F-R-B source-chain retrieval design.
```

