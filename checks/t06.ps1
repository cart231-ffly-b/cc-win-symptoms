$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$pyv = & python -c "import sys; print('%d.%d.%d' % sys.version_info[:3])" 2>$null
if (-not $pyv) { 'CANNOT CHECK (python not found, or only the Microsoft Store stub: install Python from python.org)' } else {
"python $pyv"
[IO.File]::WriteAllText("$d\dash.py", 'print("a" + chr(0x2014) + chr(0x2713) + "b")')
python "$d\dash.py" > "$d\out.txt" 2> "$d\err.txt"; $e = $LASTEXITCODE
$err = [IO.File]::ReadAllText("$d\err.txt")
"exit=$e, UnicodeEncodeError=$($err -match 'UnicodeEncodeError')"
if ($e -ne 0 -and $err -match 'UnicodeEncodeError') { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
