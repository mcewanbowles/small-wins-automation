param(
  [string]$slug = 'stellaluna',
  [string[]]$words = @()
)

$ErrorActionPreference = 'Stop'

if ($words -and $words.Length -gt 0) {
  & python "D:\Seagate\small-wins-automation\Studioforge\tools\diagnose_icons.py" --slug $slug --words @words
} else {
  & python "D:\Seagate\small-wins-automation\Studioforge\tools\diagnose_icons.py" --slug $slug
}
