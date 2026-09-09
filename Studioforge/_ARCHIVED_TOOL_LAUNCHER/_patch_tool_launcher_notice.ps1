param()
$ErrorActionPreference = 'Stop'

$File = 'D:\Seagate\small-wins-automation\Studioforge\WINDSURF_TOOL_LAUNCHER.py'
if (-not (Test-Path -LiteralPath $File)) { throw "Not found: $File" }

# Read the file
$content = Get-Content -LiteralPath $File -Raw -Encoding UTF8
$orig = $content
$changes = @()

# 1) Insert PYTHON_SOURCE + _maybe_warn_python_fallback after PYTHON line
if ($content -notmatch "PYTHON_SOURCE\s*=") {
  $patternPy = '(?m)^PYTHON\s*=\s*str\(_venv_py\).*?$'
  $replacementPy = @'
PYTHON = str(_venv_py) if (_venv_py.exists() and _probe_python(_venv_py)) else (sys.executable or "python")
PYTHON_SOURCE = "venv" if (_venv_py.exists() and _probe_python(_venv_py)) else "system"
_PY_WARNED = False

def _maybe_warn_python_fallback():
    global _PY_WARNED
    if PYTHON_SOURCE != "venv" and not _PY_WARNED:
        try:
            messagebox.showinfo("Interpreter fallback", "Using system Python (venv not available).")
        except Exception:
            pass
        _PY_WARNED = True
'@
  $new1 = [Regex]::Replace($content, $patternPy, $replacementPy, 1)
  if ($new1 -ne $content) { $content = $new1; $changes += 'python_source_notice' }
}

# 2) Update _touch_used to log python source
if ($content -notmatch '"_python_source"\] = PYTHON_SOURCE') {
  $patternTouch = '(?m)^\s{4}_write_log\(data\)'
  $replacementTouch = @'
    try:
        data["_python_source"] = PYTHON_SOURCE
    except Exception:
        pass
    _write_log(data)
'@
  $new2 = [Regex]::Replace($content, $patternTouch, $replacementTouch, 1)
  if ($new2 -ne $content) { $content = $new2; $changes += 'log_source' }
}

# 3) Prepend _maybe_warn_python_fallback() before each subprocess.Popen in launcher helpers
$popens = @(
  'subprocess\.Popen\(args, cwd=str\(cwd\), creationflags=creationflags, env=env\)',
  'subprocess\.Popen\(cmd, cwd=str\(cwd\), creationflags=creationflags, env=env\)'
)
foreach ($pat in $popens) {
  $regex = [Regex]::new("(?m)^\s{8}$pat")
  if ($regex.IsMatch($content) -and $content -notmatch '_maybe_warn_python_fallback\(\)\s*\r?\n\s{8}' + $pat) {
    $content = $regex.Replace($content, "        _maybe_warn_python_fallback()`r`n        " + $regex.Match($content).Value.Trim(), 1)
    $changes += 'warn_before_popen'
  }
}

if ($content -ne $orig) {
  Set-Content -LiteralPath $File -Encoding UTF8 -NoNewline -Value $content
  Write-Output ("Patched: " + ($changes -join ', '))
} else {
  Write-Output 'No changes made (already patched or patterns not found)'
}
