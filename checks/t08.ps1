$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$want = [string][char]0x65E5 + [char]0x672C
[IO.File]::WriteAllText("$d\nobom.ps1", "Write-Output '$want'", (New-Object System.Text.UTF8Encoding $false))
$o = powershell -NoProfile -ExecutionPolicy Bypass -File "$d\nobom.ps1"
"got $o (want $want)"
if ($o -ne $want) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
