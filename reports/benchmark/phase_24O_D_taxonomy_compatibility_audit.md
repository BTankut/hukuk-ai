# Phase 24O-D Taxonomy Compatibility Audit

Final targeted run:

```text
reports/benchmark/runs/phase_24O_targeted_shadow_smoke_20260504T094600Z
```

## CBY-04

Final selected document:

```text
source = Devlet Arşivleri Başkanlığı Hakkında Cumhurbaşkanlığı Kararnamesi
identifier = 11 m.10
score = 7.12 PASS
failure residual = wrong_family | hallucinated_identifier | partial_grounding_only
```

The runtime answer is usable enough for the targeted gate, but this is a taxonomy/scorer compatibility issue. The code must not relabel a `CB_KARARNAME` primary source as `CB_YONETMELIK` merely to satisfy a benchmark bucket. Supporting regulation/decision chains may be exposed separately, but they must not overwrite the legal family of the primary selected source.

## KKY-01

Final selected document:

```text
source = Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik
identifier = 34360 m.1
legal family = YONETMELIK
score = 6.65 FAIL
failure residual = wrong_family | hallucinated_identifier | partial_grounding_only
```

Legal family is yönetmelik. `KKY` is a benchmark bucket / domain label, not necessarily the legal source family. Runtime relabeling would be misleading.

## Decision

No runtime relabel patch was applied. The safe policy is:

- Keep `source_family` as legal family.
- If needed later, add a separate issuer/domain alias field for benchmark taxonomy compatibility.
- Do not let supporting source family overwrite primary claimed family.
