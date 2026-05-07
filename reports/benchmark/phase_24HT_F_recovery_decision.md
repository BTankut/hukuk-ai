# Phase 24HT-F Recovery Decision

## Decision

Option B: same-family scoring improves but the candidate remains insufficient.

## Basis

- KANUN-08 moved from `TÜRK BORÇLAR KANUNU / TBK m.255` to `TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18`.
- Phase24HT trace shows `same_family_domain_identity_lock` applied with margin `42.0305`.
- Focused smoke has no contract, unsupported-answer, source-key-v2, or binding-collision regression.
- Guard rows match Phase24HS v6 outcomes.
- KANUN-08 still fails because the secondary `YONETMELIK` evidence path and exception span role are not recovered.

## Productization Decision

Do not productize this candidate.

## Internal Eval Decision

Do not open internal eval.

## Fine-Tuning Decision

Do not fine-tune.

## Next Recommended Phase

Open a targeted KANUN-08 source-role retrieval and secondary-family recall phase:

- preserve the Phase24HT same-family source identity guard as a diagnostic candidate feature;
- audit why public `secondary_types=YONETMELIK` does not survive into KANUN-08 retrieval selection;
- recover distance-sales/custom-production exception evidence without QID-specific logic;
- verify that primary KANUN and supporting YONETMELIK roles are represented separately in trace and answer slots.
