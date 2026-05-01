# Phase 22S Raw Source Provenance

## Summary

- Sources in manifest: 7
- Downloaded successfully: 7
- Failed downloads: 0

## Provenance Table

| source_id | status | http_code | content_type | file_size_bytes | sha256 | raw_file_path |
|---|---|---:|---|---:|---|---|
| `yok_disc_2012_regulation` | `downloaded` | 200 | `text/html; charset=utf-8` | 60487 | `dce411bbf1c9e8d158b405d78a3a117159e4cbe3ccadd024f91850ccbd940d51` | `reports/benchmark/source_acquisition/phase_22S/raw/yok_disc_2012_regulation.html` |
| `yok_disc_2023_repeal` | `downloaded` | 200 | `text/html` | 16486 | `5862b03a41d5de57e34e9c293002173959ceebcb6c22b07c2497221667bbf21c` | `reports/benchmark/source_acquisition/phase_22S/raw/yok_disc_2023_repeal.html` |
| `law_2547_current` | `downloaded` | 200 | `application/pdf` | 1176626 | `a6483e549fceb2b28625c5eb1229e1c2adeb1783c42c817b00e26ad59d247ff4` | `reports/benchmark/source_acquisition/phase_22S/raw/law_2547_current.pdf` |
| `teblig_23093_current` | `downloaded` | 200 | `text/html; charset=utf-8` | 67314 | `430328ccfcde88bfa52384621f5688c04b571abed97aa18271fa13b42f3ddfc4` | `reports/benchmark/source_acquisition/phase_22S/raw/teblig_23093_current.html` |
| `law_6102_current` | `downloaded` | 200 | `application/pdf` | 3627130 | `48e9febb8d29e3df29e12d1c4607d1dd3e4fca29aa3b16c4c12b0674e90ce6cd` | `reports/benchmark/source_acquisition/phase_22S/raw/law_6102_current.pdf` |
| `ticaret_sicili_yonetmeligi` | `downloaded` | 200 | `text/html; charset=utf-8` | 67267 | `70ce4c16c7cf4b95d8eeecb8e995a47bdef6638d748e962eb9731790f53051f9` | `reports/benchmark/source_acquisition/phase_22S/raw/ticaret_sicili_yonetmeligi.html` |
| `teblig_23093_2021_amendment` | `downloaded` | 200 | `text/html` | 36529 | `6a60ce1f6217d4c686bb59f0d6525da3963e4e81959ec24c769fde68661a879c` | `reports/benchmark/source_acquisition/phase_22S/raw/teblig_23093_2021_amendment.html` |

## Provenance Records

Per-source JSON provenance records are stored under:

```text
reports/benchmark/source_acquisition/phase_22S/provenance/
```

Raw files are stored unmodified under:

```text
reports/benchmark/source_acquisition/phase_22S/raw/
```

## Scope Guard

This acquisition did not write to runtime config, Milvus live collections, shadow collections, benchmark prompts, source identity code, or answer synthesis code.
