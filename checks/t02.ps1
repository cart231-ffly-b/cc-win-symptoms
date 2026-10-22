$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\arr.ps1", 'param([string[]]$Path) "count=$($Path.Count) first=$($Path[0])"')
$o = powershell -NoProfile -ExecutionPolicy Bypass -File "$d\arr.ps1" -Path a b; $e = $LASTEXITCODE
"$o  exit=$e"
if ($o -eq 'count=1 first=a' -and $e -eq 0) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
