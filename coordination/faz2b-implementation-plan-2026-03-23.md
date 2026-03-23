# FAZ 2B Implementation Plan

**Date:** 2026-03-23  
**Reference:** `docs/FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-RAPORU-2026-03-23.md`  
**Intent:** turn the FAZ 2A pass decision into a repo-native cutover-readiness closure order

## Executive Position

FAZ 2B is not a new retrieval wave and not a production cutover.

Primary question:

> Can the re-qualified promoted lane close the remaining release controls strongly enough to reopen a real cutover decision?

This implementation plan keeps the work ordered as:

1. close the highest-risk request-surface controls first,
2. convert partial controls into tested repo artefacts,
3. keep rollout/rollback proof current on the re-qualified lane,
4. only then reopen cutover-readiness steering.

## Current Repo Reality At Start

- FAZ 2A closed as `Re-Qualify Pass -> Cutover Readiness Closure`
- the preserved baseline and promoted candidate both clear the matched family reruns
- the main remaining blocker class is now release-control closure, not retrieval/source precision
- the open must-close controls inherited from FAZ 1.5 are:
  - auth
  - audit logging
  - PII masking proof
  - session persistence
  - token accounting
  - observability / alerting
  - keepalive / supervision proof
  - backup / restore proof

## Work Packages

### WP-1 — API Surface Hardening

Goal:
- close the most exposed request-surface gaps on the main gateway

Repo actions:
- add opt-in request auth
- add append-only structured audit logging
- replace word-count `usage` with runtime-backed accounting where available
- cover these controls with router/main tests

Exit:
- the main API no longer runs as an unprotected anonymous surface by default when auth is enabled
- audit proof exists as a concrete repo-native artifact path
- `usage` no longer depends only on split-by-space counting

### WP-2 — PII / Guardrails Release Proof

Goal:
- turn the existing masking layer into a release-grade evidence row

Repo actions:
- freeze a cited masking smoke set
- capture exact release-mode env/config
- record pass/fail acceptance note

Exit:
- PII masking moves from `Partial` to `Closed` or is explicitly reclassified with evidence

### WP-3 — Session Persistence

Goal:
- remove in-memory-only session handling from the cutover path

Repo actions:
- add process-shared session store abstraction
- support Redis-backed persistence with in-memory fallback
- prove restart persistence with a repo-native smoke

Exit:
- session continuity survives process restart on the release lane

### WP-4 — Observability / Alerting / Supervision

Goal:
- make lane health and operator response observable rather than log-tail only

Repo actions:
- publish metrics endpoint / counters for request, blocked, refusal, error, and latency classes
- add a minimal alerting or operator-check contract
- refresh keepalive / process recovery evidence on the re-qualified lane

Exit:
- the release lane has a concrete operator-facing health surface and failure proof

### WP-5 — Backup / Restore + Cutover Closure

Goal:
- close the last operational proof gap before the next steering package

Repo actions:
- publish backup / restore runbook for lane config + vector store dependencies
- run at least one restore drill or bounded restore proof
- refresh cutover + rollback rehearsal on the FAZ 2A-passing lane if needed

Exit:
- the next steering package can honestly choose between `GO`, `NARROW GO`, or another no-go

## First Milestone

The first FAZ 2B milestone is:

- auth enforcement
- audit logging
- runtime-backed usage accounting

This milestone is intentionally first because it hardens the public request surface without changing model behavior or reopening retrieval drift.

## Gate Discipline

FAZ 2B will not reopen a cutover claim unless:

- the re-qualified family reports remain the source-of-record
- must-close controls are either closed with evidence or explicitly reclassified with written risk acceptance
- the next decision package can speak separately about:
  - internal cutover readiness
  - external pilot readiness
  - deferred technical debt

Until then, the valid state is active FAZ 2B execution, not cutover approval.
