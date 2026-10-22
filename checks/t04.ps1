$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$pyv = & python -c "import sys; print('%d.%d.%d' % sys.version_info[:3])" 2>$null
if (-not $pyv) { 'CANNOT CHECK (python not found, or only the Microsoft Store stub: install Python from python.org)' } else {
"python $pyv"
[IO.File]::WriteAllText("$d\hex.py", 'import sys; print(sys.stdin.buffer.read().strip().hex())')
$s = [string][char]0x65E5 + [char]0x672C
$h = $s | python "$d\hex.py"
"bytes=$h  (UTF-8 would be e697a5e69cac)"
if ($h -match '^(3f)+$') { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
