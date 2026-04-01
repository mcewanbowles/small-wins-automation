$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

function Test-PortAvailable {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

function Get-FirstAvailablePort {
    param(
        [Parameter(Mandatory = $true)]
        [int[]]$Candidates,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    foreach ($candidate in $Candidates) {
        if (Test-PortAvailable -Port $candidate) {
            return $candidate
        }
    }

    throw "No available $Label ports found in candidates: $($Candidates -join ', ')"
}

$backendPython = Join-Path $backend ".venv\Scripts\python.exe"
if (-not (Test-Path $backendPython)) {
    throw "Backend virtualenv not found. Run .\\setup_local.ps1 first."
}

$npmCmd = $null
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmCmd = "npm"
} elseif (Test-Path "C:\Program Files\nodejs\npm.cmd") {
    $npmCmd = "C:\Program Files\nodejs\npm.cmd"
} else {
    throw "npm not found. Install Node.js LTS and ensure npm is on PATH."
}

$backendPort = Get-FirstAvailablePort -Candidates @(8000, 8001, 8002, 8003) -Label "backend"
$frontendPort = Get-FirstAvailablePort -Candidates @(5173, 5174, 5175, 5176) -Label "frontend"

$backendCmd = "`"$backendPython`" -m uvicorn app.main:app --host 127.0.0.1 --port $backendPort --reload"
$frontendCmd = "`$env:VITE_API_URL='http://127.0.0.1:$backendPort'; & `"$npmCmd`" run dev -- --host 127.0.0.1 --port $frontendPort"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WorkingDirectory $backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WorkingDirectory $frontend

Write-Host "ListingLift started:" -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:$frontendPort" -ForegroundColor Green
Write-Host "Backend:  http://127.0.0.1:$backendPort" -ForegroundColor Green
