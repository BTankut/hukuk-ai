#!/usr/bin/env bash
set -euo pipefail

dry_run=false
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run=true
fi

steps=(
  "1. RC-G referans lane ayaga kaldirilir"
  "2. RC-R cutover candidate lane ayaga kaldirilir"
  "3. iki lane icin health + cited smoke dogrulanir"
  "4. alias RC-G uzerinden RC-R uzerine cevrilir"
  "5. alias switch sonrasi health + cited smoke tekrar calistirilir"
  "6. RC-R uzerindeyken restart senaryosu calistirilir"
  "7. restart sonrasi health + cited smoke tekrar calistirilir"
  "8. RC-R uzerindeyken restore senaryosu calistirilir"
  "9. restore sonrasi health + cited smoke tekrar calistirilir"
  "10. alias onceki known-good lane'e dondurulur"
  "11. rollback sonrasi health + cited smoke tekrar calistirilir"
)

for step in "${steps[@]}"; do
  echo "$step"
done

if [[ "$dry_run" == true ]]; then
  echo "dry_run=true"
else
  echo "rehearsal_contract_materialized=true"
fi
