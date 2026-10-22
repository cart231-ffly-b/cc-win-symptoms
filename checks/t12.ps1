$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$t = "use `night-shift and `true."
$t
if ($t -match "`n" -or $t -match "`t") { 'REPRODUCED' } else { 'NOT REPRODUCED' }
