# Legal Review Returns

This folder is the standard drop location for filled Phase 22M legal-review return CSV files.

## Expected Files

Place exactly these files here when reviewers return them:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

## Rules

Returned CSV files must not contain private benchmark answer keys.

Returned CSV files must not contain runtime configuration, prompt configuration, Milvus collection configuration, or QID-specific runtime rules.

Official source raw files must not be stored in this folder. This folder is only for CSV decisions and source-acquisition checklist returns.

Raw source bundles must be stored in a separate provenance/source-acquisition location with hashes and acquisition notes.

After all required files are present, run:

```bash
python scripts/benchmark/check_phase22m_review_returns.py
```

If the guard passes, Phase 22M-R2 intake may proceed.

If any required file is missing, Phase 22F cannot open.
