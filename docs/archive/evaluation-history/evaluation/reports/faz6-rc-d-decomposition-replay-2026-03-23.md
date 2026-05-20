# FAZ 6 RC-D Decomposition Replay

- tracked_count: `108`
- parity_mismatch_count: `54`
- trace_complete_count: `108`

## Reason Histogram

- `assembly_primary_miss`: `28`
- `canonical_normalization_mismatch`: `2`
- `citation_omission_with_correct_primary_present`: `45`
- `evaluator_alignment_mismatch`: `27`
- `guardrail_mode_drop`: `3`
- `retrieval_source_absent`: `3`

## Stage-First-Loss

- `assembly`: `28`
- `evaluator`: `26`
- `model`: `2`
- `post_generation`: `49`
- `retrieval`: `3`

## Family Breakdown

| family | count |
| --- | --- |
| faz1-50 | 15 |
| v2-95 | 33 |
| v3-170 | 60 |

## Rows

| family | question_id | primary_reason | secondary_reason | first_loss_stage | parity_match |
| --- | --- | --- | --- | --- | --- |
| faz1-50 | TBK-001 | evaluator_alignment_mismatch | - | evaluator | true |
| faz1-50 | TBK-003 | assembly_primary_miss | guardrail_mode_drop | assembly | true |
| faz1-50 | TBK-004 | evaluator_alignment_mismatch | - | evaluator | true |
| faz1-50 | TBK-006 | assembly_primary_miss | - | assembly | true |
| faz1-50 | TBK-007 | assembly_primary_miss | - | assembly | true |
| faz1-50 | TBK-008 | citation_omission_with_correct_primary_present | - | post_generation | false |
| faz1-50 | TBK-009 | citation_omission_with_correct_primary_present | - | post_generation | true |
| faz1-50 | TBK-011 | assembly_primary_miss | guardrail_mode_drop | assembly | true |
| faz1-50 | TBK-016 | assembly_primary_miss | - | assembly | true |
| faz1-50 | TBK-020 | citation_omission_with_correct_primary_present | - | post_generation | true |
| faz1-50 | TBK-033 | assembly_primary_miss | - | assembly | false |
| faz1-50 | TBK-035 | citation_omission_with_correct_primary_present | - | post_generation | true |
| faz1-50 | TBK-039 | evaluator_alignment_mismatch | - | evaluator | false |
| faz1-50 | TBK-042 | assembly_primary_miss | - | assembly | true |
| faz1-50 | TBK-043 | evaluator_alignment_mismatch | - | evaluator | false |
| v2-95 | HAL-003 | evaluator_alignment_mismatch | - | evaluator | false |
| v2-95 | HAL-004 | evaluator_alignment_mismatch | - | evaluator | false |
| v2-95 | HAL-005 | evaluator_alignment_mismatch | - | evaluator | false |
| v2-95 | HAL-006 | evaluator_alignment_mismatch | - | evaluator | false |
| v2-95 | HAL-007 | evaluator_alignment_mismatch | - | evaluator | false |
| v2-95 | HAL-009 | assembly_primary_miss | - | assembly | true |
| v2-95 | TBK-051 | retrieval_source_absent | - | retrieval | true |
| v2-95 | TBK-052 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v2-95 | TBK-054 | assembly_primary_miss | - | assembly | true |
| v2-95 | TBK-055 | assembly_primary_miss | - | assembly | true |
| v2-95 | TBK-057 | retrieval_source_absent | - | retrieval | true |
| v2-95 | TBK-059 | assembly_primary_miss | - | assembly | false |
| v2-95 | TBK-060 | evaluator_alignment_mismatch | - | evaluator | false |
| v2-95 | TBK-061 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v2-95 | TBK-062 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v2-95 | TBK-063 | assembly_primary_miss | - | assembly | true |
| v2-95 | TBK-064 | assembly_primary_miss | - | assembly | true |
| v2-95 | TBK-065 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v2-95 | TBK-066 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v2-95 | TBK-068 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v2-95 | TBK-072 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v2-95 | TBK-074 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v2-95 | TBK-079 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v2-95 | TBK-082 | assembly_primary_miss | - | assembly | false |
| v2-95 | TBK-083 | assembly_primary_miss | - | assembly | true |
| v2-95 | TBK-084 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v2-95 | TBK-113 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v2-95 | TBK-114 | evaluator_alignment_mismatch | - | evaluator | false |
| v2-95 | TMK-CL-003 | assembly_primary_miss | - | assembly | true |
| v2-95 | TMK-CL-004 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v2-95 | TMK-CL-006 | guardrail_mode_drop | - | post_generation | true |
| v2-95 | TMK-CL-007 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v2-95 | TMK-CL-009 | assembly_primary_miss | - | assembly | true |
| v3-170 | HAL-003 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | HAL-004 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | HAL-005 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | HAL-006 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | HAL-007 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | HAL-008 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | HAL-009 | assembly_primary_miss | - | assembly | true |
| v3-170 | HAL-011 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | HAL-012 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | OOS-011 | evaluator_alignment_mismatch | - | post_generation | true |
| v3-170 | TBK-051 | assembly_primary_miss | - | assembly | true |
| v3-170 | TBK-052 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-054 | assembly_primary_miss | - | assembly | true |
| v3-170 | TBK-055 | assembly_primary_miss | - | assembly | true |
| v3-170 | TBK-056 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | TBK-057 | retrieval_source_absent | - | retrieval | true |
| v3-170 | TBK-059 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-060 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | TBK-061 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TBK-062 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TBK-063 | assembly_primary_miss | - | assembly | true |
| v3-170 | TBK-064 | assembly_primary_miss | - | assembly | true |
| v3-170 | TBK-065 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-066 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-068 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-072 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TBK-074 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-079 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TBK-082 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TBK-083 | assembly_primary_miss | - | assembly | true |
| v3-170 | TBK-084 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-116 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TBK-117 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | TBK-118 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TBK-119 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-120 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-121 | assembly_primary_miss | - | assembly | true |
| v3-170 | TBK-122 | canonical_normalization_mismatch | - | model | false |
| v3-170 | TBK-123 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | TBK-124 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-125 | guardrail_mode_drop | - | post_generation | false |
| v3-170 | TBK-126 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-128 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-129 | canonical_normalization_mismatch | - | model | false |
| v3-170 | TBK-130 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TBK-135 | evaluator_alignment_mismatch | - | evaluator | true |
| v3-170 | TBK-154 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | TBK-165 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | TBK-166 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TMK-CL-003 | assembly_primary_miss | - | assembly | true |
| v3-170 | TMK-CL-004 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TMK-CL-006 | guardrail_mode_drop | - | post_generation | true |
| v3-170 | TMK-CL-007 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TMK-CL-014 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TMK-CL-015 | assembly_primary_miss | - | assembly | false |
| v3-170 | TMK-CL-017 | assembly_primary_miss | - | assembly | true |
| v3-170 | TMK-CL-019 | citation_omission_with_correct_primary_present | - | post_generation | true |
| v3-170 | TMK-CL-020 | citation_omission_with_correct_primary_present | - | post_generation | false |
| v3-170 | TMK-CL-028 | evaluator_alignment_mismatch | - | evaluator | false |
| v3-170 | TMK-CL-029 | citation_omission_with_correct_primary_present | - | post_generation | true |
