#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.0.0-dev}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m pip install --upgrade pip
python3 -m pip install -e ".[server]" pyinstaller

PAYLOAD="$ROOT/build/macos/root/usr/local/bin"
DIST="$ROOT/dist"
mkdir -p "$PAYLOAD" "$DIST"

python3 -m PyInstaller --onefile --name snes-studio --distpath "$PAYLOAD" scripts/snes_studio_cli.py
chmod +x "$PAYLOAD/snes-studio"

pkgbuild \
  --root "$ROOT/build/macos/root" \
  --identifier "com.snesstudio.cli" \
  --version "$VERSION" \
  --install-location "/" \
  "$DIST/SNES-Studio-macOS.pkg"

echo "Built $DIST/SNES-Studio-macOS.pkg"
