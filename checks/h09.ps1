$d = Join-Path $env:TEMP ('cc-trap-' + (Get-Date -Format 'yyyyMMddHHmmss')); New-Item -ItemType Directory $d -Force | Out-Null
[IO.File]::WriteAllText("$d\p1.txt", 'Run exactly this Bash command and nothing else, then stop: echo ''a$$(b'' > x.txt')
[IO.File]::WriteAllText("$d\p2.txt", 'Run exactly this Bash command and nothing else, then stop: echo ''a$(b'' > y.txt')
Push-Location $d
Get-Content "$d\p2.txt" -Raw | claude -p --allowedTools Bash | Out-Null
Get-Content "$d\p1.txt" -Raw | claude -p --allowedTools Bash | Out-Null
Pop-Location
$y = Test-Path "$d\y.txt"; $x = Test-Path "$d\x.txt"
"echo with one dollar and a paren -> written=$y; echo with two dollars and a paren -> written=$x"
if (-not $y) { 'CANNOT CHECK (even the one-dollar command did not run: check that the Bash tool is available and allowed)' } elseif (-not $x) { 'REPRODUCED' } else { 'NOT REPRODUCED' }
