# Phase 2 Candidate Answer Schema

Bu fazda benchmark candidate CSV'si cevap metninin yanina makinece denetlenebilir
answer contract kolonlari ekler.

## Zorunlu contract kolonlari

- `confidence_0_100`: Gateway policy tarafindan uretilen 0-100 tamsayi.
- `final_reason`: Kontrollu kisa gerekce sablonu.
- `answer_mode`: `direct_answer`, `qualified_answer`, `insufficient_grounding`, `conflict_detected`, `repealed_or_uncertain`.
- `grounding_status`: `fully_grounded`, `partially_grounded`, `not_grounded`.
- `source_family_claimed`: Model/gateway tarafindan iddia edilen kaynak ailesi.
- `source_title_claimed`: Iddia edilen kaynak basligi veya fallback kaynak kimligi.
- `source_identifier_claimed`: Iddia edilen belge/madde kimligi; bulunamazsa `unknown`.
- `article_or_section_claimed`: Iddia edilen madde/bolum; bulunamazsa `unknown`.
- `effective_state_claimed`: `active`, `amended`, `repealed`, `unknown`.
- `temporal_qualification`: Hedef tarih veya `unknown`.
- `needs_manual_review`: `True` veya `False`.

## Trace / validation kolonlari

- `contract_valid`: Zorunlu alanlar, enumlar ve confidence bandi gecerli.
- `contract_repaired`: Gateway mevcut cevabi Phase 2 contract'a tamamlamis.
- `claimed_source_parse_success`: Kaynak ailesi ve en az bir kaynak kimligi/basligi parse edilebilmis.
- `confidence_policy_ok`: Confidence, grounding bandi ile tutarli.
- `uncertainty_disclosed`: Manual review veya belirsizlik durumunda gerekcede acik sinyal var.
- `manual_review_flag`: Runtime tarafindaki manual review karari.
- `unsupported_confident_answer`: Yuksek confidence ile yetersiz grounding birlikte gorulmus.

CSV geriye donuk uyumludur: eski kosular bu kolonlari bos birakir, Phase 2 scorer
bu bosluklari ayri contract failure olarak sayar.
