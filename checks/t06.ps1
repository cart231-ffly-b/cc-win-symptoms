$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\dash.py", 'print("a" + chr(0x2014) + chr(0x2713) + "b")')
python "$d\dash.py" > "$d\out.txt" 2> "$d\err.txt"; $e = $LASTEXITCODE
"exit=$e"
if ($e -ne 0) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
