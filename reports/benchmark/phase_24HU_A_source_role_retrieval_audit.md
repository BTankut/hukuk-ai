# Phase 24HU-A Source-Role Retrieval Audit

## Scope

This audit uses the latest Phase 24HT focused non-live candidate trace:

- run: `reports/benchmark/runs/phase_24HT_focused_non_live_candidate_smoke`
- QID: `KANUN-08`
- question: `İnternetten kişiye özel ölçüye göre üretilen bir mobilya satılmış. Tüketici 14 gün içinde cayma hakkını kullanmak istiyor. Hangi normlar birlikte okunmalı ve 'kişiye özel üretim' istisnası nasıl test edilmeli?`

Live `8000` was not modified.

## Findings

- The benchmark CSV has `secondary_types=YONETMELIK`, but `scripts/benchmark/run_hukuk_ai_100.py` does not send that field to `/v1/chat/completions`; runtime cannot depend on the answer key.
- Runtime still detects a secondary-family signal without the answer key: `metadata_lookup_query_signals.parsed_family_candidates=["yonetmelik"]`.
- `metadata_first_selector` finds three `YONETMELIK/UY` title candidates, but all are suppressed as primary-document candidates by the Phase 24X domain gate.
- No supporting-family retrieval lane is run after the metadata candidates are suppressed. The normal source-family bucket adds only the primary `KANUN` family, so `pre_filter_family_set=["kanun"]`.
- `post_rerank_chunks` contains only `KANUN` spans: `TKHK m.18`, `TKHK m.43`, and TBK sale/installment spans. No `YONETMELIK` candidate reaches the final evidence bundle.
- The article selector improves primary source identity to `TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18`, but the exception/procedure slot selector then searches the remaining `KANUN`-only bundle.
- Because no role-tagged supporting regulation evidence exists, `exception_or_limitation`, `exception_rule`, and `exception_conditions` are filled from unrelated TBK/private-law spans (`TBK m.268`, with `scenario_applicability` from `TBK m.255`).

## Required Answers

`secondary_types=YONETMELIK nerede üretiliyor?`

- In the benchmark data it exists as row metadata, but it is not passed to runtime.
- In runtime, an equivalent source-family signal is produced by `_parse_metadata_lookup_query_signals(...)` as `parsed_family_candidates=["yonetmelik"]`.

`pre_filter_family_set neden yalnız ["kanun"] kalıyor?`

- `_apply_pre_generation_family_pool(...)` computes `pre_filter_family_set` from the chunk pool that exists before the family gate.
- At that point, no secondary/supporting `YONETMELIK` retrieval lane has added regulation chunks; suppressed metadata candidates were not retrieved as supporting evidence.

`YONETMELIK candidates retrieval top-k'de var mı?`

- They are present in metadata lookup candidates, not in dense/source-family retrieval top-k or final selected evidence.

`Varsa neden selector/evidence bundle'a girmiyor?`

- They are treated only as primary source candidates and are blocked by `phase24x_all_metadata_candidates_blocked`.
- There is no fallback path that converts blocked-but-relevant `YONETMELIK` metadata candidates into role-tagged supporting candidates.

`Yoksa family-filter mı, retrieval recall mı sorun?`

- The immediate blocker is retrieval orchestration: secondary-family recall is never run as a supporting lane.
- The family pool then only sees `KANUN`; the issue is not broad dense recall alone.

`Exception slot neden TBK/private-law span ile doluyor?`

- Slot selection is evidence-local and role-unaware. With no supporting regulation evidence, `_select_chunk_for_slot(...)` picks semantically similar exception-looking TBK spans from the remaining `KANUN` bundle.

## Conclusion

Phase 24HU should add a feature-flagged, query-signal-driven secondary-family supporting recall lane and a matching exception-slot guard. The primary `KANUN` source identity must remain locked; secondary candidates must be tagged as `supporting_rule`, `exception_rule`, or `implementation_detail`.
