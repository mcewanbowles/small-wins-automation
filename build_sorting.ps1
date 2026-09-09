param(
  [string]$Slug = 'stellaluna',
  [string]$Title = 'Stellaluna',
  [string]$Base  = 'STEL'
)
$ErrorActionPreference = 'Stop'
Push-Location 'D:\Seagate\small-wins-automation'
try {
  python "D:\Seagate\small-wins-automation\Studioforge\Accurate generators\GENERATE_ALL.py" $Slug $Title $Base --only sorting
}
finally {
  Pop-Location
}
