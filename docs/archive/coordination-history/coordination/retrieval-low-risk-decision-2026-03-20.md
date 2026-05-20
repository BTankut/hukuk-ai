# Retrieval Low-Risk Decision

Date: 2026-03-20
Scope: Faz 2 P0 retrieval genişleme kararı
Decision: `adopt-low-risk`, broad retrieval rewrite `defer`

## Sonuç

Retrieval tarafında bu dalga için geniş kapsamlı yeniden tasarım gerekmiyor. Düşük riskli iki düzeltme uygulanıp baseline'a alındı:

1. Varsayılan retrieval `top_k` değeri `10 -> 20`
2. Kullanıcı sorgusunda açık madde referansı geçtiğinde ilgili madde chunk'ları exact-include ile semantik hit'lerin önüne ekleniyor

## Neden

- Önceki Faz C0 teşhisi, yaygın sistemik retrieval çöküşünden çok sınırlı sayıda recall miss gösteriyordu.
- Repo içi sonraki analizler, kalan zor vakaların önemli bölümünün model kullanımı / grounding kaynaklı olduğunu gösteriyordu.
- Canlı explicit-reference smoke, exact-include davranışının doğru çalıştığını doğruladı.

## Doğrulama

### Test

- `api-gateway/.venv/bin/pytest -q api-gateway/tests/test_chat_router.py`
- `api-gateway/.venv/bin/pytest -q api-gateway/tests/test_rag_retriever_prompt.py`

### Live smoke

Soru:
`TBK m.237 ile TMK m.706 arasındaki ilişki nedir?`

Gözlenenler:

- Gateway default retrieval: `hits=20`
- Log: `Retrieval exact-include: refs=[('TBK', '237'), ('TMK', '706')]`
- Yanıt sitasyonları: `TBK m.237`, `TMK m.706`

Bu sonuç, explicit article force-include mekanizmasının canlı hatta çalıştığını gösteriyor.

## Bilinçli Olarak Ertelenenler

- Adjacent article expansion
- Hybrid / lexical geniş retrieval
- Cross-law özel heuristikler
- Büyük retrieval prompt rewrite

Bunlar, ancak yeniden üretilebilir hard-slice kanıtı gelirse tekrar açılacak.

## Açık Not

DGX node2 `llama.cpp` runtime üzerinde `self check input` bazen boş completion döndürüp masum hukuki sorularda false refusal üretiyor. Bu issue retrieval değil, guardrails runtime uyumu problemidir ve ayrı milestone olarak ele alınacaktır.
