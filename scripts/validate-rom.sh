#!/usr/bin/env bash
set -euo pipefail
ROM="${1:-}"
if [ -z "$ROM" ]; then echo "Usage: scripts/validate-rom.sh <file.sfc>" >&2; exit 2; fi
if [ ! -f "$ROM" ]; then echo "ROM not found: $ROM" >&2; exit 1; fi
BYTES=$(wc -c < "$ROM")
if [ "$BYTES" -le 0 ]; then echo "ROM is empty: $ROM" >&2; exit 1; fi
if grep -q "SNESSTUDIO_PLACEHOLDER_ROM" "$ROM" 2>/dev/null; then
  echo "Valid placeholder artifact: $ROM ($BYTES bytes). This is not playable."
else
  echo "Valid non-empty ROM artifact: $ROM ($BYTES bytes)."
fi
