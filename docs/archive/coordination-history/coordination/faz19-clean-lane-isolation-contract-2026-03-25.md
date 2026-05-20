# FAZ19 Clean Lane Isolation Contract

Tarih: 2026-03-25

Capture lane ayrımı:
- `capture_a`
  - `RC-G gateway/tunnel = 8149 / 30149`
  - `RC-J gateway/tunnel = 8148 / 30148`
- `capture_b`
  - `RC-G gateway/tunnel = 8159 / 30159`
  - `RC-J gateway/tunnel = 8158 / 30158`

Namespace ayrımı:
- `SESSION_STORE_NAMESPACE = faz19-<capture>-<family>-<candidate>`
- raw eval artefact root:
  - `evaluation/reports/faz19/capture_a/`
  - `evaluation/reports/faz19/capture_b/`
- pair report artefact root:
  - `evaluation/reports/faz19-control-authority-capture_a-*.json`
  - `evaluation/reports/faz19-control-authority-capture_b-*.json`

Yorum:
- `capture_b`, `capture_a` rerun’ı değildir
- aynı port, aynı artifact namespace ve aynı session namespace ile tekrar koşu açılmayacak
