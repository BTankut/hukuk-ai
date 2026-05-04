# Phase 24O-B TUZUK-04 Temporal Guard Audit

Final targeted run:

```text
reports/benchmark/runs/phase_24O_targeted_shadow_smoke_20260504T094600Z
```

## Questions Required By Brief

- Is selected source historical/repealed? Yes for the user-facing answer surface. The runtime selected `Radyasyon Güvenliği Tüzüğü / 859727 m.4`; although corpus metadata exposed active-looking spans, the question asks about old tüzük use for 2026 compliance.
- Is query current-law framed? Yes. The question includes old tüzük scanning and 2026 compliance/current-law risk.
- Is current-law supporting source present? Only weakly. The retrieved bundle contains historical/source-local tüzük spans and other support, but no complete current-law companion chain sufficient to answer a 2026 compliance question as current law.
- Is answer claiming old tüzük as active? No after Phase 24O-B fix. Final targeted smoke claims `MULGA / 859727 m.4 / repealed` and uses `repealed_transition_answer`.
- Can system safely answer with historical caveat + insufficient current-law evidence? Yes. That is the implemented behavior.

## Implemented Fix

`answer_synthesis.py` now applies a generic temporal guard for active-looking `tuzuk` evidence when the question has historical/current-law risk surface (`eski`, `2026`, `uyum`, `guncel`, `yururluk`). The guard does not mention `TUZUK-04` and does not branch on the benchmark QID.

Before the last patch, the answer said "Seçili aktif kaynak". After the patch:

```text
answer_mode = repealed_transition_answer
source_family_claimed = MULGA
source_identifier_claimed = 859727 m.4
effective_state_claimed = repealed
s7m_historical_repeal_proof_contract_applied = True
```

## Decision

Accepted as a safe systemic runtime fix. It prevents old tüzük material from being surfaced as standalone active current-law authority when the question itself frames a current-law risk.
