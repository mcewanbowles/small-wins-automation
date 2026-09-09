$ErrorActionPreference = 'Stop'
$paths = @(
  'D:\Seagate\small-wins-automation\assets\themes\stellaluna\icons_colored\bird.png',
  'D:\Seagate\small-wins-automation\assets\themes\stellaluna\icons_colored\owl.png'
)
Get-Item -LiteralPath $paths | Select-Object Name, Length, LastWriteTime, DirectoryName | Format-Table -AutoSize
