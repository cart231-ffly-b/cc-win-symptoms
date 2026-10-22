$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\exit2.ps1", 'exit 2')
powershell -NoProfile -ExecutionPolicy Bypass -File "$d\exit2.ps1"; $a = $LASTEXITCODE
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '$d\exit2.ps1'"; $b = $LASTEXITCODE
"-File=$a  -Command=$b"
if ($a -eq 2 -and $b -eq 1) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
