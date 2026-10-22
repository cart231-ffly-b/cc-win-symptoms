$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\hex.py", 'import sys; print(sys.stdin.buffer.read().strip().hex())')
$s = [string][char]0x65E5 + [char]0x672C
$h = $s | python "$d\hex.py"
"bytes=$h  (UTF-8 would be e697a5e69cac)"
if ($h -match '^(3f)+$') { 'REPRODUCED' } else { 'NOT REPRODUCED' }
