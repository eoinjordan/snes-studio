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

ICON_ARGS=()
ICON_PNG="$ROOT/web/public/branding/snes-studio-icon-1024.png"
ICON_ICNS="$ROOT/build/macos/snes-studio.icns"
if command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1 && [[ -f "$ICON_PNG" ]]; then
  ICONSET="$ROOT/build/macos/snes-studio.iconset"
  rm -rf "$ICONSET"
  mkdir -p "$ICONSET"
  for size in 16 32 64 128 256 512; do
    sips -z "$size" "$size" "$ICON_PNG" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  done
  sips -z 32 32 "$ICON_PNG" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
  sips -z 64 64 "$ICON_PNG" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
  sips -z 256 256 "$ICON_PNG" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
  sips -z 512 512 "$ICON_PNG" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
  sips -z 1024 1024 "$ICON_PNG" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "$ICONSET" -o "$ICON_ICNS"
  ICON_ARGS=(--icon "$ICON_ICNS")
fi

python3 -m PyInstaller --onefile --name snes-studio --distpath "$BIN_PAYLOAD" \
  --add-data "snesstudio/assets:snesstudio/assets" \
  --add-data "snesstudio/templates:snesstudio/templates" \
  scripts/snes_studio_cli.py
chmod +x "$BIN_PAYLOAD/snes-studio"

python3 -m PyInstaller --windowed --name "SNES Studio" --distpath "$APP_PAYLOAD" \
  "${ICON_ARGS[@]}" \
  --add-data "web/dist:web/dist" \
  --add-data "snesstudio/assets:snesstudio/assets" \
  --add-data "snesstudio/templates:snesstudio/templates" \
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
