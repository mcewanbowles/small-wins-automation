$ErrorActionPreference = 'Stop'
$root = 'D:\Seagate\small-wins-automation\Studioforge'
$bat = Join-Path $root 'Launch_Tool_Launcher.bat'
if (-not (Test-Path $bat)) { throw "Missing launcher: $bat" }
n# Create Desktop shortcut
$shell = New-Object -ComObject WScript.Shell
$lnkName = 'Small Wins Tool Launcher.lnk'
$desktop = [Environment]::GetFolderPath('Desktop')
$desktopLnk = Join-Path $desktop $lnkName
$sc1 = $shell.CreateShortcut($desktopLnk)
$sc1.TargetPath = $bat
$sc1.WorkingDirectory = $root
$sc1.WindowStyle = 7
$sc1.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$sc1.Save()

# Create Startup shortcut
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$startupLnk = Join-Path $startup $lnkName
$sc2 = $shell.CreateShortcut($startupLnk)
$sc2.TargetPath = $bat
$sc2.WorkingDirectory = $root
$sc2.WindowStyle = 7
$sc2.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$sc2.Save()

Write-Host 'Created:'
Write-Host " - $desktopLnk"
Write-Host " - $startupLnk"
Write-Host " - $bat"
