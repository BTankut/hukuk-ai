# Phase25H-E Owner Merge Review Checklist

Generated: 2026-05-09

This checklist does not authorize merge.

## PR1 Docs-Only Checklist

- Confirm PR1 URL is `https://github.com/BTankut/hukuk-ai/pull/1`.
- Confirm PR1 base branch is `main`.
- Confirm PR1 head branch is `bt/phase25e-product-policy-docs`.
- Confirm PR1 changed files remain under `reports/benchmark/productization/`.
- Confirm PR1 changed files are only `.md` and `.csv`.
- Confirm PR1 changed file count remains 21.
- Confirm PR1 contains no runtime code, source code, service code, gateway code, package code, script change, or config change.
- Confirm PR1 remains product policy/governance documentation only.

## PR2 Docs-Only Checklist

- Confirm PR2 URL is `https://github.com/BTankut/hukuk-ai/pull/2`.
- Confirm PR2 base branch is `main`.
- Confirm PR2 head branch is `bt/phase25e-judicial-architecture-docs`.
- Confirm PR2 changed files remain under `reports/benchmark/productization/`.
- Confirm PR2 changed files are only `.md` and `.csv`.
- Confirm PR2 changed file count remains 7.
- Confirm PR2 contains no runtime code, ingestion implementation, indexing implementation, retrieval implementation, source package, or config change.
- Confirm PR2 remains judicial architecture / dry-run documentation only.

## Runtime Exclusion Checklist

- No application source file is included.
- No gateway source file is included.
- No service/router/retriever code is included.
- No Docker/systemd/deployment file is included.
- No runtime configuration file is included.
- No endpoint binding is changed.
- No live `8000` behavior is changed.

## Trace / Run / Raw Exclusion Checklist

- No `trace.jsonl` file is included.
- No benchmark run directory is included.
- No raw source package is included.
- No raw judicial data is included.
- No PDF, ZIP, log artifact, or generated trace artifact is included.
- Policy documents that discuss trace handling are not trace artifacts.

## Judicial Dry-Run Constraints Checklist

- Judicial corpus remains separate from mevzuat.
- No yargı-live retrieval is enabled.
- No mevzuat/yargı collection merge is performed.
- No production judicial index is created.
- No Milvus production mutation is performed.
- No public endpoint is exposed.
- No fine-tuning is started.
- PR2 remains architecture and dry-run plan only.

## Productization Stop-Rule Checklist

- No productization is opened.
- No internal eval is opened.
- No reviewer-only eval is opened.
- No serving candidate is opened.
- No deployment is opened.
- No model, prompt, or top-k setting is changed.
- No auto-merge is enabled.
- No merge is performed.

## Merge Approval Conditions

Before any future merge, the owner must explicitly confirm all of the following:

- PR1 and PR2 have been reviewed after ready-for-review transition.
- PR1 and PR2 still match their intended docs-only scopes.
- No runtime, live config, trace/run/raw, model/prompt/top-k, productization, eval, fine-tuning, yargı-live retrieval, or mevzuat/yargı merge scope has entered either PR.
- Any GitHub checks or required branch protections are acceptable.
- Merge is explicitly approved by the owner in a new instruction.

## Current Recommendation

PR1 and PR2 are ready for owner review.

Merge remains blocked until explicit owner merge approval is given.
