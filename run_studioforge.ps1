param(
    [int]$Port = 8501,
    [switch]$NoRestart   # Pass -NoRestart for single-run (no auto-restart loop)
)

$ErrorActionPreference = 'Stop'

# Always run from this script's folder (repo root)
Set-Location -Path $PSScriptRoot

$script = Join-Path $PSScriptRoot 'studioforge_app.py'
if (-not (Test-Path $script)) {
    Write-Error "Could not find StudioForge entrypoint: $script"
    exit 1
}

function Test-PortBusy([int]$p) {
    try {
        return (Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue) -ne $null
    } catch {
        return $false
    }
}

# Pick first free port between $Port..$Port+9
$chosen = $Port
for ($p = $Port; $p -le ($Port + 9); $p++) {
    if (-not (Test-PortBusy $p)) { $chosen = $p; break }
}
if ($chosen -ne $Port) {
    Write-Host "Port $Port is busy, using $chosen instead." -ForegroundColor Yellow
}

Write-Host "Starting StudioForge on http://localhost:$chosen" -ForegroundColor Cyan
if (-not $NoRestart) {
    Write-Host "Auto-restart enabled (pass -NoRestart to disable)." -ForegroundColor DarkGray
}

# Prefer python/py module invocation; fall back to 'streamlit' on PATH
# --server.runOnSave true  : Streamlit auto-reloads on source file changes
# --server.headless true   : suppresses the "browser already open" prompt
$commonArgs = @('run', $script, '--server.port', "$chosen", '--server.runOnSave', 'true', '--server.headless', 'true')
$dependencyOverlay = Join-Path $PSScriptRoot '.studioforge_deps'
if (Test-Path $dependencyOverlay) {
    $env:PYTHONPATH = if ($env:PYTHONPATH) { "$dependencyOverlay;$env:PYTHONPATH" } else { $dependencyOverlay }
}

function Resolve-Python {
    # Returns the python executable that has streamlit, or $null
    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (Test-Path $venvPython) {
        try {
            & $venvPython -c "import streamlit" 2>$null
            if ($LASTEXITCODE -eq 0) { return $venvPython }
        } catch { }
    }
    foreach ($candidate in @('py', 'python', 'streamlit')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        if ($candidate -eq 'streamlit') { return 'streamlit' }
        try {
            & $candidate -c "import streamlit" 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        } catch { }
    }
    return $null
}

# --- Supervised run loop ---
# Always restart unless -NoRestart is set. The only way to stop is Ctrl+C
# in this window (which kills both this script and the child Streamlit process).
$attempts = 0
$maxRestarts = 5
$restartWindow = 10  # seconds — rapid-crash detection threshold

while ($true) {
    $py = Resolve-Python
    if (-not $py) {
        Write-Error "Failed to start Streamlit. Ensure Python is installed and the 'streamlit' package is available in your active environment."
        break
    }

    $startTime = Get-Date
    Write-Host "Starting Streamlit (attempt $($attempts + 1))..." -ForegroundColor Cyan
    if ($py -eq 'streamlit') {
        & streamlit @commonArgs
    } else {
        & $py -m streamlit @commonArgs
    }
    $elapsed = ((Get-Date) - $startTime).TotalSeconds

    if ($NoRestart) {
        Write-Host "StudioForge exited (no-restart mode)." -ForegroundColor Yellow
        break
    }

    # Crashed or was killed — decide whether to retry
    if ($elapsed -lt $restartWindow) {
        $attempts++
    } else {
        $attempts = 1
    }

    if ($attempts -gt $maxRestarts) {
        Write-Host "StudioForge crashed $attempts times within ${restartWindow}s. Stopping to avoid a restart loop." -ForegroundColor Red
        Write-Host "Run with -NoRestart to start once without supervision, or check the error above." -ForegroundColor DarkGray
        break
    }

    Write-Host "StudioForge stopped after $([math]::Round($elapsed, 1))s (attempt $attempts of $maxRestarts). Restarting in 3 seconds... (Ctrl+C to stop)" -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

exit 0
