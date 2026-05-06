# Trace Exposure Policy

## Scope
This policy controls benchmark trace, diagnostic trace, and runtime-debug artifact exposure.

## Commit Rules
- Do not commit full `trace.jsonl` or equivalent large per-request trace logs.
- Commit only summaries, small CSV/MD diagnostics, and redacted review packets.
- Committed trace-derived artifacts should stay below 25 MB unless explicitly approved.

## Storage Rules
- Full traces must remain in controlled local storage or a designated secure artifact store.
- External sharing requires redaction of PII, secrets, private hostnames when sensitive, and reviewer-irrelevant prompt text.
- Retention must be defined before productization.

## Review Rules
- Legal reviewers receive only the rows and evidence needed for legal/source/scorer review.
- Product reports should cite summary files instead of embedding raw trace payloads.

## Current State
- This productization pass does not stage large trace files.
- Productization remains blocked until trace retention, redaction, and exposure controls are operationally adopted.

