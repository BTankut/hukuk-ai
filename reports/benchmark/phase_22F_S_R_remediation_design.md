# Phase 22F-S-R-D Remediation Design
No implementation was performed in this phase. This document defines the next safe implementation scope if Phase 22F-S2 is opened.
## Decision
Recommendation: open Phase 22F-S2 scoped temporal alignment fix. Do not revert the whole Phase 22F-S corpus work yet, and do not productize the shadow candidate.
## Problem Statement
Phase 22F-S fixed the narrow MULGA/current-basis path, but full shadow audit shows temporal claim alignment rewrote active/current-family non-MULGA answers into `MULGA/repealed` claim surfaces. This created new wrong_family and hallucinated_identifier failures without evidence of runtime/model instability.
## Design Rules
- Apply temporal claim alignment only when explicit relation-chain metadata is present, or the primary benchmark family/source family is already `MULGA`.
- Never infer `MULGA` family from historical-scope wording alone for active `KANUN`, `KHK`, `TUZUK`, `TEBLIGLER`, `KKY`, `UY`, `YONETMELIK`, or Cumhurbaşkanlığı sources.
- Preserve selected source family as the claimed primary family unless a verified relation role explicitly makes the historical/repealed source the answer primary.
- Treat repeal/current-law-basis identifiers as supporting-role identifiers; do not let them replace the primary source identifier unless the answer mode is explicitly currentness/repeal-chain.
- If relation metadata is missing, qualify the answer text if needed, but do not rewrite family/effective_state to `MULGA/repealed` for non-MULGA selected evidence.
## Stop Rules
- Stop if any Phase22F-S2 smoke introduces new wrong_family or hallucinated_identifier in non-MULGA rows.
- Stop if `MULGA-01..05` drops below the Phase22F-S targeted smoke result.
- Stop if source_key_v2 or binding collisions become non-zero.
- Stop if live `8000` would be touched; all work stays on shadow candidate.
## Smoke Plan
- First run targeted non-MULGA overapplication set: `KANUN-05`, `KANUN-10`, `KANUN-14`, `KANUN-15`, `KHK-03`, `TEB-03`, `TEB-04`, `TUZUK-03`, `TUZUK-04`.
- Then run guard set: `MULGA-01..05`, `TEB-06`, `CBG-01..04`, `CBKAR-01..08`, `YON-04`, `UY-01`.
- Only after targeted and guard sets pass, run the full shadow benchmark once.
## Non-Goals
- No QID-specific runtime branch. The listed QIDs are only smoke coverage.
- No prompt/model/fine-tuning change.
- No answer-key driven remediation.
