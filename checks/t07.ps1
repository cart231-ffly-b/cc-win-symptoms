$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
$pyv = & python -c "import sys; print('%d.%d.%d' % sys.version_info[:3])" 2>$null
if (-not $pyv) { 'CANNOT CHECK (python not found, or only the Microsoft Store stub: install Python from python.org)' } else {
"python $pyv"
[IO.File]::WriteAllText("$d\dash.py", 'print("a" + chr(0x2014) + chr(0x2713) + "b")')
$old = $env:PYTHONIOENCODING; $env:PYTHONIOENCODING = 'utf-8'
python -I "$d\dash.py" > "$d\o1.txt" 2> "$d\e1.txt"; $a = $LASTEXITCODE
python "$d\dash.py" > "$d\o2.txt" 2> "$d\e2.txt"; $b = $LASTEXITCODE
$env:PYTHONIOENCODING = $old
$err = [IO.File]::ReadAllText("$d\e1.txt")
"with -I exit=$a, without -I exit=$b"
if ($a -ne 0 -and $err -match 'UnicodeEncodeError' -and $b -eq 0) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
}
