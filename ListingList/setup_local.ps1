$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

$npmCmd = $null
$nodeDir = $null
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmCmd = "npm"
} elseif (Test-Path "C:\Program Files\nodejs\npm.cmd") {
    $npmCmd = "C:\Program Files\nodejs\npm.cmd"
    $nodeDir = "C:\Program Files\nodejs"
} else {
    throw "npm not found. Install Node.js LTS and ensure npm is on PATH."
}

$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} else {
    throw "Python not found. Install Python 3.10+ and ensure it is on PATH."
}

Write-Host "Setting up ListingLift backend..." -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $backend ".venv"))) {
    & $pythonCmd -m venv (Join-Path $backend ".venv")
}

& (Join-Path $backend ".venv\Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $backend ".venv\Scripts\python.exe") -m pip install -r (Join-Path $backend "requirements.txt")

if (-not (Test-Path (Join-Path $backend ".env"))) {
    Copy-Item (Join-Path $backend ".env.example") (Join-Path $backend ".env")
    Write-Host "Created backend/.env from .env.example" -ForegroundColor Yellow
}

Write-Host "Setting up ListingLift frontend..." -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $frontend ".env"))) {
    Copy-Item (Join-Path $frontend ".env.example") (Join-Path $frontend ".env")
}

Push-Location $frontend
if ($nodeDir) {
    $env:Path = "$nodeDir;$env:Path"
}
& $npmCmd install
Pop-Location

Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next: run .\\run_local.ps1" -ForegroundColor Green
