# Phase 22E-B Corpus Backfill Plan

Input:

- `reports/benchmark/phase_22E_P0_legal_corpus_truth_packet.md`
- `reports/benchmark/phase_22E_P0_legal_corpus_truth_packet.csv`

Runtime behavior was not changed. No live collection update was performed.

## Backfill Items

| QID | Source / Gap | Backfill Type | Target |
| --- | --- | --- | --- |
| MULGA-01 | `16532` regulation is body-bearing but catalog state is stale; repeal/current-law transition is missing. | Source catalog effective-state correction, repeal instrument acquisition, 2547 m.54 bridge materialization. | Shadow collection only. |
| TEB-06 | `23093` tebliğ source is visible but selected spans are title-only/body=0. | Official source acquisition, deterministic body extraction, article/span materialization. | Shadow collection only. |

## Required Backfill Controls

- Use only official/public source text.
- Record raw source URL, retrieval timestamp, and SHA-256 hash before parsing.
- Keep raw source, normalized text, parsed articles, and generated canonical keys together in a provenance bundle.
- Generate `canonical_source_key_v2` and `binding_source_key` before indexing.
- Do not overwrite `mevzuat_faz1_shadow_20260418_compat1024`.
- Build shadow collection:

```text
mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

- Validate with P0 smoke before any full benchmark.

## MULGA-01 Implementation Plan

1. Acquire the official 2012 regulation text for `Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği`.
2. Acquire the repeal instrument published on `2023-03-11`, RG `32129`.
3. Verify current legal basis around `2547 sayılı Kanun m.54`.
4. Update shadow source catalog so `16532` is not treated as directly active for the 2026 reference date.
5. Materialize a transition/current-law bridge record that lets runtime distinguish:
   - historical regulation text,
   - repeal/currentness status,
   - current statutory basis.
6. Reindex only into the P0 shadow collection.

Validation QIDs:

```text
MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05
```

## TEB-06 Implementation Plan

1. Acquire the official body text for `Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ`, RG `29910`, date `2016-12-06`.
2. Legal review must confirm whether benchmark expected source is:
   - the 2016 company-formation tebliğ `23093`,
   - a separate `Ticaret Sicili Tebliği`,
   - or a source chain with `6102 sayılı Türk Ticaret Kanunu` / Ticaret Sicili secondary regulation.
3. Extract article-level body spans for 23093, especially article range around company contract preparation/signing/application.
4. Do not promote title-only `23093` spans before materialization.
5. Reindex only into the P0 shadow collection.

Validation QIDs:

```text
TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08
```

## Acceptance Before Any Runtime Switch

```text
MULGA >= 4/5
TEBLIGLER >= 7/8 preferred, >=6/8 minimum
unsupported_confident_answer = 0
contract_valid = all rows
source_key_v2_collision = 0
binding_collision = 0
```

## Rollback Plan

No live rollback should be necessary because Phase 22E-B does not touch live collection. If optional Phase 22E-C shadow backfill is attempted and fails, delete the shadow collection and discard the generated shadow catalog/provenance bundle.

CSV: `reports/benchmark/phase_22E_corpus_backfill_plan.csv`

