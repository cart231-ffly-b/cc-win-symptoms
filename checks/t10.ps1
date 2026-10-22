$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
powershell -NoProfile -Command "foreach ($i in 1..2) { $i }"; $e = $LASTEXITCODE
"exit=$e"
if ($e -ne 0) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
