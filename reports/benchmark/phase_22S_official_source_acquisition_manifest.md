# Phase 22S Official Source Acquisition Manifest

## Scope

Phase 22S acquires official/public raw sources required for P0 shadow backfill readiness. This is not a runtime remediation phase.

Runtime code, source identity patches, article/span selector patches, Milvus writes, shadow collection builds, benchmark runs, productization, and fine-tuning remain prohibited.

## Required Sources

| source_id | Source | Purpose | QID |
|---|---|---|---|
| `yok_disc_2012_regulation` | 2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği | historical/repealed discipline source | `MULGA-01` |
| `yok_disc_2023_repeal` | 2023 repeal instrument for 2012 YÖK discipline regulation | repeal/effective-state source | `MULGA-01` |
| `law_2547_current` | 2547 sayılı Yükseköğretim Kanunu m.54 | current-law basis | `MULGA-01` |
| `teblig_23093_current` | 23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ | primary operational source | `TEB-06` |
| `law_6102_current` | 6102 sayılı Türk Ticaret Kanunu m.210 | supporting legal basis | `TEB-06` |
| `ticaret_sicili_yonetmeligi` | Ticaret Sicili Yönetmeliği relevant framework provisions | supporting framework source | `TEB-06` |
| `teblig_23093_2021_amendment` | 2021 amendment instrument for 23093 current text control | current text control | `TEB-06` |

## Article Scopes

`MULGA-01` requires:

- 2012 YÖK discipline regulation: relevant discipline articles
- 2023 repeal instrument: repeal clause, effective date, execution clause
- 2547: m.54 current-law basis

`TEB-06` requires:

- 23093 tebliğ: m.4-m.8, especially m.6 and m.8
- 6102 TTK: m.210
- Ticaret Sicili Yönetmeliği: company formation / registry framework provisions
- 2021 amendment instrument: current text control for 23093

## Gate Rule

Raw acquisition uses parser-accessible official endpoints when a public detail page is only a shell page. In this manifest that means Resmî Gazete item HTML for the repealed 2012 regulation, Mevzuat DOC files for consolidated laws, and Mevzuat iframe body HTML for consolidated tebliğ/yönetmelik body text.

For Phase 22F readiness, each required source must have:

- official URL
- raw downloaded file
- raw file path
- SHA-256 hash
- parser-readiness decision
- article-boundary detectability decision

If acquisition succeeds but parsing or article boundaries are not ready, Phase 22F remains closed and parser/materialization preparation must open first.
