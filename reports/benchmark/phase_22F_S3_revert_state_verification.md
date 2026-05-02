# Phase 22F-S3 Revert State Verification
Date: 2026-05-02
## Scope
Audit/design-only verification after Phase 22F-S2 failed and was reverted. No runtime code change, benchmark run, retrieval change, prompt/model change, or live cutover was performed in this phase.
## Git State
- Current HEAD before this report commit: `271d032`
- Relevant recent commits:
  - `271d032 Report Phase 22F-S2 scoped temporal alignment decision`
  - `0ac41ed Revert "Scope temporal claim alignment to relation-backed historical sources"`
  - `ec76b4c Run Phase 22F-S2 P0 relation guard smoke`
  - `8e73f53 Run Phase 22F-S2 overapplication smoke`
  - `cd4f7db Scope temporal claim alignment to relation-backed historical sources`
  - `1154fca Create Phase 22F-S2 temporal overapplication fixture`
## Revert Verification
- S2 implementation commit `cd4f7db` exists in history.
- Revert commit `0ac41ed` exists after the implementation commit.
- Current source tree has no active S2-only trace fields under `api-gateway/src` or `api-gateway/tests`.
- Source grep result for S2-only fields: `clean`
## Runtime Verification
### 8018 Shadow
```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_shadow","api_version":"2026-05-01-phase22f","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```
Listener:
```text
COMMAND     PID        USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
python3.1 93102 btmacstudio    9u  IPv4 0x7d1379c2c5c5a153      0t0  TCP 127.0.0.1:8018 (LISTEN)
```
tmux session:
```text
hukuk-ai-8018-s2-reverted: 1 windows (created Sat May  2 08:28:30 2026)
```
### 8000 Live
```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"current_serving_lane","api_version":"2026-03-24-rc-h","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```
## Gate State
- `8018` lane remains `phase22f_shadow`.
- `8018` collection remains `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`.
- Live `8000` remains `current_serving_lane`.
- Productization remains closed.
- Fine-tuning remains closed.
## Decision
Revert state is verified. Proceed to S3 two-permission policy audit/design without runtime implementation.
