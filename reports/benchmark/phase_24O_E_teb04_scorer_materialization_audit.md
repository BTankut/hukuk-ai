# Phase 24O-E TEB-04 Scorer / Materialization Audit

Final targeted run:

```text
reports/benchmark/runs/phase_24O_targeted_shadow_smoke_20260504T094600Z
```

## Audit

Final runtime selected:

```text
source = 19631 / Katma Değer Vergisi Genel Uygulama Tebliği
article = m.0
metadata_lookup_source = teb_kdv_source_identity_lookup
score = 0.00 FAIL
failure = auto_fail_triggered | missing_required_content_signal | partial_grounding_only
```

The source identity is fixed: the selected source is the KDV Genel Uygulama Tebliği. The remaining blocker is section/span materialization. The retrieved span is document-level `19631 m.0` and contains appendix-style content such as `EK 23/B`, not the relevant tevkifat/iade section.

Legal review already stated that the official consolidated KDV Genel Uygulama Tebliği is the correct primary source for KDV tevkifat/iade questions, but exact section span is still required.

## Decision

No runtime patch was applied. A safe runtime patch requires section-level materialization for the relevant KDV GUT parts. Until then, accepting `19631 m.0` as enough would hide a real evidence-span gap.

## Next Required Work

- Materialize relevant KDV GUT section/article rows for tevkifat/iade.
- Preserve `19631` as the canonical primary source.
- Re-run TEB-04 after section spans are present.
- If scorer still auto-fails after exact section materialization, open scorer/rubric acceptance correction.
