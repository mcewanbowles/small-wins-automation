$ErrorActionPreference = 'SilentlyContinue'

$removed = @()
$targets = @()

$paths = @(
  [Environment]::GetFolderPath('Startup'),
  (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'),
  (Join-Path $env:OneDrive 'Start Menu\Programs\Startup'),
  'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp'
) | Where-Object { $_ -and (Test-Path $_) }

$patterns = @(
  '*Small Wins*Tool*Launcher*.lnk',
  '*WINDSURF*Tool*Launcher*.lnk',
  '*Studioforge*Tool*Launcher*.lnk'
)

foreach ($dir in $paths) {
  foreach ($pat in $patterns) {
    $targets += Get-ChildItem -Path $dir -Filter $pat -File -ErrorAction SilentlyContinue
  }
}

# Also catch shortcuts whose TargetPath points to our Launch_Tool_Launcher.bat
$shell = $null
try { $shell = New-Object -ComObject WScript.Shell } catch {}
if ($shell) {
  foreach ($dir in $paths) {
    foreach ($lnk in Get-ChildItem -Path $dir -Filter '*.lnk' -File -ErrorAction SilentlyContinue) {
      try {
        $sc = $shell.CreateShortcut($lnk.FullName)
        if ($sc.TargetPath -match 'small-wins-automation\\Studioforge\\Launch_Tool_Launcher\.bat') {
          $targets += $lnk
        }
      } catch {}
    }
  }
}

$targets = $targets | Sort-Object FullName -Unique

if ($targets.Count -eq 0) {
  Write-Host 'No matching startup shortcuts found.'
  exit 0
}

foreach ($t in $targets) {
  try {
    Remove-Item -LiteralPath $t.FullName -Force
    $removed += $t.FullName
  } catch {
    Write-Warning ("Failed to remove {0}: {1}" -f $t.FullName, $_)
  }
}

Write-Host 'Removed:'
$removed | ForEach-Object { Write-Host (' - ' + $_) }
