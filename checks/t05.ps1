$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$pyv = & python -c "import sys; print('%d.%d.%d' % sys.version_info[:3])" 2>$null
if (-not $pyv) { 'CANNOT CHECK (python not found, or only the Microsoft Store stub: install Python from python.org)' } else {
"python $pyv"
[IO.File]::WriteAllText("$d\say.py", 'import sys; sys.stdout.buffer.write((chr(0x65e5)+chr(0x672c)).encode("utf-8"))')
$s = python "$d\say.py"
$want = [string][char]0x65E5 + [char]0x672C
"read with code page $([Console]::OutputEncoding.CodePage): " + (($s.ToCharArray() | ForEach-Object { '{0:X4}' -f [int]$_ }) -join ' ') + '  (want 65E5 672C)'
if ($s -ne $want) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
