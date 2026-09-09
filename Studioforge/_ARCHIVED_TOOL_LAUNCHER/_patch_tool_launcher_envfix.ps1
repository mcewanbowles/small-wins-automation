param()
$ErrorActionPreference = 'Stop'

$File = 'D:\Seagate\small-wins-automation\Studioforge\WINDSURF_TOOL_LAUNCHER.py'
if (-not (Test-Path -LiteralPath $File)) {
  Write-Error "Not found: $File"
}

# Read file
$content = Get-Content -LiteralPath $File -Raw -Encoding UTF8
$original = $content
$changes = @()

# 1) Add venv executability probe and fallback
if ($content -notmatch 'def\s+_probe_python\(') {
  $pattern1 = '(?ms)_venv_py\s*=\s*STUDIOFORGE_DIR\s*/\s*"backend"\s*/\s*"\.venv311_x64"\s*/\s*"Scripts"\s*/\s*\("python\.exe"\s*if\s*os\.name\s*==\s*"nt"\s*else\s*"python"\)\r?\nPYTHON\s*=\s*str\(_venv_py\)\s*if\s*_venv_py\.exists\(\)\s*else\s*\(sys\.executable\s*or\s*"python"\)'
  $replacement1 = @'
_venv_py = STUDIOFORGE_DIR / "backend" / ".venv311_x64" / "Scripts" / ("python.exe" if os.name == "nt" else "python")
def _probe_python(path):
    try:
        p = subprocess.run([str(path), "-c", "print(1)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        return p.returncode == 0
    except Exception:
        return False
PYTHON = str(_venv_py) if (_venv_py.exists() and _probe_python(_venv_py)) else (sys.executable or "python")
'@
  $new = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern1, $replacement1, 1)
  if ($new -ne $content) {
    $content = $new
    $changes += 'venv_probe'
  }
}

# 2) Merge PYTHONPATH in _run_in_console_env instead of overwrite
if ($content -notmatch 'env\["PYTHONPATH"\] = \(str\(newv\) \+ os\.pathsep \+ prev\) if prev else str\(newv\)') {
  $pattern2 = '(?ms)^\s{8}if\s+isinstance\(extra_env,\s*dict\):\s*\r?\n\s{12}env\.update\(\{str\(k\): str\(v\) for k, v in extra_env\.items\(\)\}\)'
  $replacement2 = @'
        if isinstance(extra_env, dict):
            xe = {str(k): str(v) for k, v in extra_env.items()}
            if "PYTHONPATH" in xe:
                prev = env.get("PYTHONPATH", "")
                newv = xe.pop("PYTHONPATH")
                env["PYTHONPATH"] = (str(newv) + os.pathsep + prev) if prev else str(newv)
            env.update(xe)
'@
  $new2 = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern2, $replacement2, 1)
  if ($new2 -ne $content) {
    $content = $new2
    $changes += 'merge_pythonpath'
  }
}

if ($content -ne $original) {
  Set-Content -LiteralPath $File -Encoding UTF8 -NoNewline -Value $content
  Write-Output ("Patched: " + ($changes -join ', '))
} else {
  Write-Output 'No changes made (already patched or patterns not found)'
}
