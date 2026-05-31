#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.0.0-dev}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m pip install --upgrade pip
python3 -m pip install -e ".[server]" pyinstaller
npm ci --prefix web
# Force base '/' so the bundled SPA works when served from the desktop app root.
export SNES_STUDIO_DESKTOP=1
npm run build --prefix web

BIN_PAYLOAD="$ROOT/build/macos/root/usr/local/bin"
APP_PAYLOAD="$ROOT/build/macos/root/Applications"
DIST="$ROOT/dist"
mkdir -p "$BIN_PAYLOAD" "$APP_PAYLOAD" "$DIST"

python3 -m PyInstaller --onefile --name snes-studio --distpath "$BIN_PAYLOAD" scripts/snes_studio_cli.py
chmod +x "$BIN_PAYLOAD/snes-studio"

python3 -m PyInstaller --windowed --name "SNES Studio" --distpath "$APP_PAYLOAD" \
  --add-data "web/dist:web/dist" \
  --add-data "examples/pocket-bugs:examples/pocket-bugs" \
  --add-data "examples/mango-island:examples/mango-island" \
  --add-data "examples/poachermon:examples/poachermon" \
  scripts/snes_studio_desktop.py

pkgbuild \
  --root "$ROOT/build/macos/root" \
  --identifier "com.snesstudio.app" \
  --version "$VERSION" \
  --install-location "/" \
  "$DIST/SNES-Studio-macOS.pkg"

echo "Built $DIST/SNES-Studio-macOS.pkg"
