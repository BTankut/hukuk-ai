# FAZ 2C Implementation Plan

**Date:** 2026-03-23  
**Reference:** `docs/FAZ2B-CUTOVER-READINESS-CLOSURE-RAPORU-2026-03-23.md`  
**Intent:** turn the `NARROW GO` steering decision into a repo-native controlled cutover execution package

## Executive Position

FAZ 2C is not another readiness or retrieval phase.

Primary question:

> Can the re-qualified promoted lane be cut over in a controlled way, with explicit rollback and operator checks, without reopening the decision package itself?

This phase keeps the work ordered as:

1. package the actual cutover/rollback commands,
2. freeze narrow-pilot acceptance and rollback triggers,
3. only then execute a real cutover when operators choose the window.

## Current Repo Reality At Start

- FAZ 2A is closed as `Re-Qualify Pass -> Cutover Readiness Closure`
- FAZ 2B is closed as `NARROW GO - controlled internal cutover / dar kapsam pilot`
- preserved baseline rollback still exists on `dgxnode2`
- promoted candidate lane remains `dgx1` merged
- auth / audit / PII / session / observability / supervision / bounded restore controls are now closed at repo-native proof level

## Work Packages

### WP-1 — Controlled Cutover Command Surface

Goal:
- package the exact cutover and rollback actions into repo-native scripts

Repo actions:
- add cutover script for flipping `8000` from baseline to candidate alias
- add rollback script for restoring preserved baseline
- embed preflight, smoke, and bounded backup steps

Exit:
- one command can perform a controlled cutover
- one command can restore preserved baseline

### WP-2 — Narrow Pilot Contract

Goal:
- define what is and is not approved under `NARROW GO`

Repo actions:
- publish runbook for cutover, smoke, and rollback
- freeze rollback triggers and operator checks

Exit:
- cutover claim is bounded to controlled internal / dar pilot scope

### WP-3 — Execution Capture

Goal:
- ensure the real cutover window can emit an execution summary rather than an ad-hoc terminal story

Repo actions:
- write cutover summary artifact
- write rollback summary artifact

Exit:
- the next actual cutover run can produce evidence directly into `runtime_logs/`

## First Milestone

The first FAZ 2C milestone is:

- controlled cutover script
- controlled rollback script
- runbook and package note

This milestone is intentionally first because it creates the exact operator surface needed for the next real execution window without forcing a live switchover during package construction.
