param(
  [string]$Base = 'STEL'
)
$ErrorActionPreference = 'Stop'
$outRoot = "D:\Seagate\small-wins-automation\production\generators\Studioforge\OUTPUT"
$candidates = Get-ChildItem -LiteralPath $outRoot -Directory -Filter "$Base-SORT*" | Sort-Object LastWriteTime -Descending
if (-not $candidates -or $candidates.Count -eq 0) {
  Write-Output "No output directories found under $outRoot for pattern '$Base-SORT*'"
  return
}
$latest = $candidates[0]
$qa = Join-Path $latest.FullName 'QA_OUT'
if (Test-Path $qa) {
  Get-ChildItem -LiteralPath $qa -File |
    Select-Object Name, Length, LastWriteTime |
    Sort-Object LastWriteTime -Descending |
    Format-Table -AutoSize
} else {
  Write-Output "QA_OUT not found in $($latest.FullName)"
}
