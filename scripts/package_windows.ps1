param(
  [string]$Version = "0.0.0-dev",
  [switch]$SkipInstaller
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

python -m PyInstaller --onefile --name snes-studio --distpath $payload `
  --add-data "snesstudio/assets;snesstudio/assets" `
  --add-data "snesstudio/templates;snesstudio/templates" `
  scripts/snes_studio_cli.py
python -m PyInstaller --onefile --windowed --name "SNES Studio" --distpath $payload `
  --add-data "web/dist;web/dist" `
  --add-data "snesstudio/assets;snesstudio/assets" `
  --add-data "snesstudio/templates;snesstudio/templates" `
  --add-data "examples/pocket-bugs;examples/pocket-bugs" `
  --add-data "examples/mango-island;examples/mango-island" `
  --add-data "examples/poachermon;examples/poachermon" `
  scripts/snes_studio_desktop.py

if ($SkipInstaller) {
  Write-Host "Skipping installer generation. Payload executables are in build/windows/payload."
  exit 0
}

$iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
  $fallbacks = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
  )
  $isccPath = $fallbacks | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
  if ($isccPath) {
    $iscc = @{ Source = $isccPath }
  }
}
if (-not $iscc) {
  throw "Inno Setup compiler (iscc.exe) not found. Install Inno Setup 6 and rerun, or pass -SkipInstaller for local payload testing."
}

$env:SNES_STUDIO_VERSION = $Version
& $iscc.Source "packaging/windows/snes-studio.iss"

if (-not (Test-Path "dist/SNES-Studio-Setup.exe")) {
  throw "Installer was not generated."
}

Write-Host "Built dist/SNES-Studio-Setup.exe"
