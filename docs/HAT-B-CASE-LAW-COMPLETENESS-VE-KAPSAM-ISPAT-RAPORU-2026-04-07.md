# Hat-B Case-Law Completeness Ve Kapsam Ispat Raporu 2026-04-07

## Completeness Findings

### Yargitay

- official_locator = `https://karararama.yargitay.gov.tr/`
- official_bundle_sha256 = `35b7626a7e2987a28f8bfae728e41b58b94a4618f5665cb5ea3bc11956e3666b`
- observed_signal = `recordsTotal-driven paged search client and detail-id hook`
- completeness_judgment = `PARTIAL_OR_UNPROVEN`
- decisive_reason = `official search shell acquired, but full canonical decision rowset was not materialized or frozen`

### Danistay

- official_locator = `https://karararama.danistay.gov.tr/`
- official_bundle_sha256 = `f5e2af20328a3d3cbd85d5e08fd281397bb7f1261da6bfeef45e8ce4c4235b49`
- observed_signal = `382739 explicit document count plus result API and detail-id hook`
- completeness_judgment = `PARTIAL_OR_UNPROVEN`
- decisive_reason = `official total-count evidence exists, but full canonical decision corpus was not yet parsed and frozen repo-locally`

### Anayasa Mahkemesi

- official_locator = `https://www.anayasa.gov.tr/tr/kararlar-bilgi-bankasi/ ; https://kararlarbilgibankasi.anayasa.gov.tr/ ; https://normkararlarbilgibankasi.anayasa.gov.tr/`
- official_bundle_sha256 = `6396a7b2d484180e3619c223e361c33ad6c89a9136faf7d14e9e65983dfaee03`
- observed_signals = `5533 norm decisions visible ; bireysel portal pagination to 1674 ; official stats 714774 bireysel applications and 2436 norm applications`
- completeness_judgment = `PARTIAL_OR_UNPROVEN`
- decisive_reason = `multi-portal official surface acquired, but no single unified canonical decision export or full parsed corpus has yet been materialized`

## Aggregate Result

- minimum_source_set_completeness = `not_proven`
- completeness_equivalent_to_FULL_AND_PROVEN = `false`
- decisive_missing_step = `full canonical decision-row materialization and completeness proof per source`
