# Hat-B Official Case-Law Acquisition Manifest 2026-04-06

## Acquisition Manifest

| source_name | official_source_locator | acquisition_date | raw_source_file_path | checksum_sha256 | source_provenance_verified | full_source_acquired | source_boundary_notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Yargitay | `https://karararama.yargitay.gov.tr/` | `2026-04-07` | `data/case_law/full_acquisition/yargitay/official_source_bundle.html` | `35b7626a7e2987a28f8bfae728e41b58b94a4618f5665cb5ea3bc11956e3666b` | `true` | `true` | official karar arama portali snapshot olarak acquire edildi; phase boundary runtime integration degil source acquisition/provenance seviyesidir |
| Danistay | `https://karararama.danistay.gov.tr/` | `2026-04-07` | `data/case_law/full_acquisition/danistay/official_source_bundle.html` | `f5e2af20328a3d3cbd85d5e08fd281397bb7f1261da6bfeef45e8ce4c4235b49` | `true` | `true` | official karar arama portali explicit dokuman sayisi ile birlikte acquire edildi; phase boundary parse/runtime degil official source ownership seviyesidir |
| Anayasa Mahkemesi | `https://www.anayasa.gov.tr/tr/kararlar-bilgi-bankasi/ ; https://kararlarbilgibankasi.anayasa.gov.tr/ ; https://normkararlarbilgibankasi.anayasa.gov.tr/` | `2026-04-07` | `data/case_law/full_acquisition/anayasa_mahkemesi/official_source_bundle.html` | `6396a7b2d484180e3619c223e361c33ad6c89a9136faf7d14e9e65983dfaee03` | `true` | `true` | official source boundary multi-portal oldugu icin ana karar bankasi, bireysel basvuru, norm denetimi ve resmi istatistik yuzeyleri tek acquisition bundle icinde toplandi |

## Manifest Result

- acquisition_manifest_status = `closed`
- external_ad_hoc_content_used = `false`
- YIM_used_as_authoritative_source = `false`
