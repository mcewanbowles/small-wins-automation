$ErrorActionPreference = 'Stop'
$root = 'D:\Seagate\small-wins-automation\Studioforge'
$bat = Join-Path $root 'Launch_Tool_Launcher.bat'
if (-not (Test-Path $bat)) { throw "Missing launcher: $bat" }

$destDir = 'D:\Seagate\small-wins-automation'
$lnkName = 'Small Wins Tool Launcher.lnk'
$dest = Join-Path $destDir $lnkName

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($dest)
$sc.TargetPath = $bat
$sc.WorkingDirectory = $root
$sc.WindowStyle = 7
$sc.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$sc.Save()

Write-Host "Created: $dest"
