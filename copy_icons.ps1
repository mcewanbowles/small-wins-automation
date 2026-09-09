$ErrorActionPreference = 'Stop'
$srcBird = 'D:\Seagate\small-wins-automation\assets\symbols\png\Alpha\b\bird.png'
$srcOwl  = 'D:\Seagate\small-wins-automation\assets\symbols\png\Alpha\o\owl.png'
$dst     = 'D:\Seagate\small-wins-automation\assets\themes\stellaluna\icons_colored'
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -LiteralPath $srcBird -Destination (Join-Path $dst 'bird.png') -Force
Copy-Item -LiteralPath $srcOwl  -Destination (Join-Path $dst 'owl.png')  -Force
Get-Item -LiteralPath (Join-Path $dst 'bird.png'), (Join-Path $dst 'owl.png') |
  Select-Object Name, Length, LastWriteTime, DirectoryName | Format-Table -AutoSize
