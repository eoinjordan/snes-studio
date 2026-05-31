param(
  [string]$Version = "0.0.0-dev"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

python -m pip install --upgrade pip
python -m pip install -e ".[server]" pyinstaller
npm ci --prefix web
# Force base '/' so the bundled SPA works when served from the desktop app root.
$env:SNES_STUDIO_DESKTOP = "1"
npm run build --prefix web

$payload = Join-Path $root "build/windows/payload"
$dist = Join-Path $root "dist"
New-Item -ItemType Directory -Force -Path $payload | Out-Null
New-Item -ItemType Directory -Force -Path $dist | Out-Null

python -m PyInstaller --onefile --name snes-studio --distpath $payload scripts/snes_studio_cli.py
python -m PyInstaller --onefile --windowed --name "SNES Studio" --distpath $payload `
  --add-data "web/dist;web/dist" `
  --add-data "examples/pocket-bugs;examples/pocket-bugs" `
  --add-data "examples/mango-island;examples/mango-island" `
  --add-data "examples/poachermon;examples/poachermon" `
  scripts/snes_studio_desktop.py

$iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
  throw "Inno Setup compiler (iscc.exe) not found. Install Inno Setup or run in CI where it is provisioned."
}

$env:SNES_STUDIO_VERSION = $Version
& $iscc.Source "packaging/windows/snes-studio.iss"

if (-not (Test-Path "dist/SNES-Studio-Setup.exe")) {
  throw "Installer was not generated."
}

Write-Host "Built dist/SNES-Studio-Setup.exe"
